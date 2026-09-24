#!/usr/bin/env python3
"""論理データモデル資料が、イミュータブルデータモデルの型に構造上合うかを検査する。

基準資料: 同梱の内部skill design-data-model の references/immutable-data-modeling.md（三つのテーブル、命名、時刻は occurred_at の一本、
  業務が与えた値）と references/technical-process-lifecycle.md（技術処理の命名と時刻）。記法は write-doc の rdb-logical-data-modeling 型。
入力: 標準入力の資料本文（Markdown）。または {"documents": [{"path", "content"}]} のJSON。
正規化: 「リソース系とイベント系」の節の7列の表を分類として、「論理データモデル図」の節の erDiagram の実体と属性行
  （型 名前 [PK|FK|UK...] "意味"）を列として、「論理テーブル定義」の節の ### `名前` を定義として読む。backtick は外して比べる。
合格述語: 分類、図の実体、定義の見出しが同じテーブルの集合で、分類は一度ずつ。系列・性質・正式な定義が許可値で、根拠が空でない。
  リソース系はイベント列を選ばない。イベント系は追加のみ・イベント列・性質が派生でなく、名前が _events で終わる。
  イベント系の時刻の列（型が timestamptz / timestamp / date か、名前が _at で終わる列）は、基底イベント（_base_events）と技術イベントでは
  occurred_at（timestamptz）の一本だけ、業務の詳細イベントでは無し。ただし意味が「業務が与えた値」で始まる列は時刻の列に数えない。
  基底イベントと技術イベントの分類表の時刻の欄は occurred_at を示す。業務の詳細イベントがあれば基底イベントもある。
  現在の状態の列は status（state、current_state、*_state を使わない）、リソースの現在の版は current_version（version などを使わない）、
  業務の基底イベントは適用後の版 version を持つ。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。終了code 1。入力を読めなければ {"error"} と終了code 2。
正例: revise-data-models/fixtures/valid.md と write-doc の rdb-logical-data-modeling の見本。
反例: scripts/validate-structure.sh の、旧列名、イベントの更新宣言、未分類のテーブル、二本目の時刻、日付の二本目の時点、
  _events で終わらないイベント表、occurred_at 以外の技術イベントの時刻、state の列、リソースの version、version の無い基底イベント。
境界例: 状態・完了日時・削除フラグ・条件付きNULLを含むだけでは拒まない。リソースの業務の日付は拒まない。
  意味が「業務が与えた値」で始まる日付の列は詳細イベントに置ける。
意味評価として残す範囲: 列が事実か業務が与えた値か導ける情報か、「業務が与えた値」の宣言が正しいか、保存表現の選択、資料間の意味の整合。
"""

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
TABLE_CELL = re.compile(r"^`([^`|]+)`$")
OCCURRED_AT = "occurred_at"
TIME_TYPES = {"timestamptz", "timestamp", "date"}
GIVEN_VALUE = "業務が与えた値"
STATUS = "status"
STATE_NAMES = {"state", "current_state", "current_status"}
CURRENT_VERSION = "current_version"
VERSION_ALIASES = {"version", "last_version", "latest_version"}
ENTITY_OPEN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\{$")
ATTRIBUTE = re.compile(r'^([A-Za-z_][A-Za-z0-9_\[\]]*)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+(?:PK|FK|UK)(?:\s*,\s*(?:PK|FK|UK))*)?(?:\s+"([^"]*)")?$')


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


def parse_headings(lines: list[str], problems: list[Problem]) -> list[str]:
    bounds = section(lines, "## 論理テーブル定義")
    if bounds is None:
        problems.append(Problem("definitions", "『論理テーブル定義』節が無い", "テーブルごとに ### `名前` の節を置く"))
        return []
    start, end = bounds
    return [m.group(1) for m in (TABLE_HEADING.match(lines[i]) for i in range(start + 1, end)) if m]


def parse_er(lines: list[str], problems: list[Problem]) -> dict[str, list[dict]]:
    """論理データモデル図の erDiagram から {実体: [{type, name, comment}]} を読む。"""
    bounds = section(lines, "## 論理データモデル図")
    if bounds is None:
        problems.append(Problem("er", "『論理データモデル図』節が無い", "erDiagram で全テーブルと全列を描く"))
        return {}
    start, end = bounds
    entities: dict[str, list[dict]] = {}
    in_er = False
    current = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_er = False
            current = None
            continue
        if stripped == "erDiagram":
            in_er = True
            continue
        if not in_er:
            continue
        opened = ENTITY_OPEN.match(stripped)
        if opened:
            current = opened.group(1)
            if current in entities:
                problems.append(Problem(f"er.{current}", "erDiagram に同じ実体が2度ある", "実体は一度だけ描く"))
            entities.setdefault(current, [])
            continue
        if stripped == "}":
            current = None
            continue
        if current is not None:
            attr = ATTRIBUTE.match(stripped)
            if not attr:
                problems.append(Problem(f"er.{current}", f"属性の行を読めない: {stripped}", "型 名前 [PK|FK] \"意味\" の形で書く"))
                continue
            entities[current].append({"type": attr.group(1), "name": attr.group(2), "comment": attr.group(3) or ""})
    if not entities:
        problems.append(Problem("er", "erDiagram に実体が1つも無い", "erDiagram で全テーブルと全列を描く"))
    return entities


def check_document(markdown: str, label: str) -> list[Problem]:
    lines = markdown.splitlines()
    problems: list[Problem] = []
    classification = parse_classification(lines, problems)
    entities = parse_er(lines, problems)
    headings = parse_headings(lines, problems)

    classified, drawn, defined = set(classification), set(entities), set(headings)
    for name in sorted(drawn - classified):
        problems.append(Problem(f"{label}.classification.{name}", "図のテーブルが分類表に無い", "系列・性質・正式な定義・時刻・変化・根拠を記載する"))
    for name in sorted(classified - drawn):
        problems.append(Problem(f"{label}.er.{name}", "分類したテーブルが図に無い", "erDiagram に実体と全列を描く"))
    for name in sorted(classified - defined):
        problems.append(Problem(f"{label}.definitions.{name}", "分類したテーブルの ### 節が論理テーブル定義に無い", "何を一つの行にまとめるかを書く節を置く"))

    for name in sorted(classified & drawn):
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
        column_names = [a["name"] for a in entities[name]]
        for column in column_names:
            if column in STATE_NAMES or column.endswith("_state"):
                problems.append(Problem(f"{prefix}.{column}", f"状態の列の名前が {STATUS} ではない: {column}", f"現在の状態の列は {STATUS} と名付ける"))
        if row["系列"] == "リソース系" and set(column_names) & VERSION_ALIASES:
            problems.append(Problem(f"{prefix}.version", f"リソースの版の列の名前が {CURRENT_VERSION} ではない: {sorted(set(column_names) & VERSION_ALIASES)}", f"リソースの現在の版は {CURRENT_VERSION} と名付ける"))
        if row["系列"] == "イベント系" and row["性質"] == "業務" and name.endswith("_base_events") and "version" not in column_names:
            problems.append(Problem(f"{prefix}.version", "基底イベントに適用後の版 version が無い", "基底イベントに、そのイベントを適用した後の版を version として置く"))
        if row["系列"] == "リソース系" and row["正式な定義"] == "イベント列":
            problems.append(Problem(f"{prefix}.正式な定義", "リソース系の論理テーブルに対し、分類表の「正式な定義」列でイベント列を選択している", "「正式な定義」列を現在状態・有効期間履歴・派生のいずれかにする"))
        if row["系列"] != "イベント系":
            continue
        if row["変化"] != "追加のみ":
            problems.append(Problem(f"{prefix}.変化", f"追加専用ではない: {row['変化']}", "イベント表は追加のみにする"))
        if row["正式な定義"] != "イベント列":
            problems.append(Problem(f"{prefix}.正式な定義", "イベント系の論理テーブルで「正式な定義」列がイベント列ではない", "「正式な定義」列をイベント列にする"))
        if row["性質"] == "派生":
            problems.append(Problem(f"{prefix}.性質", "派生物をイベント系に分類している", "業務イベントか技術イベントかを明示する"))
        if not name.endswith("_events"):
            problems.append(Problem(f"{prefix}.name", "イベント系のテーブル名が過去分詞の_eventsで終わらない", "<対象>_base_events、<対象>_<過去分詞>_events、<処理>_<過去分詞>_eventsのどれかにする"))
            continue
        times = [a for a in entities[name]
                 if (a["type"] in TIME_TYPES or a["name"].endswith("_at")) and not a["comment"].startswith(GIVEN_VALUE)]
        time_names = [a["name"] for a in times]
        detail = row["性質"] == "業務" and not name.endswith("_base_events")
        if detail:
            if time_names:
                problems.append(Problem(f"{prefix}.時刻", f"詳細イベントが時点の列を持つ: {time_names}", f"出来事の時点は基底イベントの{OCCURRED_AT}だけに置く。業務が与えた日付なら意味を「{GIVEN_VALUE}」で始める"))
            continue
        if time_names != [OCCURRED_AT]:
            problems.append(Problem(f"{prefix}.時刻", f"時点の列が{OCCURRED_AT}の一本ではない: {time_names}", f"出来事の時点は{OCCURRED_AT}の一本だけにする。業務が与えた日付なら意味を「{GIVEN_VALUE}」で始める"))
        elif times[0]["type"] != "timestamptz":
            problems.append(Problem(f"{prefix}.{OCCURRED_AT}", f"{OCCURRED_AT}の型が timestamptz ではない: {times[0]['type']}", "出来事の時点は timestamptz で持つ"))
        if OCCURRED_AT not in row["時刻"]:
            problems.append(Problem(f"{prefix}.時刻", f"分類表の時刻が{OCCURRED_AT}を示さない", f"分類表の時刻に{OCCURRED_AT}を書く"))

    business_details = [n for n, r in classification.items() if r["系列"] == "イベント系" and r["性質"] == "業務" and n.endswith("_events") and not n.endswith("_base_events")]
    business_bases = [n for n, r in classification.items() if r["系列"] == "イベント系" and r["性質"] == "業務" and n.endswith("_base_events")]
    if business_details and not business_bases:
        problems.append(Problem(f"{label}.base_events", f"詳細イベント {business_details} に対応する基底イベントが無い", "<対象>_base_events を置き、詳細イベントの主キーを基底イベントの識別子にする"))
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
