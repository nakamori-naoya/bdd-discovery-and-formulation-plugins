#!/usr/bin/env python3
"""RDB機能根拠を記録し、物理設計が論理テーブル構造を変えていないか照合する。"""

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FEATURE = re.compile(r"^###\s+機能:\s*(.+?)\s*$")
TABLE = re.compile(r"^###\s+テーブル:\s*(.+?)\s*$")
COLUMN = re.compile(r"^####\s+列:\s*(.+?)\s*$")
BUSINESS_CONSTRAINT = re.compile(r"^####\s+業務制約:\s*(.+?)\s*$")
CONTENT_TABLE = re.compile(r"^###\s+(.+?)\s*$")
ISOLATION_CASE = re.compile(r"^###\s+分離性判断:\s*(.+?)\s*$")
INDEX_CASE = re.compile(r"^###\s+index:\s*(.+?)\s*$")
READ_CASE = re.compile(r"^###\s+Read-[0-9]+:\s*(.+?)\s*$")
BDD = re.compile(r"^(?:###\s+Scenario\b|Given\s|When\s|Then\s|And\s)", re.MULTILINE)
FORBIDDEN = re.compile(
    r"(?:\bAPI\b|\bDTO\b|\bHTTP\b|\bORM\b|エンドポイント|画面コンポーネント)",
    re.IGNORECASE | re.ASCII,
)
REQUIRED_HEADINGS = (
    "## 対象と論理設計", "## 物理制約", "## 物理化の方針", "## index",
    "## トランザクションと分離レベル", "## パーティションと配置",
    "## 容量・性能・運用", "## 採用するRDB機能", "## 物理設計の完了条件",
    "## 未決", "## 代表的な読み取り",
)
ISOLATION_FIELDS = (
    "- 同時に進む操作:", "- 許してはいけない結果:", "- 発生し得る現象:",
    "- 選択する分離レベル:", "- 併用する仕組み:",
    "- 対象バージョンでの確認:", "- 競合時の扱い:",
)
INDEX_FIELDS = (
    "- 対象:", "- 種類:", "- 目的:", "- 列の順番:",
    "- 対象Read・更新:", "- 根拠:", "- 更新費用:",
)
READ_FIELDS = (
    "- 利用者と目的:", "- 入力・検索条件:", "- 結合:",
    "- 並び順と上限:", "- 返す情報:", "- 鮮度と一貫性:",
    "- 想定件数:", "- SLO:", "- 支えるindex:",
    "**対象バージョンでの確認**:",
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


def target(config):
    database = config.get("database") or {}
    product = str(database.get("product") or "").strip()
    version = str(database.get("version") or "").strip()
    if not product or not version:
        fail("設定に database.product / database.version が無い")
    return product, version


def capability_path(config, topic):
    directory = str(config.get("design_dir") or "").strip()
    if not directory:
        fail("設定に design_dir が無い")
    return os.path.join(directory, safe_topic(topic) + ".capabilities.jsonl")


def read_jsonl(path, expected_kind=None):
    if not os.path.isfile(path):
        fail("入力ファイルが無い: {}".format(path))
    rows = []
    try:
        with open(path, encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    fail("{}の{}行目がJSONではない: {}".format(path, number, exc))
                if expected_kind and row.get("kind") != expected_kind:
                    continue
                rows.append(row)
    except OSError as exc:
        fail("{}を読めない: {}".format(path, exc))
    return rows


def cmd_capability(args, config):
    product, version = target(config)
    feature = (args.feature or "").strip()
    support_from = (args.support_from or "").strip()
    evidence = (args.evidence or "").strip()
    note = (args.note or "").strip()
    if not all((feature, support_from, evidence, note)):
        fail("feature、support-from、evidence、noteは空にできない")
    if not (evidence.startswith("https://") or evidence.startswith("local:")):
        fail("evidenceは対象版の公式https URLまたは local: で始まる実機確認にする")
    path = capability_path(config, args.topic)
    rows = read_jsonl(path) if os.path.exists(path) else []
    duplicate = [row for row in rows if row.get("feature") == feature]
    if duplicate and not args.replace:
        fail("同じ機能の根拠がある。変更するなら --replace: {}".format(feature), 3)
    row = {
        "kind": "capability", "topic": safe_topic(args.topic), "feature": feature,
        "product": product, "version": version, "support_from": support_from,
        "evidence": evidence, "note": note,
        "ts": datetime.now(JST).isoformat(timespec="seconds"),
    }
    rows = [item for item in rows if item.get("feature") != feature] + [row]
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as stream:
            for item in rows:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    except OSError as exc:
        fail("機能根拠台帳へ書けない: {}".format(exc))
    print(json.dumps({"capability": "recorded", "feature": feature, "path": path}, ensure_ascii=False))


def read_text(path, label):
    try:
        with open(path, encoding="utf-8") as stream:
            return stream.read()
    except OSError as exc:
        fail("{}を読めない: {}".format(label, exc))


def schema_signature(text, label, problems):
    signature = {}
    current = None
    source_lines = text.splitlines()
    if any(TABLE.match(line) for line in source_lines):
        for line in source_lines:
            table = TABLE.match(line)
            if table:
                current = table.group(1)
                if current in signature:
                    problems.append("{}でテーブル「{}」が重複".format(label, current))
                signature.setdefault(current, {"columns": [], "constraints": [], "definitions": []})
                continue
            column = COLUMN.match(line)
            constraint = BUSINESS_CONSTRAINT.match(line)
            if not column and not constraint:
                continue
            if current is None:
                problems.append("{}でテーブル外に列または業務制約がある: {}".format(label, line))
                continue
            kind = "columns" if column else "constraints"
            name = (column or constraint).group(1)
            if name in signature[current][kind]:
                problems.append("{}のテーブル「{}」で「{}」が重複".format(label, current, name))
            signature[current][kind].append(name)
    if not signature:
        lines = source_lines
        try:
            start = lines.index("## 論理テーブル定義") + 1
        except ValueError:
            start = -1
        if start >= 0:
            end = next((index for index in range(start, len(lines))
                        if lines[index].startswith("## ")), len(lines))
            current = None
            detail_table = False
            for line in lines[start:end]:
                heading = CONTENT_TABLE.match(line)
                if heading:
                    raw_name = heading.group(1).strip()
                    detail_table = raw_name == "詳細イベント"
                    if detail_table:
                        current = None
                    else:
                        code_names = re.findall(r"`([^`]+)`", raw_name)
                        current = code_names[0] if code_names else raw_name
                        if current in signature:
                            problems.append("{}でテーブル「{}」が重複".format(label, current))
                        signature.setdefault(current, {"columns": [], "constraints": [], "definitions": []})
                    continue
                constraint = BUSINESS_CONSTRAINT.match(line)
                if constraint and current:
                    signature[current]["constraints"].append(constraint.group(1))
                    continue
                if not line.startswith("|") or line.startswith("|---"):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if detail_table and len(cells) >= 2:
                    table_names = re.findall(r"`([^`]+)`", cells[0])
                    column_names = re.findall(r"`([^`]+)`", cells[1])
                    if table_names:
                        current_detail = table_names[0]
                        signature.setdefault(current_detail, {"columns": [], "constraints": [], "definitions": []})
                        signature[current_detail]["definitions"].append("|".join(cells))
                        for column_name in column_names:
                            if column_name not in signature[current_detail]["columns"]:
                                signature[current_detail]["columns"].append(column_name)
                    continue
                if current and cells:
                    column_names = re.findall(r"`([^`]+)`", cells[0])
                    if column_names:
                        if column_names[0] not in signature[current]["columns"]:
                            signature[current]["columns"].append(column_names[0])
                        signature[current]["definitions"].append("|".join(cells))
    if not signature:
        problems.append("{}に論理テーブル定義が1件も無い".format(label))
    return signature


def schema_digest(signature):
    canonical = {
        table: {
            "columns": sorted(values["columns"]),
            "constraints": sorted(values["constraints"]),
            "definitions": sorted(values.get("definitions", [])),
        }
        for table, values in sorted(signature.items())
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def named_sections(lines, pattern):
    sections = []
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        end = index + 1
        while end < len(lines) and not lines[end].startswith("### ") and not lines[end].startswith("## "):
            end += 1
        sections.append((match.group(1), lines[index + 1:end]))
    return sections


def require_section_fields(kind, sections, fields, problems):
    for name, lines in sections:
        for field in fields:
            values = [line for line in lines if line.startswith(field)]
            if len(values) != 1:
                problems.append("{}「{}」の「{}」が{}件（1件必要）".format(kind, name, field, len(values)))
            elif values[0].strip() == field:
                problems.append("{}「{}」の「{}」が空".format(kind, name, field))


def cmd_fingerprint(args, config):
    del config
    model = read_text(args.model_file, "論理モデル")
    problems = []
    signature = schema_signature(model, "論理モデル", problems)
    if problems:
        for problem in problems:
            print(json.dumps({"problem": problem}, ensure_ascii=False))
        fail("論理構造の指紋を作れない", 1)
    print(json.dumps({
        "algorithm": "sha256",
        "digest": schema_digest(signature),
        "tables": len(signature),
        "columns": sum(len(table["columns"]) for table in signature.values()),
        "business_constraints": sum(len(table["constraints"]) for table in signature.values()),
    }, ensure_ascii=False))


def cmd_check(args, config):
    product, version = target(config)
    design = read_text(args.design_file, "RDB設計")
    model = read_text(args.model_file, "論理モデル")
    capabilities = read_jsonl(capability_path(config, args.topic), "capability")
    problems = []
    design_lines = design.splitlines()
    for heading in REQUIRED_HEADINGS:
        if design_lines.count(heading) != 1:
            problems.append("見出し「{}」が{}件（1件必要）".format(heading, design_lines.count(heading)))
    for expected in (
        "- 対象DBMS: {}".format(product),
        "- 対象バージョン: {}".format(version),
    ):
        if expected not in design_lines:
            problems.append("対象と根拠に「{}」が無い".format(expected))
    logical_basename = os.path.basename(args.model_file)
    if not any(line.startswith("- 論理モデル:") and logical_basename in line for line in design_lines):
        problems.append("対象と論理設計に入力ファイル「{}」が無い".format(logical_basename))
    forbidden = FORBIDDEN.search(design)
    if forbidden:
        problems.append("永続化設計に別の関心「{}」が混ざっている".format(forbidden.group(0)))
    if BDD.search(design):
        problems.append("物理設計にBDDシナリオが混ざっている。業務シナリオは論理設計だけに置く")
    logical_schema = schema_signature(model, "論理モデル", problems)
    logical_digest = schema_digest(logical_schema)
    fingerprint_line = "- 論理構造の指紋: sha256:{}".format(logical_digest)
    if design_lines.count(fingerprint_line) != 1:
        problems.append("対象と論理設計に現在の論理構造の指紋「{}」が1件必要".format(fingerprint_line))
    if any(TABLE.match(line) or COLUMN.match(line) or BUSINESS_CONSTRAINT.match(line)
           for line in design_lines):
        problems.append("物理設計に論理テーブル・列・業務制約の定義を複製しない")
    for table in logical_schema.values():
        for constraint in table["constraints"]:
            if constraint not in design:
                problems.append("論理設計の業務制約「{}」を物理制約で扱っていない".format(constraint))
    indexes = named_sections(design_lines, INDEX_CASE)
    reads = named_sections(design_lines, READ_CASE)
    if not indexes:
        problems.append("### index: <名前> が1件も無い")
    if not reads:
        problems.append("### Read-<連番>: <業務上の読み取り> が1件も無い")
    require_section_fields("index", indexes, INDEX_FIELDS, problems)
    require_section_fields("Read", reads, READ_FIELDS, problems)
    isolation_cases = named_sections(design_lines, ISOLATION_CASE)
    if not isolation_cases:
        problems.append("### 分離性判断: <判断名> が1件も無い")
    require_section_fields("分離性判断", isolation_cases, ISOLATION_FIELDS, problems)
    features = [match.group(1) for match in (FEATURE.match(line) for line in design_lines) if match]
    if not features:
        problems.append("### 機能: <機能名> が1件も無い")
    evidence = {row.get("feature"): row for row in capabilities
                if row.get("product") == product and str(row.get("version")) == version}
    for feature in features:
        if feature not in evidence:
            problems.append("採用機能「{}」に{} {}の根拠が無い".format(feature, product, version))
    if problems:
        for problem in problems:
            print(json.dumps({"problem": problem}, ensure_ascii=False))
        fail("RDB永続化設計を完了にできない", 1)
    print(json.dumps({
        "check": "aligned", "database": {"product": product, "version": version},
        "logical_tables": len(logical_schema),
        "logical_columns": sum(len(table["columns"]) for table in logical_schema.values()),
        "business_constraints": sum(len(table["constraints"]) for table in logical_schema.values()),
        "logical_schema_sha256": logical_digest,
        "indexes": len(indexes),
        "read_scenarios": len(reads),
        "isolation_cases": len(isolation_cases),
        "verified_features": len(features),
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    capability = sub.add_parser("capability")
    capability.add_argument("--config", required=True)
    capability.add_argument("--topic", required=True)
    capability.add_argument("--feature", required=True)
    capability.add_argument("--support-from", required=True)
    capability.add_argument("--evidence", required=True)
    capability.add_argument("--note", required=True)
    capability.add_argument("--replace", action="store_true")
    check = sub.add_parser("check")
    check.add_argument("--config", required=True)
    check.add_argument("--topic", required=True)
    check.add_argument("--design-file", required=True)
    check.add_argument("--model-file", required=True)
    fingerprint = sub.add_parser("fingerprint")
    fingerprint.add_argument("--config", required=True)
    fingerprint.add_argument("--model-file", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    {"capability": cmd_capability, "check": cmd_check, "fingerprint": cmd_fingerprint}[args.command](args, config)


if __name__ == "__main__":
    main()
