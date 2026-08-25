#!/usr/bin/env python3
"""永続化に関係する業務シナリオとCRUD検討状況を記録・検査する。"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
OPERATIONS = ("create", "update", "delete")
OPERATION_LABEL = {"create": "作成", "update": "更新", "delete": "削除"}
COVERAGE = ("covered", "not-applicable")
STATUSES = ("confirmed", "assumed", "unknown")
STATUS_LABEL = {"confirmed": "確認済み", "assumed": "仮置き", "unknown": "未確認"}
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TECHNICAL = re.compile(
    r"(?:\bAPI\b|\bDTO\b|\bHTTP\b|\bSQL\b|\bORM\b|\bqueue\b|"
    r"テーブル|カラム|エンドポイント|リポジトリ層)", re.IGNORECASE | re.ASCII,
)


def fail(message, code=2):
    print(json.dumps({"error": message}, ensure_ascii=False))
    raise SystemExit(code)


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
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        fail("--config が読めない: {}".format(exc))


def safe_topic(topic):
    if not TOPIC_RE.match(topic or "") or ".." in (topic or ""):
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(topic))
    return topic


def output_paths(config, topic):
    directory = config.get("scenario_dir") or ""
    if not directory:
        fail("設定に scenario_dir が無い")
    base = os.path.join(directory, safe_topic(topic))
    return base + ".persistence.jsonl", base + ".md"


def read_rows(path):
    if not os.path.exists(path):
        return []
    rows = []
    try:
        with open(path, encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    fail("台帳の{}行目がJSONではない: {}".format(number, exc))
                if row.get("kind") not in ("scenario", "coverage"):
                    fail("台帳の{}行目に未知のkindがある".format(number))
                rows.append(row)
    except OSError as exc:
        fail("台帳を読めない: {}".format(exc))
    return rows


def write_rows(path, rows):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        fail("台帳へ書けない: {}".format(exc))


def require_text(name, value):
    value = (value or "").strip()
    if not value:
        fail("{} が空".format(name))
    return value


def cmd_coverage(args, config):
    ledger, _ = output_paths(config, args.topic)
    rows = read_rows(ledger)
    existing = [r for r in rows if r.get("kind") == "coverage" and r.get("operation") == args.operation]
    if existing and not args.replace:
        fail("{}の検討状況は記録済み。変更するなら --replace".format(
            OPERATION_LABEL[args.operation]), 3)
    row = {
        "kind": "coverage",
        "id": "CV-{}".format(args.operation),
        "topic": safe_topic(args.topic),
        "operation": args.operation,
        "status": args.status,
        "reason": require_text("--reason", args.reason),
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
    }
    rows = [r for r in rows if not (
        r.get("kind") == "coverage" and r.get("operation") == args.operation
    )] + [row]
    write_rows(ledger, rows)
    print(json.dumps({"coverage": "recorded", "operation": args.operation, "path": ledger}, ensure_ascii=False))


def cmd_add(args, config):
    ledger, _ = output_paths(config, args.topic)
    rows = read_rows(ledger)
    fields = {
        "title": args.title, "actor": args.actor, "prior_state": args.prior_state,
        "event": args.event, "condition": args.condition, "decision": args.decision,
        "result": args.result, "next_state": args.next_state, "fact": args.fact,
        "history": args.history, "retention": args.retention, "source": args.source,
    }
    fields = {key: require_text("--" + key.replace("_", "-"), value) for key, value in fields.items()}
    for key in ("title", "actor", "prior_state", "event", "condition", "decision", "result", "next_state"):
        match = TECHNICAL.search(fields[key])
        if match:
            fail("{} に実現用語「{}」がある。業務の言葉へ戻す".format(key, match.group(0)))
    duplicate = [r for r in rows if r.get("kind") == "scenario" and
                 r.get("operation") == args.operation and r.get("title") == fields["title"]]
    if duplicate and not args.replace:
        fail("同じ操作と題名のシナリオがある。変更するなら --replace", 3)
    number = max([int(str(r.get("id", "PS-000")).split("-")[-1])
                  for r in rows if r.get("kind") == "scenario"] or [0]) + 1
    row = {
        "kind": "scenario", "id": "PS-{:03d}".format(number),
        "topic": safe_topic(args.topic), "operation": args.operation,
        **fields, "status": args.status,
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
    }
    if duplicate:
        old_id = duplicate[0]["id"]
        row["id"] = old_id
        rows = [r for r in rows if r.get("id") != old_id]
    rows.append(row)
    write_rows(ledger, rows)
    print(json.dumps({"scenario": "recorded", "id": row["id"], "path": ledger}, ensure_ascii=False))


def validate(rows):
    problems = []
    coverage_rows = [r for r in rows if r.get("kind") == "coverage"]
    scenarios = [r for r in rows if r.get("kind") == "scenario"]
    for operation in OPERATIONS:
        coverage = [r for r in coverage_rows if r.get("operation") == operation]
        if len(coverage) != 1:
            problems.append("{}の検討状況が{}件（1件必要）".format(OPERATION_LABEL[operation], len(coverage)))
            continue
        status = coverage[0].get("status")
        matching = [r for r in scenarios if r.get("operation") == operation]
        if status == "covered" and not matching:
            problems.append("{}はcoveredだがシナリオが無い".format(OPERATION_LABEL[operation]))
        if status == "not-applicable" and matching:
            problems.append("{}はnot-applicableだがシナリオがある".format(OPERATION_LABEL[operation]))
    unknown = [r.get("id") for r in scenarios if r.get("status") == "unknown"]
    if unknown:
        problems.append("未確認のシナリオがある: {}".format(" / ".join(unknown)))
    if not scenarios:
        problems.append("永続化シナリオが1件も無い")
    return problems, scenarios, coverage_rows


def cmd_check(args, config):
    ledger, _ = output_paths(config, args.topic)
    problems, scenarios, _ = validate(read_rows(ledger))
    if problems:
        for problem in problems:
            print(json.dumps({"problem": problem}, ensure_ascii=False))
        fail("永続化シナリオをデータモデリングへ渡せない", 1)
    counts = {operation: sum(1 for row in scenarios if row.get("operation") == operation)
              for operation in OPERATIONS}
    print(json.dumps({"check": "ready", "scenarios": len(scenarios), "operations": counts}, ensure_ascii=False))


def markdown(topic, rows):
    problems, scenarios, coverage = validate(rows)
    if problems:
        fail("資料化の前にcheckを通す: {}".format(" / ".join(problems)), 1)
    lines = ["# 永続化シナリオ — {}".format(topic), "", "## 作成・更新・削除の検討", ""]
    for operation in OPERATIONS:
        item = next(r for r in coverage if r.get("operation") == operation)
        lines.append("- {}: `{}` — {}".format(OPERATION_LABEL[operation], item["status"], item["reason"]))
    lines.extend(["", "## シナリオ", ""])
    for row in scenarios:
        lines.extend([
            "### {} {}".format(row["id"], row["title"]), "",
            "- 操作上の観点: {}".format(OPERATION_LABEL[row["operation"]]),
            "- アクター: {}".format(row["actor"]),
            "- 事前状態: {}".format(row["prior_state"]),
            "- 業務イベント: {}".format(row["event"]),
            "- 条件: {}".format(row["condition"]),
            "- 業務判断: {}".format(row["decision"]),
            "- 業務上の結果: {}".format(row["result"]),
            "- 次状態: {}".format(row["next_state"]),
            "- 永続化する事実: {}".format(row["fact"]),
            "- 残す履歴: {}".format(row["history"]),
            "- 物理削除を許す条件: {}".format(row["retention"]),
            "- 出所: {}".format(row["source"]),
            "- 確からしさ: {}".format(STATUS_LABEL[row["status"]]), "",
        ])
    return "\n".join(lines)


def cmd_render(args, config):
    ledger, document = output_paths(config, args.topic)
    if os.path.exists(document) and not args.force:
        fail("資料が既にある。置き換えるなら --force: {}".format(document), 3)
    content = markdown(args.topic, read_rows(ledger))
    try:
        os.makedirs(os.path.dirname(document), exist_ok=True)
        with open(document, "w", encoding="utf-8") as stream:
            stream.write(content)
    except OSError as exc:
        fail("資料を書けない: {}".format(exc))
    print(json.dumps({"document": "written", "path": document}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    coverage = sub.add_parser("coverage")
    coverage.add_argument("--config", required=True)
    coverage.add_argument("--topic", required=True)
    coverage.add_argument("--operation", choices=OPERATIONS, required=True)
    coverage.add_argument("--status", choices=COVERAGE, required=True)
    coverage.add_argument("--reason", required=True)
    coverage.add_argument("--replace", action="store_true")
    add = sub.add_parser("add")
    add.add_argument("--config", required=True)
    add.add_argument("--topic", required=True)
    for name in ("title", "actor", "prior-state", "event", "condition", "decision",
                 "result", "next-state", "fact", "history", "retention", "source"):
        add.add_argument("--" + name, required=True)
    add.add_argument("--operation", choices=OPERATIONS, required=True)
    add.add_argument("--status", choices=STATUSES, default="assumed")
    add.add_argument("--replace", action="store_true")
    check = sub.add_parser("check")
    check.add_argument("--config", required=True)
    check.add_argument("--topic", required=True)
    render = sub.add_parser("render")
    render.add_argument("--config", required=True)
    render.add_argument("--topic", required=True)
    render.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    {"coverage": cmd_coverage, "add": cmd_add, "check": cmd_check, "render": cmd_render}[args.command](args, config)


if __name__ == "__main__":
    main()
