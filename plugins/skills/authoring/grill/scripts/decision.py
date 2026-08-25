#!/usr/bin/env python3
"""決めたことを1件ずつ積み、後から読み返す。

**このプラグインで唯一、状態を持つ場所である。**

素材から作り直せるものは持たない、というのがこの一式の方針だが、
決定は会話の産物で、素材が残っていても再現できない。
「なぜそう決めたか」は、決めた場に居た人しか書けない。だから記録する。

  decision.py add --config <json|path> --topic <題材> --what <決めたこと> --why <理由>
                  [--aspect <観点>] [--status decided|open|dropped]
      -> 1件を追記する

  decision.py list --config <json|path> [--topic <題材>] [--status <状態>]
      -> JSONL で読み返す

  decision.py render --config <json|path> --topic <題材> [--format markdown]
      -> 決定ログを人が読む形にする
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
STATUS = ("decided", "open", "dropped")
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


def log_path(cfg, topic):
    d = cfg.get("log_dir") or ""
    if not d:
        fail("設定に log_dir が無い")
    return os.path.join(d, "{}.jsonl".format(topic))


def safe_topic(t):
    """題材はファイル名になる。区切りも相対参照も入れない。"""
    if not TOPIC_RE.match(t or "") or ".." in (t or ""):
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(t))
    return t


def cmd_add(args, cfg):
    topic = safe_topic(args.topic)
    if args.status not in STATUS:
        fail("--status が不正: {}（{}）".format(args.status, " / ".join(STATUS)))
    if not (args.what or "").strip():
        fail("--what が空（何を決めたか）")
    # 理由の無い決定は、後から読んだ人が覆せない（覆していいのかも分からない）。
    # 未決・取り下げは「なぜ決められないか」が理由になる。
    if not (args.why or "").strip():
        fail("--why が空。理由の無い決定は、後から読んだ人が覆せない")

    p = log_path(cfg, topic)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    except OSError as e:
        fail("決定ログの置き場を作れない: {}".format(e))

    entry = {
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
        "topic": topic,
        "aspect": args.aspect or "",
        "status": args.status,
        "what": args.what.strip(),
        "why": args.why.strip(),
    }
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        fail("決定ログへ書けない: {}".format(e))
    print(json.dumps({"decision": "recorded", "path": p, "status": entry["status"]},
                     ensure_ascii=False))


def read_log(cfg, topic):
    p = log_path(cfg, topic)
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
        fail("決定ログを読めない: {}".format(e))
    return out


def cmd_list(args, cfg):
    topics = [safe_topic(args.topic)] if args.topic else []
    if not topics:
        d = cfg.get("log_dir") or ""
        if os.path.isdir(d):
            topics = [f[:-6] for f in sorted(os.listdir(d)) if f.endswith(".jsonl")]
    found = 0
    for t in topics:
        for e in read_log(cfg, t):
            if args.status and e.get("status") != args.status:
                continue
            print(json.dumps(e, ensure_ascii=False))
            found += 1
    if found == 0:
        # 黙って空にしない。まだ何も決めていないのか、置き場が違うのか。
        print(json.dumps({"warning": "決定が1件も無い", "log_dir": cfg.get("log_dir"),
                          "topics": topics}, ensure_ascii=False), file=sys.stderr)


def cmd_render(args, cfg):
    topic = safe_topic(args.topic)
    entries = read_log(cfg, topic)
    if not entries:
        fail("決定が1件も無い: {}".format(log_path(cfg, topic)), 3)

    def block(title, st):
        rows = [e for e in entries if e.get("status") == st]
        lines = ["## {}".format(title), ""]
        if not rows:
            lines += ["なし", ""]
            return lines
        lines += ["| 決めたこと | なぜ | 観点 | いつ |", "|---|---|---|---|"]
        for e in rows:
            cell = lambda s: str(s).replace("|", "\\|")
            lines.append("| {} | {} | {} | {} |".format(
                cell(e.get("what", "")), cell(e.get("why", "")),
                cell(e.get("aspect", "")), e.get("ts", "")[:10]))
        lines.append("")
        return lines

    out = ["# 決定ログ — {}".format(topic), ""]
    out += ["対象 {} 件（決定 {} ／ 未決 {} ／ 取り下げ {}）".format(
        len(entries),
        sum(1 for e in entries if e.get("status") == "decided"),
        sum(1 for e in entries if e.get("status") == "open"),
        sum(1 for e in entries if e.get("status") == "dropped")), ""]
    out += block("決めたこと", "decided")
    out += block("未決のまま", "open")
    out += block("取り下げたもの", "dropped")
    print("\n".join(out))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--what", required=True)
    sp.add_argument("--why", required=True)
    sp.add_argument("--aspect", default="")
    sp.add_argument("--status", choices=STATUS, default="decided")

    sp = sub.add_parser("list")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", default="")
    sp.add_argument("--status", choices=("",) + STATUS, default="")

    sp = sub.add_parser("render")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--format", choices=("markdown",), default="markdown")

    args = p.parse_args()
    cfg = load_config(args.config)
    {"add": cmd_add, "list": cmd_list, "render": cmd_render}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
