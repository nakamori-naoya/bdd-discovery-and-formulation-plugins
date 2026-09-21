#!/usr/bin/env python3
"""Validate the structural contract of immutable-aware logical models."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass


REQUIRED_HEADERS = ["系列", "性質", "論理テーブル", "正式な定義", "時刻", "変化", "根拠"]
ALLOWED_SERIES = {"リソース系", "イベント系"}
ALLOWED_NATURES = {"業務", "技術", "派生"}
ALLOWED_SOURCES = {"現在状態", "有効期間履歴", "イベント列", "派生"}
TABLE_HEADING = re.compile(r"^###\s+`([^`|]+)`")
COLUMN_CELL = re.compile(r"^`([^`|]+)`(?:（[^）]+）)?$")
TABLE_CELL = re.compile(r"^`([^`|]+)`$")


@dataclass
class Problem:
    path: str
    detail: str
    howto: str

    def emit(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def section(lines: list[str], heading: str) -> tuple[int, int] | None:
    try:
        start = lines.index(heading)
    except ValueError:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return start, end


def parse_classification(lines: list[str], problems: list[Problem]) -> dict[str, dict[str, str]]:
    bounds = section(lines, "## リソース系とイベント系")
    if bounds is None:
        problems.append(Problem("classification", "『リソース系とイベント系』節が無い", "必須の分類表を置く"))
        return {}
    start, end = bounds
    header_index = next((i for i in range(start + 1, end) if lines[i].lstrip().startswith("|")), None)
    if header_index is None or header_index + 1 >= end:
        problems.append(Problem("classification", "分類表を読めない", "指定された7列のMarkdown表を置く"))
        return {}
    headers = split_cells(lines[header_index])
    if headers != REQUIRED_HEADERS:
        problems.append(Problem("classification.headers", f"列が契約と一致しない: {headers}", f"{REQUIRED_HEADERS}の順で置く"))
        return {}
    rows: dict[str, dict[str, str]] = {}
    for line_number in range(header_index + 2, end):
        line = lines[line_number]
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = split_cells(line)
        if len(cells) != len(headers):
            problems.append(Problem(f"classification.line[{line_number + 1}]", "列数が分類表headerと一致しない", "各行を7列にする"))
            continue
        row = dict(zip(headers, cells))
        match = TABLE_CELL.fullmatch(row["論理テーブル"])
        if not match:
            problems.append(Problem(f"classification.line[{line_number + 1}].論理テーブル", "単一のテーブル名をbacktickで囲んでいない", "1行に1テーブルを書く"))
            continue
        name = match.group(1)
        if name in rows:
            problems.append(Problem(f"classification.{name}", "分類が重複している", "各テーブルを一度だけ分類する"))
            continue
        rows[name] = row
    return rows


def parse_definitions(lines: list[str], problems: list[Problem]) -> dict[str, list[tuple[str, str, int]]]:
    bounds = section(lines, "## 論理テーブル定義")
    if bounds is None:
        problems.append(Problem("definitions", "『論理テーブル定義』節が無い", "全論理テーブルの定義を置く"))
        return {}
    start, end = bounds
    headings: list[tuple[str, int]] = []
    for index in range(start + 1, end):
        match = TABLE_HEADING.match(lines[index])
        if match:
            headings.append((match.group(1), index))
    definitions: dict[str, list[tuple[str, str, int]]] = {}
    for position, (name, heading_index) in enumerate(headings):
        next_index = headings[position + 1][1] if position + 1 < len(headings) else end
        columns: list[tuple[str, str, int]] = []
        for index in range(heading_index + 1, next_index):
            if not lines[index].lstrip().startswith("|"):
                continue
            cells = split_cells(lines[index])
            if not cells:
                continue
            match = COLUMN_CELL.fullmatch(cells[0])
            if match:
                columns.append((match.group(1), " | ".join(cells), index + 1))
        definitions[name] = columns
    if not definitions:
        problems.append(Problem("definitions", "テーブル見出しを読めない", "### `table_name`（業務上の名前）の形で定義する"))
    return definitions


def check_document(markdown: str, label: str) -> list[Problem]:
    lines = markdown.splitlines()
    problems: list[Problem] = []
    classification = parse_classification(lines, problems)
    definitions = parse_definitions(lines, problems)

    classified = set(classification)
    defined = set(definitions)
    for name in sorted(defined - classified):
        problems.append(Problem(f"{label}.classification.{name}", "論理テーブルが分類表に無い", "系列・性質・正式な定義・時刻・変化・根拠を記載する"))
    for name in sorted(classified - defined):
        problems.append(Problem(f"{label}.classification.{name}", "分類したテーブルの論理定義が無い", "論理テーブル定義を追加するか分類から外す"))

    for name in sorted(classified & defined):
        row = classification[name]
        prefix = f"{label}.{name}"
        if row["系列"] not in ALLOWED_SERIES:
            problems.append(Problem(f"{prefix}.系列", f"許可値ではない: {row['系列']}", "リソース系またはイベント系にする"))
        if row["性質"] not in ALLOWED_NATURES:
            problems.append(Problem(f"{prefix}.性質", f"許可値ではない: {row['性質']}", "業務・技術・派生のいずれかにする"))
        if row["正式な定義"] not in ALLOWED_SOURCES:
            problems.append(Problem(f"{prefix}.正式な定義", f"許可値ではない: {row['正式な定義']}", "分類表の「正式な定義」列を現在状態・有効期間履歴・イベント列・派生のいずれかにする"))
        if not row["根拠"] or row["根拠"] in {"-", "なし"}:
            problems.append(Problem(f"{prefix}.根拠", "業務知識または技術要件への根拠が無い", "対応する業務知識または技術要件の参照を記載する"))

        columns = {column for column, _, _ in definitions[name]}
        if row["系列"] == "リソース系":
            if "created_at" not in columns:
                problems.append(Problem(f"{prefix}.created_at", "リソース系にcreated_atが無い", "リソース成立時刻をcreated_atで持つ"))
            if "created_at" not in row["時刻"]:
                problems.append(Problem(f"{prefix}.時刻", "分類表の時刻がcreated_atを示さない", "created_atの意味を記載する"))
            if row["正式な定義"] == "イベント列":
                problems.append(Problem(f"{prefix}.正式な定義", "リソース系の論理テーブルに対し、分類表の「正式な定義」列でイベント列を選択している", "「正式な定義」列を現在状態・有効期間履歴・派生のいずれかにする"))

        if row["系列"] == "イベント系":
            if "occurred_at" not in row["時刻"]:
                problems.append(Problem(f"{prefix}.時刻", "イベント系の業務上または技術上の成立時刻がoccurred_atではない", "occurred_atを記載する"))
            if row["変化"] != "追加のみ":
                problems.append(Problem(f"{prefix}.変化", f"追加専用ではない: {row['変化']}", "イベント表は追加のみにする"))
            if row["正式な定義"] != "イベント列":
                problems.append(Problem(f"{prefix}.正式な定義", "イベント系の論理テーブルで「正式な定義」列がイベント列ではない", "「正式な定義」列をイベント列にする"))
            if row["性質"] == "派生":
                problems.append(Problem(f"{prefix}.性質", "派生物をイベント系に分類している", "業務イベントか技術イベントかを明示する"))

    return problems


def decode_input(raw: str) -> list[tuple[str, str]]:
    stripped = raw.lstrip()
    if not stripped.startswith("{"):
        return [("document", raw)]
    payload = json.loads(raw)
    if not isinstance(payload, dict) or set(payload) != {"documents"} or not isinstance(payload["documents"], list) or not payload["documents"]:
        raise ValueError("JSON入力はdocumentsの非空listだけを持つobjectにする")
    result: list[tuple[str, str]] = []
    for index, item in enumerate(payload["documents"]):
        if not isinstance(item, dict) or set(item) != {"path", "content"} or not isinstance(item["path"], str) or not isinstance(item["content"], str):
            raise ValueError(f"documents[{index}]はpathとcontentの文字列だけを持つobjectにする")
        result.append((item["path"], item["content"]))
    return result


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] != "check":
        print(json.dumps({"error": "usage: immutable_model.py check"}, ensure_ascii=False))
        return 2
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "標準入力が空である"}, ensure_ascii=False))
        return 2
    try:
        documents = decode_input(raw)
    except (json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 2
    problems: list[Problem] = []
    for label, markdown in documents:
        problems.extend(check_document(markdown, label))
    if problems:
        for problem in problems:
            print(problem.emit())
        return 1
    print(json.dumps({"status": "ok", "documents": len(documents)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
