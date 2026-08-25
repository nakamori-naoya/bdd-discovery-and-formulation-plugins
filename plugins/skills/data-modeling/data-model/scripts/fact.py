#!/usr/bin/env python3
"""記録すべき事実のシナリオを積み、モデルと突き合わせる。

**データモデルの出発点は保存方式ではなく「何を記録しないと業務が回らないか」である。**
記録の必要を説明できない要素は、手法が何であれモデルに要らない。

  fact.py add --config <json|path> --topic <題材> --element <モデル要素>
              --fact <記録する事実> --why-record <記録しないと何が困るか>
              --actor <その事実を必要とする人> --source <どの例・事実から来たか>
              [--status confirmed|assumed|unknown] [--replace]
      -> 1件を追記する

  fact.py list --config <json|path> --topic <題材> [--status <確からしさ>]
  fact.py render --config <json|path> --topic <題材>
      -> 台帳を表にする

  fact.py check --config <json|path> --topic <題材> --model-file <path>
      -> モデルと台帳を双方向で突き合わせ、片側にしかない要素があれば落とす
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
# **正本はこの1箇所だけ。** 表示名もここから導く。値と表示名を別々に持つと、
# 片方だけ足したとき「?」を混ぜたまま exit 0 で通してしまう。
STATUS_LABEL = {"confirmed": "確認済み", "assumed": "仮置き", "unknown": "未確認"}
STATUS = tuple(STATUS_LABEL)
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TABLE_RE = re.compile(r"^###\s+テーブル:\s*(.+?)\s*$")
CONTENT_TABLE_RE = re.compile(r"^###\s+(.+?)\s*$")
BDD_SCENARIO_RE = re.compile(r"^###\s+Scenario\s+([A-Za-z]+-[0-9]+):\s+(.+?)\s*$")
LOGICAL_HEADINGS = (
    "## 目的と範囲", "## リソース系とイベント系", "## シナリオと記録の対応",
    "## 論理データモデル図", "## 論理テーブル定義", "## ライフサイクルと時間軸",
    "## 並行実行で必要な保証", "## 論理設計の完了条件", "## 未決", "## BDD",
)
# 物理実装まで降りたモデルは、手法によらずこのプラグインの成果物ではない。
# 語ではなく「実装そのもの」だけを拾う（テーブルという語は論理モデルでも使う）。
PHYSICAL = (
    ("CREATE TABLE", "物理DDL"),
    ("ALTER TABLE", "物理DDL"),
    ("PRIMARY KEY (", "物理制約"),
    ("VARCHAR(", "物理型"),
    ("```sql", "SQL"),
    ("CREATE INDEX", "物理索引"),
    ("READ COMMITTED", "分離レベル"),
    ("REPEATABLE READ", "分離レベル"),
    ("SERIALIZABLE", "分離レベル"),
)


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


def safe_topic(t):
    if not TOPIC_RE.match(t or "") or ".." in (t or ""):
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(t))
    return t


def ledger_path(cfg, topic):
    d = cfg.get("model_dir") or ""
    if not d:
        fail("設定に model_dir が無い")
    return os.path.join(d, "{}.facts.jsonl".format(topic))


def read_ledger(cfg, topic):
    p = ledger_path(cfg, topic)
    if not os.path.exists(p):
        return []
    rows = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError as e:
        fail("台帳を読めない: {}".format(e))
    return rows


def read_scenario_ids(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as e:
                    fail("{}の{}行目がJSONではない: {}".format(path, number, e))
                if row.get("kind") == "scenario" and row.get("id"):
                    rows.append(row["id"])
    except OSError as e:
        fail("永続化シナリオ台帳を読めない: {}".format(e))
    if not rows:
        fail("永続化シナリオが1件も無い: {}".format(path))
    return rows


def bdd_scenarios(lines, problems):
    found = {}
    positions = []
    for index, line in enumerate(lines):
        match = BDD_SCENARIO_RE.match(line)
        if match:
            positions.append((index, match.group(1), match.group(2)))
    if not positions:
        problems.append({"kind": "BDDシナリオが無い",
                         "howto": "### Scenario <ID>: <場合> と Given / When / Then を置く"})
        return found
    for offset, (start, scenario_id, title) in enumerate(positions):
        end = positions[offset + 1][0] if offset + 1 < len(positions) else len(lines)
        # 次のH3がテーブルなら、その直前までがシナリオである。
        for index in range(start + 1, end):
            if lines[index].startswith("### "):
                end = index
                break
        body = lines[start + 1:end]
        if scenario_id in found:
            problems.append({"kind": "BDDシナリオIDの重複", "scenario": scenario_id})
        found[scenario_id] = title
        for keyword in ("Given ", "When ", "Then "):
            if not any(line.startswith(keyword) and line != keyword for line in body):
                problems.append({"kind": "BDDシナリオの節が不足", "scenario": scenario_id,
                                 "missing": keyword.strip()})
    return found


def logical_tables(lines, problems):
    """rdb-logical-data-modeling資料の論理テーブル名を定義節だけから読む。"""
    try:
        start = lines.index("## 論理テーブル定義") + 1
    except ValueError:
        return []
    end = next((index for index in range(start, len(lines))
                if lines[index].startswith("## ")), len(lines))
    tables = []
    in_detail_table = False
    for line in lines[start:end]:
        heading = CONTENT_TABLE_RE.match(line)
        if heading:
            raw_name = heading.group(1).strip()
            in_detail_table = raw_name == "詳細イベント"
            if not in_detail_table:
                code_names = re.findall(r"`([^`]+)`", raw_name)
                name = code_names[0] if code_names else raw_name
                if name in tables:
                    problems.append({"kind": "論理テーブルが重複", "element": name})
                else:
                    tables.append(name)
            continue
        if not in_detail_table or not line.startswith("|") or line.startswith("|---"):
            continue
        first_cell = line.strip().strip("|").split("|", 1)[0].strip()
        code_names = re.findall(r"`([^`]+)`", first_cell)
        if code_names:
            name = code_names[0]
            if name in tables:
                problems.append({"kind": "論理テーブルが重複", "element": name})
            else:
                tables.append(name)
    return tables


def cmd_add(args, cfg):
    topic = safe_topic(args.topic)
    for key, value, why in (
        ("--element", args.element, "どのモデル要素の話かが決まらない"),
        ("--fact", args.fact, "何を記録するのかが無い"),
        ("--why-record", args.why_record,
         "記録の必要を説明できない要素は、手法が何であれモデルに要らない"),
        ("--actor", args.actor, "誰がその記録を必要とするのか分からない"),
        ("--source", args.source, "どの例・事実から来たか辿れない記録は、後から覆せない"),
    ):
        if not (value or "").strip():
            fail("{} が空。{}".format(key, why))

    existing = read_ledger(cfg, topic)
    key = (args.element.strip(), args.fact.strip())
    dup = [r for r in existing if (r.get("element"), r.get("fact")) == key]
    if dup and not args.replace:
        fail("同じ要素へ同じ事実がすでにある: {} / {}。書き換えるなら --replace".format(*key), 3)

    p = ledger_path(cfg, topic)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    except OSError as e:
        fail("台帳の置き場を作れない: {}".format(e))

    entry = {
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
        "id": "FS-{:03d}".format(len(existing) + 1),
        "topic": topic,
        "element": key[0],
        "fact": key[1],
        "why_record": args.why_record.strip(),
        "actor": args.actor.strip(),
        "source": args.source.strip(),
        "status": args.status,
    }
    rows = ([r for r in existing if (r.get("element"), r.get("fact")) != key] + [entry]
            if args.replace else None)
    try:
        if rows is None:
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        else:
            with open(p, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        fail("台帳へ書けない: {}".format(e))
    print(json.dumps({"fact_scenario": "recorded", "id": entry["id"], "path": p},
                     ensure_ascii=False))


def cmd_list(args, cfg):
    rows = read_ledger(cfg, safe_topic(args.topic))
    found = 0
    for r in rows:
        if args.status and r.get("status") != args.status:
            continue
        print(json.dumps(r, ensure_ascii=False))
        found += 1
    if found == 0:
        print(json.dumps({"warning": "記録シナリオが1件も無い",
                          "model_dir": cfg.get("model_dir")}, ensure_ascii=False),
              file=sys.stderr)


def cmd_render(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_ledger(cfg, topic)
    if not rows:
        fail("記録シナリオが1件も無い: {}".format(ledger_path(cfg, topic)), 3)

    def cell(s):
        return str(s or "").replace("|", "\\|")

    label = STATUS_LABEL
    unknown_status = sorted({r.get("status") for r in rows} - set(STATUS_LABEL) - {None})
    if unknown_status:
        fail("台帳に未知の確からしさがある: {}（使えるのは {}）".format(
            " / ".join(unknown_status), " / ".join(STATUS)))
    out = ["# 記録すべき事実 — {}".format(topic), "",
           "{} 件".format(len(rows)), "",
           "| ID | モデル要素 | 記録する事実 | 記録しないと困ること | 必要とする人 | 出所 | 確からしさ |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r.get("id", ""), cell(r.get("element")), cell(r.get("fact")),
            cell(r.get("why_record")), cell(r.get("actor")), cell(r.get("source")),
            label.get(r.get("status"), "?")))
    out.append("")
    print("\n".join(out))


def cmd_check(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_ledger(cfg, topic)
    if not rows:
        fail("記録シナリオが1件も無い。モデルより先に、何を記録するかを洗い出す", 3)
    try:
        with open(args.model_file, encoding="utf-8") as f:
            model = f.read()
    except OSError as e:
        fail("モデルを読めない: {}".format(e))

    problems = []
    lines = model.splitlines()
    for heading in LOGICAL_HEADINGS:
        if lines.count(heading) != 1:
            problems.append({"kind": "論理設計の見出しが不正", "heading": heading,
                             "count": lines.count(heading)})
    for token, kind in PHYSICAL:
        if token in model:
            problems.append({"kind": kind, "token": token,
                             "howto": "物理の実装はこの成果物の外。論理の意味まで戻す"})

    input_scenarios = read_scenario_ids(args.scenario_file)
    written_scenarios = bdd_scenarios(lines, problems)
    for scenario_id in input_scenarios:
        if scenario_id not in written_scenarios:
            problems.append({"kind": "論理設計に無い永続化シナリオ", "scenario": scenario_id,
                             "howto": "入力シナリオをBDDシナリオとして論理設計へ写す"})

    declared = logical_tables(lines, problems)
    if not declared:
        fail("論理モデルの『## 論理テーブル定義』にテーブルが1つも無い")
    recorded = {r.get("element") for r in rows}
    # 記録の必要を説明されていない要素は、手法が何であれ残さない。
    for e in declared:
        if e not in recorded:
            problems.append({"kind": "記録の必要が無い要素", "element": e,
                             "howto": "その要素を記録すべき事実シナリオを足すか、モデルから外す"})
    # 記録すると決めたのにモデルに置き場が無いものは、落ちている。
    for e in sorted(recorded - set(declared)):
        problems.append({"kind": "モデルに無い記録", "element": e,
                         "howto": "論理テーブル定義へ {} を足すか、記録シナリオを取り下げる".format(e)})

    if problems:
        for p in problems:
            print(json.dumps(p, ensure_ascii=False))
        print(json.dumps({"error": "モデルと記録シナリオが {} 箇所ずれている".format(len(problems))},
                         ensure_ascii=False))
        sys.exit(1)
    print(json.dumps({"check": "aligned", "logical_tables": len(declared),
                      "bdd_scenarios": len(written_scenarios),
                      "fact_scenarios": len(rows)}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--element", required=True)
    sp.add_argument("--fact", required=True)
    sp.add_argument("--why-record", required=True)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--source", required=True)
    sp.add_argument("--status", choices=STATUS, default="assumed")
    sp.add_argument("--replace", action="store_true")

    sp = sub.add_parser("list")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--status", choices=("",) + STATUS, default="")

    sp = sub.add_parser("render")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)

    sp = sub.add_parser("check")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--model-file", required=True)
    sp.add_argument("--scenario-file", required=True)

    args = p.parse_args()
    cfg = load_config(args.config)
    {"add": cmd_add, "list": cmd_list, "render": cmd_render, "check": cmd_check}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
