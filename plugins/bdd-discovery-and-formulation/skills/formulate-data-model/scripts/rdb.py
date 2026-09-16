#!/usr/bin/env python3
"""物理設計が論理テーブル構造を変えていないか、採用機能に対象版の根拠があるかを照合する。

  rdb.py fingerprint --model-file <論理設計Markdownの絶対path>
      -> 論理テーブル・列・業務制約から sha256 の指紋をstdoutへJSONで返す。exit 0 / 1 = 指紋を作れない / 2 = 読めない
  rdb.py check --model-file <更新済み論理設計Markdownの絶対path> --product <製品> --version <版>   < <物理設計本文Markdown>
      -> 見出し、対象、指紋、論理定義の非複製、業務制約の扱い、index・Read・分離性判断の欄、採用機能の根拠欄を検査する。
         exit 0 = 整合 / 1 = 問題あり（stdoutへ problem を1行ずつ） / 2 = 読めない
  rdb.py self-test

正本: --model-file が指す保存済みの論理設計資料。指紋はそこから毎回計算する。
入力: agentが同じ文脈で作った物理設計本文（Markdown）を標準入力で受ける。fileは介さない。
  採用機能の根拠は本文の "### 機能: <名前>" 節の "- 利用可能な版:" と "- 根拠:" 欄に書かれ、資料自体が根拠の記録になる。
  "- 根拠:" は対象版の公式 https URL または local: で始まる実機確認。機能名は重複しない。
検査するのは述語だけであり、index の選択や分離レベルの妥当性、根拠のURLがその版の公式資料かは判定しない。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

FEATURE = re.compile(r"^###\s+機能:\s*(.+?)\s*$")
TABLE = re.compile(r"^###\s+テーブル:\s*(.+?)\s*$")
COLUMN = re.compile(r"^####\s+列:\s*(.+?)\s*$")
BUSINESS_CONSTRAINT = re.compile(r"^####\s+業務制約:\s*(.+?)\s*$")
CONTENT_TABLE = re.compile(r"^###\s+(.+?)\s*$")
ISOLATION_CASE = re.compile(r"^###\s+分離性判断:\s*(.+?)\s*$")
INDEX_CASE = re.compile(r"^###\s+index:\s*(.+?)\s*$")
READ_CASE = re.compile(r"^###\s+Read-[0-9]+:\s*(.+?)\s*$")
BDD = re.compile(r"^(?:###\s+Scenario\b|Given\s|When\s|Then\s|And\s)", re.MULTILINE)
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
)
FEATURE_FIELDS = ("- 利用可能な版:", "- 根拠:")
EVIDENCE_FIELD = "- 根拠:"


def fail(message, code=2):
    print(json.dumps({"error": message}, ensure_ascii=False))
    raise SystemExit(code)




def target(args):
    product = str(args.product or "").strip()
    version = str(args.version or "").strip()
    if not product or not version:
        fail("--product / --version は空にできない")
    return product, version


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


def cmd_fingerprint(args):
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


def read_stdin_design():
    """標準入力を物理設計本文として読む。空なら exit 2。"""
    design = sys.stdin.read()
    if not design.strip():
        fail("標準入力が空。物理設計本文（Markdown）を標準入力で渡す")
    return design


def check_feature_evidence(features, problems):
    """各 ### 機能: 節が利用可能な版と根拠の欄を持ち、根拠が https URL または local: であることを検査する。"""
    seen = set()
    for name, lines in features:
        if name in seen:
            problems.append("機能「{}」が重複".format(name))
        seen.add(name)
        require_section_fields("機能", [(name, lines)], FEATURE_FIELDS, problems)
        values = [line[len(EVIDENCE_FIELD):].strip() for line in lines if line.startswith(EVIDENCE_FIELD)]
        for value in values:
            if value and not (value.startswith("https://") or value.startswith("local:")):
                problems.append("機能「{}」の根拠は対象版の公式https URLまたは local: で始まる実機確認にする: {}".format(name, value))


def cmd_check(args):
    product, version = target(args)
    design = read_stdin_design()
    model = read_text(args.model_file, "論理モデル")
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
    features = named_sections(design_lines, FEATURE)
    if not features:
        problems.append("### 機能: <機能名> が1件も無い")
    check_feature_evidence(features, problems)
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
        "features_with_evidence": len(features),
    }, ensure_ascii=False))


def self_test():
    logical_text = "\n".join((
        "# RDB論理設計 — 予約", "## 論理テーブル定義", "### テーブル: reservation",
        "#### 列: id", "#### 列: slot", "#### 業務制約: 同じ利用枠に有効な予約は一つ", "",
    ))
    with tempfile.TemporaryDirectory() as tmp:
        logical = os.path.join(tmp, "logical.md")
        with open(logical, "w", encoding="utf-8") as stream:
            stream.write(logical_text)
        fingerprint = subprocess.run([sys.executable, __file__, "fingerprint", "--model-file", logical], text=True, capture_output=True)
        assert fingerprint.returncode == 0, "正例: fingerprint"
        digest = json.loads(fingerprint.stdout)["digest"]
        design = "\n".join((
            "# RDB物理設計 — 予約", "## 対象と論理設計", "- 対象DBMS: PostgreSQL", "- 対象バージョン: 16",
            "- 論理モデル: logical.md", "- 論理構造の指紋: sha256:" + digest,
            "## 物理制約", "同じ利用枠に有効な予約は一つ を排他制約で守る", "## 物理化の方針", "x",
            "## index", "### index: reservation_slot_excl", "- 対象: reservation(slot)", "- 種類: GiST 排他",
            "- 目的: 競合制御", "- 列の順番: 単一列", "- 対象Read・更新: 予約の作成", "- 根拠: 対象版仕様", "- 更新費用: 小",
            "## トランザクションと分離レベル", "### 分離性判断: 同時予約", "- 同時に進む操作: 予約Aと予約B",
            "- 許してはいけない結果: 同じ枠に二つの予約", "- 発生し得る現象: 書き込みスキュー",
            "- 選択する分離レベル: READ COMMITTED", "- 併用する仕組み: 排他制約", "- 対象バージョンでの確認: 実機",
            "- 競合時の扱い: 中断して利用者へ返す", "## パーティションと配置", "なし", "## 容量・性能・運用", "x",
            "## 採用するRDB機能", "### 機能: 排他制約", "- 採用箇所: reservation(slot)の排他制約",
            "- 利用可能な版: 9.0", "- 根拠: https://www.postgresql.org/docs/16/", "- 対象バージョンで確認したこと: 実機",
            "## 物理設計の完了条件", "x", "## 未決", "なし", "## 代表的な読み取り", "### Read-001: 空き枠を探す",
            "- 利用者と目的: 予約者", "- 入力・検索条件: 日付", "- 結合: なし", "- 並び順と上限: 開始時刻, 100",
            "- 返す情報: slot", "- 鮮度と一貫性: primary", "- 想定件数: 1000", "- SLO: p95 100ms",
            "- 支えるindex: reservation_slot_excl", "",
        ))

        def run(payload, model=logical, *extra):
            return subprocess.run([sys.executable, __file__, "check", "--model-file", model, "--product", "PostgreSQL", "--version", "16", *extra],
                                  input=payload, text=True, capture_output=True)

        assert run(design).returncode == 0, "正例: 指紋・欄・根拠欄が揃う"
        assert run("").returncode == 2, "境界例: 空stdinはexit 2"
        assert run(design.replace("- 根拠: https://www.postgresql.org/docs/16/\n", "")).returncode == 1, "反例: 根拠欄が無い"
        assert run(design.replace("- 利用可能な版: 9.0\n", "")).returncode == 1, "反例: 利用可能な版の欄が無い"
        assert run(design.replace("https://www.postgresql.org/docs/16/", "読んだ気がする")).returncode == 1, "反例: 根拠の形が不正"
        assert run(design.replace("https://www.postgresql.org/docs/16/", "local: 16.4で排他制約を実行して確認")).returncode == 0, "境界例: local: の実機確認を受理"
        duplicated = design.replace("## 物理設計の完了条件", "### 機能: 排他制約\n- 利用可能な版: 9.0\n- 根拠: https://www.postgresql.org/docs/16/\n## 物理設計の完了条件")
        assert run(duplicated).returncode == 1, "反例: 同じ機能が重複"
        assert run(design, os.path.join(tmp, "missing.md")).returncode == 2, "境界例: 正本pathの欠落はexit 2"
        old_form = subprocess.run([sys.executable, __file__, "check", "--design-file", "x", "--model-file", logical, "--product", "P", "--version", "1"], text=True, capture_output=True)
        assert old_form.returncode == 2, "境界例: 旧引数 --design-file はargparseが拒否する"
        old_sub = subprocess.run([sys.executable, __file__, "capability", "--ledger", "x"], text=True, capture_output=True)
        assert old_sub.returncode == 2, "境界例: 旧subcommand capability は無い"
        with open(logical, "a", encoding="utf-8") as stream:
            stream.write("#### 列: created_at\n")
        assert run(design).returncode == 1, "反例: 論理構造の変化（指紋不一致）"
    print(json.dumps({"self_test": "passed", "cases": 12}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--model-file", required=True)
    check.add_argument("--product", required=True)
    check.add_argument("--version", required=True)
    fingerprint = sub.add_parser("fingerprint")
    fingerprint.add_argument("--model-file", required=True)
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "self-test":
        self_test()
        return
    {"check": cmd_check, "fingerprint": cmd_fingerprint}[args.command](args)


if __name__ == "__main__":
    main()
