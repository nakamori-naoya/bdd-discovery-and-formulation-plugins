#!/usr/bin/env python3
"""論理データモデル資料が、イミュータブルデータモデルの型に構造上合うかを検査する。

基準資料: 同梱の内部skill design-data-model の references/immutable-data-modeling.md（三つのテーブル、命名、時刻は occurred_at の一本、
  業務が与えた値）と references/technical-process-lifecycle.md（技術処理の命名と時刻）。記法は write-doc の公開契約が rdb-logical-data-modeling 型について宣言した「検査が読む目印」。見出しの文言は読まない。
入力: 標準入力の資料本文（Markdown）。または {"documents": [{"path", "content"}]} のJSON。
正規化: コードブロックの外で見出し行が「系列 | 性質 | 論理テーブル | 保存表現 | 時刻 | 変化 | 根拠」の表を分類として、
  1行目が erDiagram の Mermaid ブロックの実体と属性行（型 名前 [PK|FK|UK...] "意味"）を列として、
  ### の直後が backtick で囲んだテーブル名で始まる見出しを定義として読む。どれも資料のどの見出しの下にあってもよい。backtick は外して比べる。
合格述語: 分類の表が資料に一つだけあり、分類、図の実体、定義の見出しが同じテーブルの集合で、分類は一度ずつ。系列・性質・保存表現が許可値で、根拠が空でない。
  リソース系はイベント列を選ばない。イベント系は追加のみ・イベント列・性質が派生でなく、名前が _events で終わる。
  イベント系の表で名前が _at で終わる列は、業務の基底イベント（_base_events）と技術イベントでは occurred_at（型は timestamptz）だけで、
  必ずある。分類表の時刻の欄は `occurred_at` と完全に一致する（backtick は外す）。業務の詳細イベントは _at で終わる列を持たない。業務の基底イベントは version の列を持つ。業務の詳細イベントがあれば基底イベントもある。
  いずれも宣言（分類表の値、テーブルと列の名前）から一意に決まることだけを見る。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。終了code 1。入力を読めなければ {"error"} と終了code 2。
正例: revise-data-models/fixtures/valid.md と write-doc の rdb-logical-data-modeling の見本。
反例: scripts/validate-structure.sh の、旧列名、イベントの更新宣言、未分類のテーブル、_events で終わらないイベント表、
  occurred_at の無い技術イベント、_at の列を持つ詳細イベント、occurred_at のほかの _at の列、version の無い基底イベント、
  時刻の欄が `occurred_at` と一致しない分類表、分類の表が無いか二つある資料。
境界例: 見出しに結論を入れた資料や、見出しの名前を変えた資料は通る。状態・完了日時・削除フラグ・条件付きNULLを含むだけでは拒まない。名前が _at で終わらない日付の列（返却期限の due_on など）は拒まない。
意味評価として残す範囲: 列が事実か業務が与えた値か加工した情報か、イベント表に二本目の時点が無いか（日付の列が出来事の時点の写しでないか）、
  状態と版の列の名前が status・current_version になっているか、保存表現の選択、資料間の意味の整合。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass


REQUIRED_HEADERS = ["系列", "性質", "論理テーブル", "保存表現", "時刻", "変化", "根拠"]
ALLOWED_SERIES = {"リソース系", "イベント系"}
ALLOWED_NATURES = {"業務", "技術", "派生"}
ALLOWED_SOURCES = {"現在状態", "有効期間履歴", "イベント列", "派生"}
TABLE_HEADING = re.compile(r"^###\s+`([^`|]+)`")
TABLE_CELL = re.compile(r"^`([^`|]+)`$")
OCCURRED_AT = "occurred_at"
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


def prose_lines(lines: list[str]) -> list[tuple[int, str]]:
    """コードブロックの外の行を (行番号, 行) で返す。"""
    result: list[tuple[int, str]] = []
    in_code = False
    for number, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            result.append((number, line))
    return result


def parse_classification(lines: list[str], problems: list[Problem]) -> dict[str, dict[str, str]]:
    """見出し行が契約の7列の表を資料全体から一つ探し、分類として読む。"""
    prose = prose_lines(lines)
    starts = [i for i, (_, line) in enumerate(prose) if line.lstrip().startswith("|") and split_cells(line) == REQUIRED_HEADERS]
    if len(starts) != 1:
        problems.append(Problem("classification", f"見出し行が『| {' | '.join(REQUIRED_HEADERS)} |』の分類表が{len(starts)}個ある", "分類表を資料に一つだけ置く"))
        return {}
    headers = REQUIRED_HEADERS
    rows: dict[str, dict[str, str]] = {}
    for line_number, line in prose[starts[0] + 2:]:
        if not line.lstrip().startswith("|"):
            break
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
    """### の直後が backtick で囲んだテーブル名で始まる見出しを、テーブルの定義として読む。"""
    return [m.group(1) for m in (TABLE_HEADING.match(line) for _, line in prose_lines(lines)) if m]


def parse_er(lines: list[str], problems: list[Problem]) -> dict[str, list[dict]]:
    """1行目が erDiagram の Mermaid ブロックから {実体: [{type, name, comment}]} を読む。複数のブロックは合わせて読む。"""
    entities: dict[str, list[dict]] = {}
    fence: list[str] | None = None
    language = ""
    blocks: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith("```"):
                if language == "mermaid":
                    blocks.append(fence)
                fence = None
            else:
                fence.append(stripped)
            continue
        if stripped.startswith("```"):
            fence, language = [], stripped[3:].strip()
    for block in blocks:
        content = [line for line in block if line and not line.startswith("%%")]
        if not content or content[0] != "erDiagram":
            continue
        current = None
        for stripped in content[1:]:
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
        problems.append(Problem("er", "erDiagram に実体が1つも無い", "1行目が erDiagram の Mermaid ブロックで全テーブルと全列を描く"))
    return entities


def check_document(markdown: str, label: str) -> list[Problem]:
    lines = markdown.splitlines()
    problems: list[Problem] = []
    classification = parse_classification(lines, problems)
    entities = parse_er(lines, problems)
    headings = parse_headings(lines, problems)

    classified, drawn, defined = set(classification), set(entities), set(headings)
    for name in sorted(drawn - classified):
        problems.append(Problem(f"{label}.classification.{name}", "図のテーブルが分類表に無い", "系列・性質・保存表現・時刻・変化・根拠を記載する"))
    for name in sorted(classified - drawn):
        problems.append(Problem(f"{label}.er.{name}", "分類したテーブルが図に無い", "erDiagram に実体と全列を描く"))
    for name in sorted(classified - defined):
        problems.append(Problem(f"{label}.definitions.{name}", "分類したテーブルの ### `名前` の見出しが無い", "何を一つの行にまとめるかを書く節を置く"))

    for name in sorted(classified & drawn):
        row = classification[name]
        prefix = f"{label}.{name}"
        if row["系列"] not in ALLOWED_SERIES:
            problems.append(Problem(f"{prefix}.系列", f"許可値ではない: {row['系列']}", "リソース系またはイベント系にする"))
        if row["性質"] not in ALLOWED_NATURES:
            problems.append(Problem(f"{prefix}.性質", f"許可値ではない: {row['性質']}", "業務・技術・派生のいずれかにする"))
        if row["保存表現"] not in ALLOWED_SOURCES:
            problems.append(Problem(f"{prefix}.保存表現", f"許可値ではない: {row['保存表現']}", "分類表の「保存表現」列を現在状態・有効期間履歴・イベント列・派生のいずれかにする"))
        if not row["根拠"] or row["根拠"] in {"-", "なし"}:
            problems.append(Problem(f"{prefix}.根拠", "分類表の根拠の欄が空か「-」「なし」である", "対応する業務知識または技術要件の参照を記載する"))
        column_names = [a["name"] for a in entities[name]]
        if row["系列"] == "イベント系" and row["性質"] == "業務" and name.endswith("_base_events") and "version" not in column_names:
            problems.append(Problem(f"{prefix}.version", "基底イベントに適用後の版 version が無い", "基底イベントに、そのイベントを適用した後の版を version として置く"))
        if row["系列"] == "リソース系" and row["保存表現"] == "イベント列":
            problems.append(Problem(f"{prefix}.保存表現", "リソース系の論理テーブルに対し、分類表の「保存表現」列でイベント列を選択している", "「保存表現」列を現在状態・有効期間履歴・派生のいずれかにする"))
        if row["系列"] != "イベント系":
            continue
        if row["変化"] != "追加のみ":
            problems.append(Problem(f"{prefix}.変化", f"追加専用ではない: {row['変化']}", "イベント表は追加のみにする"))
        if row["保存表現"] != "イベント列":
            problems.append(Problem(f"{prefix}.保存表現", "イベント系の論理テーブルで「保存表現」列がイベント列ではない", "「保存表現」列をイベント列にする"))
        if row["性質"] == "派生":
            problems.append(Problem(f"{prefix}.性質", "派生物をイベント系に分類している", "業務イベントか技術イベントかを明示する"))
        if not name.endswith("_events"):
            problems.append(Problem(f"{prefix}.name", "イベント系のテーブル名が過去分詞の_eventsで終わらない", "<対象>_base_events、<対象>_<過去分詞>_events、<処理>_<過去分詞>_eventsのどれかにする"))
            continue
        at_columns = [a for a in entities[name] if a["name"].endswith("_at")]
        detail = row["性質"] == "業務" and not name.endswith("_base_events")
        if detail:
            if at_columns:
                problems.append(Problem(f"{prefix}.時刻", f"詳細イベントが _at の列を持つ: {[a['name'] for a in at_columns]}", f"出来事の時点は基底イベントの {OCCURRED_AT} にだけ置く"))
            continue
        extra = [a["name"] for a in at_columns if a["name"] != OCCURRED_AT]
        if extra:
            problems.append(Problem(f"{prefix}.時刻", f"_at の列が {OCCURRED_AT} のほかにある: {extra}", f"イベント表の _at の列は {OCCURRED_AT} だけにする"))
        occurred = [a for a in at_columns if a["name"] == OCCURRED_AT]
        if not occurred:
            problems.append(Problem(f"{prefix}.{OCCURRED_AT}", f"{OCCURRED_AT} の列が無い", f"出来事が起きた時点を {OCCURRED_AT} として置く"))
        elif occurred[0]["type"] != "timestamptz":
            problems.append(Problem(f"{prefix}.{OCCURRED_AT}", f"{OCCURRED_AT} の型が timestamptz ではない: {occurred[0]['type']}", f"{OCCURRED_AT} は timestamptz で持つ"))
        if row["時刻"].strip("`") != OCCURRED_AT:
            problems.append(Problem(f"{prefix}.時刻", f"分類表の時刻の欄が `{OCCURRED_AT}` と一致しない: {row['時刻']}", f"分類表の時刻の欄を `{OCCURRED_AT}` だけにする"))

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
