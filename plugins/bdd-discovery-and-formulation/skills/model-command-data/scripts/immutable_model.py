#!/usr/bin/env python3
"""コマンドデータモデルの資料（command-data-model）が、イミュータブルデータモデルの型とテーブルの持ち主の決まりに構造上合うかを検査する。

基準資料: この入口の SKILL.md が書くイミュータブルデータモデルの型（三つのテーブル、命名、時刻は occurred_at の一本、
  リソースの status と current_version）とテーブルの持ち主の決まり、references/technical-process-lifecycle.md（要求・回収・成功）。
  記法は write-doc の command-data-model 型の「検査が読む目印」。見出しの文言は読まない。
入力: check は、引数に並べたコマンドデータモデルのパス。最初の一本が判定する資料（保存した資料）で、残りは重複の照合に読むだけである。
  check-set は、置き場の全コマンドデータモデルのパス。それぞれを順に判定する資料にし、残りを照合の相手にして同じ判定をする。
  参照の表の持ち主のリンクは、判定する資料のディレクトリから解決して読む。
正規化: コードブロックの外で見出し行が「系列 | 性質 | 論理テーブル | 保存表現 | 根拠」の表を分類として、
  見出し行が「参照するテーブル | 読む列 | 持ち主の資料」の表を参照として、1行目が erDiagram の Mermaid ブロックの実体と属性行
  （型 名前 [PK|FK|UK...] "意味"）を列として、関係の行（<実体> <多重度> <実体> : <ラベル>）を関係として、
  ### の直後が backtick で囲んだテーブル名で始まる見出しを定義として読む。backtick は外して比べる。
合格述語: 分類の表が資料に一つだけあり、参照の表は無いか一つだけある。図の実体は、分類か参照のどちらか一方にだけある。
  分類、図の実体のうち分類したもの、定義の見出しが同じテーブルの集合で、分類は一度ずつ。系列・性質・保存表現が許可値で、根拠が空でない。
  性質は 業務 か 技術 で、リソース系はイベント列を選ばない。イベント系は保存表現がイベント列で、名前が _events で終わる。
  業務の基底イベント（_base_events）と技術イベントは occurred_at（型は timestamptz）の列を持つ。業務の詳細イベントは occurred_at の列を持たない。業務の基底イベントは version の列を持ち、関係の行で
  リソース系・業務のテーブルと結ばれ、結ばれたリソースは status と current_version の列を持つ。業務の詳細イベントがあれば基底イベントもある。
  技術の <処理>_requested_events があれば、同じ接頭辞の <処理>_claimed_events と <処理>_succeeded_events も技術として分類され、
  <処理>_claimed_events は version の列を持つ。
  参照したテーブルは、図の列が読む列と同じ集合で、持ち主の資料があれば、そのテーブルを分類し、読む列が持ち主の図の列に含まれる。
  持ち主の資料が無いことは未確認として報告し、合否に数えない（check-set では違反に数える）。持ち主の資料の欄が「範囲の外: [持ち主の資料](パス)」の参照は、
  置かれない持ち主の宣言なので照合せず、未確認にも数えない。テーブル名が「未定」なら読む列も「未定」である。読む列が仮置きの印「未定」の参照は図に描かず、
  持ち主の資料があるのに「未定」が残っていれば違反である。判定する資料が分類したテーブルを、残りの引数の資料が分類していない。
  技術の <処理>_<単位>_completed_events があれば、同じ接頭辞の <処理>_<単位>_planned_events も技術として分類されている。
  業務のリソースとその詳細イベント（同じ基底イベントと関係の行で結ばれたもの）の両方にキーでない同じ名前の列があれば、違反ではなく警告を出す。
  残りの引数の資料そのものの違反は判定しない。
  見出し行が「業務知識のBDD | この資料のBDD」の対応の表が一つだけあり、各行の左は BDD-<番号>（重複なし）、右は BDD-<番号> を「、」で
  区切ったもの・対象外・クエリデータモデル のどれかで、右に書いた BDD はこの資料の「### [BDD-<番号>]」の見出しにある。
  いずれも宣言（分類表と参照の表の値、テーブルと列の名前、関係の行）から一意に決まることだけを見る。列の名前の語尾（_at など）から、
  その列が時点かどうかは判定しない。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。未確認は {"unverified", "detail"}、警告は {"warning", "detail", "howto"} で出し、最後に
  {"status", "subject", "problems", "unverified"} を一行出す。違反があれば終了code 1、未確認だけなら 0。引数が無いかファイルを読めなければ {"error"} と終了code 2。
正例: repository の scripts/fixtures/command-data-model/ の valid.md と、それを持ち主として参照する reader.md。
反例: scripts/test-immutable-model.sh の、旧列名、性質が派生のテーブル、未分類のテーブル、_events で終わらないイベント表、
  occurred_at の無い技術イベント、occurred_at を持つ詳細イベント、version の無い基底イベント、status か current_version の無いリソース、
  リソースと結ばれていない基底イベント、成功の無い要求、version の無い回収、単位を決めた表の無い単位の完了、持ち主の資料があるのに残った未定、未定の参照を描いた図、
  分類の表が無いか二つある資料、持ち主の図に無い読む列、残りの引数の資料も同じテーブルを分類する組、許されない対応の欄、この資料に無い BDD を指す対応。
境界例: 見出しに結論を入れた資料や、見出しの名前を変えた資料は通る。持ち主の資料がまだ無い参照は未確認として通る。状態・完了日時・削除フラグ・条件付きNULLを含むだけでは拒まない。
  名前が _at で終わる列（詳細イベントの cancelled_at、基底イベントの recorded_at など）も、名前だけでは拒まない。
意味評価として残す範囲: 列が事実か業務が与えた値か後から導けない技術上の判断か加工した情報か、イベント表に二本目の時点が無いか、
  status と current_version が本当に状態と版を表しているか、保存の単位と保存表現の選択、どの業務がテーブルを書くべきか、
  技術処理の諦める出来事が要るか、資料間の意味の整合。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_HEADERS = ["系列", "性質", "論理テーブル", "保存表現", "根拠"]
REFERENCE_HEADERS = ["参照するテーブル", "読む列", "持ち主の資料"]
ALLOWED_SERIES = {"リソース系", "イベント系"}
ALLOWED_NATURES = {"業務", "技術"}
ALLOWED_SOURCES = {"現在状態", "有効期間履歴", "イベント列", "派生"}
TABLE_HEADING = re.compile(r"^###\s+`([^`|]+)`")
TABLE_CELL = re.compile(r"^`([^`|]+)`$")
COLUMN_LIST = re.compile(r"^`[^`]+`(?:\s*、\s*`[^`]+`)*$")
LINK = re.compile(r"^\[[^\]]*\]\(([^)\s]+)\)$")
OUTSIDE = re.compile(r"^範囲の外:\s*\[[^\]]*\]\(([^)\s]+)\)$")
OCCURRED_AT = "occurred_at"
ENTITY_OPEN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\{$")
ATTRIBUTE = re.compile(r'^([A-Za-z_][A-Za-z0-9_\[\]]*)\s+([A-Za-z_][A-Za-z0-9_]*)(\s+(?:PK|FK|UK)(?:\s*,\s*(?:PK|FK|UK))*)?(?:\s+"([^"]*)")?$')
PENDING = "未定"
RELATION = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s+([|}o{]{2}(?:--|\.\.)[|}o{]{2})\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*.+$')


@dataclass
class Problem:
    path: str
    detail: str
    howto: str

    def emit(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


@dataclass
class Model:
    classification: dict[str, dict[str, str]] = field(default_factory=dict)
    references: dict[str, tuple[list[str], str]] = field(default_factory=dict)
    entities: dict[str, list[dict]] = field(default_factory=dict)
    relations: list[tuple[str, str]] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)


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


def table_rows(prose: list[tuple[int, str]], headers: list[str]) -> list[list[tuple[int, list[str]]]]:
    """見出し行が headers の表を探し、表ごとに (行番号, セル) の列を返す。"""
    tables: list[list[tuple[int, list[str]]]] = []
    starts = [i for i, (_, line) in enumerate(prose) if line.lstrip().startswith("|") and split_cells(line) == headers]
    for start in starts:
        rows: list[tuple[int, list[str]]] = []
        for number, line in prose[start + 2:]:
            if not line.lstrip().startswith("|"):
                break
            rows.append((number, split_cells(line)))
        tables.append(rows)
    return tables


def parse_classification(label: str, prose: list[tuple[int, str]], problems: list[Problem]) -> dict[str, dict[str, str]]:
    tables = table_rows(prose, REQUIRED_HEADERS)
    if len(tables) != 1:
        problems.append(Problem(f"{label}.classification", f"見出し行が『| {' | '.join(REQUIRED_HEADERS)} |』の分類表が{len(tables)}個ある", "分類表を資料に一つだけ置く"))
        return {}
    rows: dict[str, dict[str, str]] = {}
    for line_number, cells in tables[0]:
        if len(cells) != len(REQUIRED_HEADERS):
            problems.append(Problem(f"{label}.classification.line[{line_number + 1}]", "列数が分類表headerと一致しない", "各行を5列にする"))
            continue
        row = dict(zip(REQUIRED_HEADERS, cells))
        match = TABLE_CELL.fullmatch(row["論理テーブル"])
        if not match:
            problems.append(Problem(f"{label}.classification.line[{line_number + 1}].論理テーブル", "単一のテーブル名をbacktickで囲んでいない", "1行に1テーブルを書く"))
            continue
        name = match.group(1)
        if name in rows:
            problems.append(Problem(f"{label}.classification.{name}", "分類が重複している", "各テーブルを一度だけ分類する"))
            continue
        rows[name] = row
    return rows


def parse_references(label: str, prose: list[tuple[int, str]], problems: list[Problem]) -> dict[str, tuple[list[str], str]]:
    tables = table_rows(prose, REFERENCE_HEADERS)
    if len(tables) > 1:
        problems.append(Problem(f"{label}.references", f"見出し行が『| {' | '.join(REFERENCE_HEADERS)} |』の参照の表が{len(tables)}個ある", "参照の表は資料に一つだけ置く"))
    references: dict[str, tuple[list[str], str]] = {}
    for line_number, cells in (tables[0] if tables else []):
        where = f"{label}.references.line[{line_number + 1}]"
        if len(cells) != len(REFERENCE_HEADERS):
            problems.append(Problem(where, "列数が参照の表の見出しと一致しない", "各行を3列にする"))
            continue
        table, columns, owner = cells
        pending_table = table.strip("`") == PENDING
        match = TABLE_CELL.fullmatch(table)
        if not (match or pending_table) or not (COLUMN_LIST.fullmatch(columns) or columns == PENDING) or not (LINK.fullmatch(owner) or OUTSIDE.fullmatch(owner)):
            problems.append(Problem(where, "参照の行が、backtick のテーブル名か「未定」、backtick の列名を「、」で区切った並びか「未定」、持ち主の資料への相対 Markdown リンクか「範囲の外: [持ち主の資料](パス)」になっていない", "参照するテーブル、読む列、持ち主の資料をこの形で書く"))
            continue
        if pending_table and columns != PENDING:
            problems.append(Problem(where, f"テーブル名が「{PENDING}」なのに読む列が書かれている", f"持ち主が決めるテーブル名が分からないなら、読む列も「{PENDING}」にする"))
            continue
        name = f"{PENDING}@line{line_number + 1}" if pending_table else match.group(1)
        if name in references:
            problems.append(Problem(where, "同じテーブルの参照が二行ある", "一つのテーブルは一行で参照する"))
            continue
        link = LINK.fullmatch(owner)
        references[name] = ([PENDING] if columns == PENDING else re.findall(r"`([^`]+)`", columns), link.group(1) if link else "")
    return references


def parse_er(label: str, lines: list[str], problems: list[Problem]) -> tuple[dict[str, list[dict]], list[tuple[str, str]]]:
    """1行目が erDiagram の Mermaid ブロックから実体と関係を読む。複数のブロックは合わせて読む。"""
    entities: dict[str, list[dict]] = {}
    relations: list[tuple[str, str]] = []
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
                    problems.append(Problem(f"{label}.er.{current}", "erDiagram に同じ実体が2度ある", "実体は一度だけ描く"))
                entities.setdefault(current, [])
                continue
            if stripped == "}":
                current = None
                continue
            if current is not None:
                attr = ATTRIBUTE.match(stripped)
                if not attr:
                    problems.append(Problem(f"{label}.er.{current}", f"属性の行を読めない: {stripped}", "型 名前 [PK|FK] \"意味\" の形で書く"))
                    continue
                entities[current].append({"type": attr.group(1), "name": attr.group(2), "key": bool(attr.group(3)), "comment": attr.group(4) or ""})
                continue
            relation = RELATION.match(stripped)
            if relation:
                relations.append((relation.group(1), relation.group(3)))
    if not entities:
        problems.append(Problem(f"{label}.er", "erDiagram に実体が1つも無い", "1行目が erDiagram の Mermaid ブロックで全テーブルと全列を描く"))
    return entities, relations


def read_model(label: str, markdown: str, problems: list[Problem]) -> Model:
    lines = markdown.splitlines()
    prose = prose_lines(lines)
    model = Model()
    model.classification = parse_classification(label, prose, problems)
    model.references = parse_references(label, prose, problems)
    model.entities, model.relations = parse_er(label, lines, problems)
    model.headings = [m.group(1) for m in (TABLE_HEADING.match(line) for _, line in prose) if m]
    return model


def columns_of(model: Model, name: str) -> list[str]:
    return [a["name"] for a in model.entities.get(name, [])]


def check_model(label: str, model: Model, problems: list[Problem]) -> None:
    classification = model.classification
    classified, referenced = set(classification), set(model.references)
    drawn, defined = set(model.entities), set(model.headings)
    for name in sorted(classified & referenced):
        problems.append(Problem(f"{label}.references.{name}", "同じテーブルを分類と参照の両方に載せている", "書くテーブルは分類に、ほかの資料が書くテーブルは参照にだけ載せる"))
    for name in sorted(drawn - classified - referenced):
        problems.append(Problem(f"{label}.classification.{name}", "図のテーブルが分類表にも参照の表にも無い", "書くテーブルは分類に、ほかの資料が書くテーブルは参照に載せる"))
    for name in sorted(classified - drawn):
        problems.append(Problem(f"{label}.er.{name}", "分類したテーブルが図に無い", "erDiagram に実体と全列を描く"))
    pending = {n for n, (read, _) in model.references.items() if read == [PENDING]}
    for name in sorted(pending & drawn):
        problems.append(Problem(f"{label}.er.{name}", f"読む列が「{PENDING}」の参照を図に描いている", "持ち主の資料ができるまで、そのテーブルは図にもBDDの行にも載せない"))
    for name in sorted(referenced - drawn - pending):
        problems.append(Problem(f"{label}.er.{name}", "参照したテーブルが図に無い", "erDiagram に読む列だけで描く"))
    for name in sorted(classified - defined):
        problems.append(Problem(f"{label}.definitions.{name}", "分類したテーブルの ### `名前` の見出しが無い", "何を一つの行にまとめるかを書く節を置く"))
    for name in sorted(referenced & defined):
        problems.append(Problem(f"{label}.definitions.{name}", "参照したテーブルに ### `名前` の定義の見出しがある", "定義は持ち主の資料にだけ置く"))
    for name in sorted((referenced & drawn) - pending):
        read, _ = model.references[name]
        if sorted(columns_of(model, name)) != sorted(read):
            problems.append(Problem(f"{label}.er.{name}", f"参照したテーブルの図の列が読む列と一致しない: 図 {columns_of(model, name)}、読む列 {read}", "参照したテーブルは、読む列だけで図に描く"))

    related: dict[str, set[str]] = {}
    for left, right in model.relations:
        related.setdefault(left, set()).add(right)
        related.setdefault(right, set()).add(left)

    for name in sorted(classified & drawn):
        row = classification[name]
        prefix = f"{label}.{name}"
        if row["系列"] not in ALLOWED_SERIES:
            problems.append(Problem(f"{prefix}.系列", f"許可値ではない: {row['系列']}", "リソース系またはイベント系にする"))
        if row["性質"] not in ALLOWED_NATURES:
            problems.append(Problem(f"{prefix}.性質", f"許可値ではない: {row['性質']}", "業務か技術にする"))
        if row["保存表現"] not in ALLOWED_SOURCES:
            problems.append(Problem(f"{prefix}.保存表現", f"許可値ではない: {row['保存表現']}", "分類表の「保存表現」列を現在状態・有効期間履歴・イベント列・派生のいずれかにする"))
        if not row["根拠"] or row["根拠"] in {"-", "なし"}:
            problems.append(Problem(f"{prefix}.根拠", "分類表の根拠の欄が空か「-」「なし」である", "対応する業務知識または技術要件の参照を記載する"))
        column_names = columns_of(model, name)
        is_business_base = row["系列"] == "イベント系" and row["性質"] == "業務" and name.endswith("_base_events")
        if is_business_base:
            if "version" not in column_names:
                problems.append(Problem(f"{prefix}.version", "基底イベントに適用後の版 version が無い", "基底イベントに、そのイベントを適用した後の版を version として置く"))
            resources = sorted(r for r in related.get(name, set()) if classification.get(r, {}).get("系列") == "リソース系" and classification.get(r, {}).get("性質") == "業務")
            if not resources:
                problems.append(Problem(f"{prefix}.resource", "基底イベントが関係の行でリソース系・業務のテーブルと結ばれていない", "erDiagram に <リソース> ||--|{ <対象>_base_events : \"...\" の関係の行を描く"))
            for resource in resources:
                missing = [c for c in ("status", "current_version") if c not in columns_of(model, resource)]
                if missing:
                    problems.append(Problem(f"{label}.{resource}", f"イベント列を持つリソースに {'・'.join(missing)} の列が無い", "イベント列を選んだ対象のリソースには、状態が一つでも status と current_version を置く"))
        if row["系列"] == "リソース系" and row["保存表現"] == "イベント列":
            problems.append(Problem(f"{prefix}.保存表現", "リソース系の論理テーブルに対し、分類表の「保存表現」列でイベント列を選択している", "「保存表現」列を現在状態・有効期間履歴・派生のいずれかにする"))
        if row["系列"] != "イベント系":
            continue
        if row["保存表現"] != "イベント列":
            problems.append(Problem(f"{prefix}.保存表現", "イベント系の論理テーブルで「保存表現」列がイベント列ではない", "「保存表現」列をイベント列にする"))
        if not name.endswith("_events"):
            problems.append(Problem(f"{prefix}.name", "イベント系のテーブル名が過去分詞の_eventsで終わらない", "<対象>_base_events、<対象>_<過去分詞>_events、<処理>_<過去分詞>_eventsのどれかにする"))
            continue
        occurred = [a for a in model.entities[name] if a["name"] == OCCURRED_AT]
        if row["性質"] == "業務" and not name.endswith("_base_events"):
            if occurred:
                problems.append(Problem(f"{prefix}.時刻", f"詳細イベントが {OCCURRED_AT} の列を持つ", f"出来事の時点は基底イベントの {OCCURRED_AT} にだけ置く"))
            continue
        if not occurred:
            problems.append(Problem(f"{prefix}.{OCCURRED_AT}", f"{OCCURRED_AT} の列が無い", f"出来事が起きた時点を {OCCURRED_AT} として置く"))
        elif occurred[0]["type"] != "timestamptz":
            problems.append(Problem(f"{prefix}.{OCCURRED_AT}", f"{OCCURRED_AT} の型が timestamptz ではない: {occurred[0]['type']}", f"{OCCURRED_AT} は timestamptz で持つ"))

    technical = {n for n, r in classification.items() if r["性質"] == "技術" and r["系列"] == "イベント系"}
    for name in sorted(technical):
        if not name.endswith("_requested_events"):
            continue
        process = name[: -len("_requested_events")]
        for suffix in ("_claimed_events", "_succeeded_events"):
            if process + suffix not in technical:
                problems.append(Problem(f"{label}.{name}", f"要求に対応する {process}{suffix} が技術イベントとして分類されていない", "技術処理は、要求・回収・成功の三つの表を同じ接頭辞でそろえる"))
        claimed = process + "_claimed_events"
        if claimed in technical and claimed in model.entities and "version" not in columns_of(model, claimed):
            problems.append(Problem(f"{label}.{claimed}.version", "回収の表に要求の中での回収の版 version が無い", "回収の表に version を置く"))

    for name in sorted(technical):
        if name.endswith("_completed_events") and name[: -len("_completed_events")] + "_planned_events" not in technical:
            problems.append(Problem(f"{label}.{name}", f"単位の完了に対応する {name[: -len('_completed_events')]}_planned_events が技術イベントとして分類されていない", "単位を決めた事実を <処理>_<単位>_planned_events に置く。要求全体の成功の判定に単位の集合が要るからである"))

    business_details = [n for n, r in classification.items() if r["系列"] == "イベント系" and r["性質"] == "業務" and n.endswith("_events") and not n.endswith("_base_events")]
    business_bases = [n for n, r in classification.items() if r["系列"] == "イベント系" and r["性質"] == "業務" and n.endswith("_base_events")]
    if business_details and not business_bases:
        problems.append(Problem(f"{label}.base_events", f"詳細イベント {business_details} に対応する基底イベントが無い", "<対象>_base_events を置き、詳細イベントの主キーを基底イベントの識別子にする"))


MAPPING_HEADERS = ["業務知識のBDD", "この資料のBDD"]
BDD_ID = re.compile(r"^BDD-\d{3,}$")
BDD_LIST = re.compile(r"^BDD-\d{3,}(?:\s*、\s*BDD-\d{3,})*$")
OWN_BDD = re.compile(r"^###\s+\[(BDD-\d{3,})\]\s+\S")


def find_copies(model: Model) -> list[dict]:
    """リソースとその詳細イベントの両方にある、キーでない同じ名前の列を警告として返す。"""
    classification = model.classification
    related: dict[str, set[str]] = {}
    for left, right in model.relations:
        related.setdefault(left, set()).add(right)
        related.setdefault(right, set()).add(left)
    warnings: list[dict] = []
    for base in sorted(n for n, r in classification.items() if r["系列"] == "イベント系" and r["性質"] == "業務" and n.endswith("_base_events")):
        resources = [r for r in related.get(base, set()) if classification.get(r, {}).get("系列") == "リソース系"]
        details = [d for d in related.get(base, set()) if d != base and d.endswith("_events") and classification.get(d, {}).get("性質") == "業務"]
        for resource in resources:
            names = {a["name"] for a in model.entities.get(resource, []) if not a["key"]}
            for detail in details:
                for column in sorted(names & {a["name"] for a in model.entities.get(detail, []) if not a["key"]}):
                    warnings.append({"warning": f"{resource}.{column}", "detail": f"同じ名前の列がリソースと詳細イベント {detail} の両方にある", "howto": "今の業務知識の行いに要る写しかを読み直す。先回りした写しなら片方だけにする"})
    return warnings


def check_mapping(label: str, prose: list[tuple[int, str]], words: set[str], problems: list[Problem]) -> None:
    """業務知識のBDDとの対応の表を一つ読み、欄の形と、指したこの資料のBDDが実在するかを見る。"""
    starts = [i for i, (_, line) in enumerate(prose) if line.lstrip().startswith("|") and [c.strip() for c in line.strip().strip("|").split("|")] == MAPPING_HEADERS]
    if len(starts) != 1:
        problems.append(Problem(f"{label}.mapping", f"見出し行が『| {' | '.join(MAPPING_HEADERS)} |』の対応の表が{len(starts)}個ある", "業務知識のBDDとの対応の表を資料に一つだけ置く"))
        return
    own = {m.group(1) for m in (OWN_BDD.match(line) for _, line in prose) if m}
    seen: set[str] = set()
    for number, line in prose[starts[0] + 2:]:
        if not line.lstrip().startswith("|"):
            break
        row = [c.strip() for c in line.strip().strip("|").split("|")]
        where = f"{label}.mapping.line[{number + 1}]"
        if len(row) != 2 or not BDD_ID.fullmatch(row[0]):
            problems.append(Problem(where, "対応の行が、BDD-<番号> と、この資料のBDDの欄の2列になっていない", "業務知識のBDDを一行に一つ、BDD-<番号> で書く"))
            continue
        if row[0] in seen:
            problems.append(Problem(where, f"業務知識の {row[0]} が二行ある", "業務知識のBDDは一行だけに置く"))
        seen.add(row[0])
        if row[1] in words:
            continue
        if not BDD_LIST.fullmatch(row[1]):
            problems.append(Problem(where, f"この資料のBDDの欄が許された形ではない: {row[1]}", f"BDD-<番号> を「、」で区切ったものか、{'・'.join(sorted(words))} のどれかにする。理由は表の後の本文に書く"))
            continue
        for target in re.findall(r"BDD-\d{3,}", row[1]):
            if target not in own:
                problems.append(Problem(where, f"この資料に {target} が無い", "この資料にある BDD の番号を書く"))


def check_references(path: Path, model: Model, models: dict[Path, Model | None], problems: list[Problem], unverified: list[dict]) -> None:
    for name, (read, link) in sorted(model.references.items()):
        if not link:
            continue
        target = (path.parent / link).resolve()
        if target not in models:
            try:
                models[target] = read_model(str(target), target.read_text(encoding="utf-8"), [])
            except OSError:
                models[target] = None
        owner = models[target]
        where = f"{path}.references.{name}"
        if owner is None:
            unverified.append({"unverified": str(target), "detail": f"持ち主の資料がまだ無いので、`{name}` の読む列を照合していない"})
            continue
        if read == [PENDING]:
            problems.append(Problem(where, f"持ち主の資料があるのに「{PENDING}」のまま残っている: {target}", "同じ入口で深めて、持ち主の列に替える"))
            continue
        if name not in owner.classification:
            problems.append(Problem(where, f"持ち主の資料がこのテーブルを分類していない: {target}", "リンクを、このテーブルへ書く業務のコマンドデータモデルに直す"))
            continue
        missing = [c for c in read if c not in columns_of(owner, name)]
        if missing:
            problems.append(Problem(where, f"読む列が持ち主の図に無い: {missing}", "持ち主の図にある列名を使う。列が足りなければ持ち主の資料への変更案として返す"))


def judge(subject: Path, others: list[Path], texts: dict[Path, str]) -> tuple[list[Problem], list[dict], list[dict]]:
    """subject だけを判定し、others は重複の照合に読む。"""
    label = str(subject)
    problems: list[Problem] = []
    unverified: list[dict] = []
    models: dict[Path, Model | None] = {}
    model = read_model(label, texts[subject], problems)
    models[subject] = model
    check_mapping(label, prose_lines(texts[subject].splitlines()), {"対象外", "クエリデータモデル"}, problems)
    check_model(label, model, problems)
    for path in others:
        if path == subject:
            continue
        other = read_model(str(path), texts[path], [])
        models[path] = other
        for name in sorted(set(model.classification) & set(other.classification)):
            problems.append(Problem(f"{label}.classification.{name}", f"同じテーブルをほかの資料も分類している: {path}", "テーブルは、そこへ書く業務の資料一本だけが分類する。分け方の一覧で自分が持ち主なら相手への変更案として返し、そうでなければ参照の表に移す"))
    check_references(subject, model, models, problems, unverified)
    return problems, unverified, find_copies(model)


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in {"check", "check-set"}:
        print(json.dumps({"error": "usage: immutable_model.py check <保存した資料のパス> [<ほかのコマンドデータモデルのパス>...] | check-set <置き場の全コマンドデータモデルのパス>..."}, ensure_ascii=False))
        return 2
    paths = [Path(arg).resolve() for arg in sys.argv[2:]]
    texts: dict[Path, str] = {}
    for path in paths:
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except OSError as error:
            print(json.dumps({"error": f"読めない: {path}: {error}"}, ensure_ascii=False))
            return 2
        if not texts[path].strip():
            print(json.dumps({"error": f"資料が空である: {path}"}, ensure_ascii=False))
            return 2
    if sys.argv[1] == "check":
        problems, unverified, warnings = judge(paths[0], paths[1:], texts)
        for problem in problems:
            print(problem.emit())
        for item in unverified + warnings:
            print(json.dumps(item, ensure_ascii=False))
        print(json.dumps({"status": "ng" if problems else "ok", "subject": str(paths[0]), "problems": len(problems), "unverified": len(unverified), "warnings": len(warnings)}, ensure_ascii=False))
        return 1 if problems else 0
    total = 0
    for subject in paths:
        problems, unverified, warnings = judge(subject, paths, texts)
        for problem in problems:
            print(problem.emit())
        for item in unverified:
            print(Problem(f"{subject}.references", f"集合がそろった後も持ち主の資料が無い: {item['unverified']}", "持ち主の資料を置くか、参照の表のリンクを直す").emit())
        for item in warnings:
            print(json.dumps(item, ensure_ascii=False))
        total += len(problems) + len(unverified)
    print(json.dumps({"status": "ng" if total else "ok", "documents": len(paths), "problems": total}, ensure_ascii=False))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
