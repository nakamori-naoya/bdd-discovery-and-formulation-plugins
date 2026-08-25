#!/usr/bin/env python3
"""業務で起きる事実を1件ずつ台帳へ積み、時系列で読み返す。

**洗い出しは会話の産物である。** 誰が何を確かめ、何を仮に置いたかは、
その場に居た者しか書けない。だから確からしさまで含めて記録する。

  event.py add --config <json|path> --topic <題材> --name <起きたこと>
               --actor <担い手> --trigger <引き金> --outcome <業務上どう変わったか>
               [--precondition <前提>] [--status confirmed|assumed|unknown]
               [--source <誰・どこからの知識か>] [--replace]
      -> 1件を追記する

  event.py list --config <json|path> --topic <題材> [--status <確からしさ>]
      -> JSONL で読み返す

  event.py render --config <json|path> --topic <題材>
      -> 台帳を時系列の表にする
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
# 確からしさ。**未確認を確認済みと同じ顔で並べない。**
# **正本はこの1箇所だけ。** 表示名も集計もここから導く。
# 値と表示名を別々に書くと、片方だけ足したとき「1件（0／0／0）」のような
# 矛盾した出力を exit 0 で返してしまう。
STATUS_LABEL = {"confirmed": "確認済み", "assumed": "仮置き", "unknown": "未確認"}
STATUS = tuple(STATUS_LABEL)
# 引き金。ここに無いものは、まだ業務イベントとして見えていない。
TRIGGER = ("操作", "時間", "外部", "連鎖")
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def fail(msg, code=2):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def load_config(raw):
    raw = (raw or "").strip()
    if raw.startswith("{"):
        return json.loads(raw)
    try:
        result = subprocess.run(
            ["yq", "-o=json", "-I=0", ".", raw], capture_output=True,
            text=True, timeout=10, check=True,
        )
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        fail("--config が読めない: {}".format(e))


def ledger_path(cfg, topic):
    d = cfg.get("event_dir") or ""
    if not d:
        fail("設定に event_dir が無い")
    return os.path.join(d, "{}.jsonl".format(topic))


def safe_topic(t):
    """題材はファイル名になる。区切りも相対参照も入れない。"""
    if not TOPIC_RE.match(t or "") or ".." in (t or ""):
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(t))
    return t


def read_ledger(cfg, topic):
    p = ledger_path(cfg, topic)
    if not os.path.exists(p):
        return []
    out = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue  # 壊れた1行で全部を捨てない
    except OSError as e:
        fail("台帳を読めない: {}".format(e))
    return out


def cmd_add(args, cfg):
    topic = safe_topic(args.topic)
    if args.trigger not in TRIGGER:
        fail("--trigger が不正: {}（{}）".format(args.trigger, " / ".join(TRIGGER)))
    for key, value, why in (
        ("--name", args.name, "何が起きたかが無い"),
        ("--actor", args.actor, "誰の行いか分からない事実は、業務の担い手を確定できない"),
        ("--outcome", args.outcome, "業務上何が変わったかが無いと、そもそも事実ではない"),
    ):
        if not (value or "").strip():
            fail("{} が空。{}".format(key, why))

    existing = read_ledger(cfg, topic)
    name = args.name.strip()
    hit = [e for e in existing if e.get("name") == name]
    if hit and not args.replace:
        fail("同じ名前の事実がすでにある: {!r}。書き換えるなら --replace".format(name), 3)

    p = ledger_path(cfg, topic)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    except OSError as e:
        fail("台帳の置き場を作れない: {}".format(e))

    entry = {
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
        "topic": topic,
        "name": name,
        "actor": args.actor.strip(),
        "trigger": args.trigger,
        "precondition": (args.precondition or "").strip(),
        "outcome": args.outcome.strip(),
        "status": args.status,
        "source": (args.source or "").strip(),
    }
    rows = ([e for e in existing if e.get("name") != name] + [entry]) if args.replace else None
    try:
        if rows is None:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        else:
            with open(p, "w", encoding="utf-8") as f:
                for e in rows:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
    except OSError as e:
        fail("台帳へ書けない: {}".format(e))
    print(json.dumps({"event": "recorded", "path": p, "status": entry["status"]},
                     ensure_ascii=False))


def cmd_list(args, cfg):
    rows = read_ledger(cfg, safe_topic(args.topic))
    found = 0
    for e in rows:
        if args.status and e.get("status") != args.status:
            continue
        print(json.dumps(e, ensure_ascii=False))
        found += 1
    if found == 0:
        print(json.dumps({"warning": "事実が1件も無い", "event_dir": cfg.get("event_dir")},
                         ensure_ascii=False), file=sys.stderr)


def cmd_render(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_ledger(cfg, topic)
    if not rows:
        fail("事実が1件も無い: {}".format(ledger_path(cfg, topic)), 3)

    def cell(s):
        return str(s or "").replace("|", "\\|")

    label = STATUS_LABEL
    counts = ["{} {}".format(name, sum(1 for e in rows if e.get("status") == key))
              for key, name in STATUS_LABEL.items()]
    # 正本に無い値が混じったら、件数と内訳が合わなくなる前に気づけるようにする。
    unknown_status = sorted({e.get("status") for e in rows} - set(STATUS_LABEL) - {None})
    if unknown_status:
        fail("台帳に未知の確からしさがある: {}（使えるのは {}）".format(
            " / ".join(unknown_status), " / ".join(STATUS)))
    out = ["# 業務イベント台帳 — {}".format(topic), ""]
    out += ["{} 件（{}）".format(len(rows), " ／ ".join(counts)), ""]
    out += ["| 起きたこと | 担い手 | 引き金 | 前提 | 業務上の結果 | 確からしさ | 出所 |",
            "|---|---|---|---|---|---|---|"]
    for e in rows:
        out.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            cell(e.get("name")), cell(e.get("actor")), cell(e.get("trigger")),
            cell(e.get("precondition")) or "—", cell(e.get("outcome")),
            label.get(e.get("status"), "?"), cell(e.get("source")) or "—"))
    out.append("")
    print("\n".join(out))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--trigger", required=True)
    sp.add_argument("--outcome", required=True)
    sp.add_argument("--precondition", default="")
    sp.add_argument("--status", choices=STATUS, default="assumed")
    sp.add_argument("--source", default="")
    sp.add_argument("--replace", action="store_true")

    sp = sub.add_parser("list")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--status", choices=("",) + STATUS, default="")

    sp = sub.add_parser("render")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)

    args = p.parse_args()
    cfg = load_config(args.config)
    {"add": cmd_add, "list": cmd_list, "render": cmd_render}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
