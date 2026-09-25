#!/usr/bin/env python3
"""クエリデータモデルの資料（query-data-model）の BDD が読むテーブルと列が、コマンドデータモデルに実在するかを検査する。

基準資料: write-doc の query-data-model 型と command-data-model 型の「検査が読む目印」。見出しの文言は読まない。
入力: 引数に並べたクエリデータモデルのパス（一本以上）。読むテーブルの表の持ち主のリンクは、その資料のディレクトリから解決して読む。
正規化: クエリデータモデルでは、コードブロックの外で見出し行が「読むテーブル | 持ち主の資料」の表を読むテーブルとして、
  「### [BDD-<数字>]」の見出しから次の見出しまでを一件の BDD として、その中の「**`<テーブル名>`**」の行に続く表の見出し行を読む列として、
  「**取得結果**」の行を取得結果の目印として読む。持ち主のコマンドデータモデルでは、見出し行が
  「系列 | 性質 | 論理テーブル | 保存表現 | 時刻 | 変化 | 根拠」の表の論理テーブルの欄と、1行目が erDiagram の Mermaid ブロックの
  実体と属性行の名前を読む。backtick は外して比べる。
合格述語: 読むテーブルの表が一つだけあり、各行は backtick のテーブル名と相対 Markdown リンクで、同じテーブルは一行だけである。
  分類の表と erDiagram のブロックを持たない。BDD の見出しは「### [BDD-<3桁以上の数字>] <本文>」で、番号は資料の中で一意である。
  各 BDD に「**取得結果**」の行がちょうど一つあり、その後に表がある。BDD に出たテーブルはすべて読むテーブルの表にあり、
  リンク先の資料が実在してそのテーブルを分類しており、BDD の表の見出しの列名はすべて、持ち主の erDiagram のそのテーブルの列にある。
  見出し行が「業務知識のBDD | この資料のBDD」の対応の表が一つだけあり、各行の左は BDD-<番号>（重複なし）、右は BDD-<番号> を「、」で
  区切ったものか 対象外 で、右に書いた BDD はこの資料の「### [BDD-<番号>]」の見出しにある。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。終了code 1。引数が無いかファイルを読めなければ {"error"} と終了code 2。
正例: repository の scripts/fixtures/query-data-model/valid.md（持ち主は scripts/fixtures/command-data-model/valid.md）。
反例: scripts/test-query-model.sh の、持ち主の図に無い列、読むテーブルの表に無いテーブル、持ち主が分類していないテーブル、
  実在しない持ち主、取得結果の無い BDD と二つある BDD、BDD 番号の重複、分類の表を持つ資料、許されない対応の欄、この資料に無い BDD を指す対応。
意味評価として残す範囲: 取得結果が業務知識の表示対象と並び順に合うか、範囲の行の書き方が正しいか、読み取りが本当に実現できるか、
  境界の例が足りるか、物理設計の関心が混ざっていないか。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


READ_HEADERS = ["読むテーブル", "持ち主の資料"]
CLASSIFICATION_HEADERS = ["系列", "性質", "論理テーブル", "保存表現", "時刻", "変化", "根拠"]
TABLE_CELL = re.compile(r"^`([^`|]+)`$")
LINK = re.compile(r"^\[[^\]]*\]\(([^)\s]+)\)$")
BDD_ANY = re.compile(r"^###\s+\[BDD-")
BDD = re.compile(r"^###\s+\[BDD-(\d{3,})\]\s+\S")
HEADING = re.compile(r"^#{1,6}\s")
TABLE_LABEL = re.compile(r"^\*\*`([^`|]+)`\*\*\s*$")
RESULT_LABEL = "**取得結果**"
ENTITY_OPEN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\{$")
ATTRIBUTE = re.compile(r'^[A-Za-z_][A-Za-z0-9_\[\]]*\s+([A-Za-z_][A-Za-z0-9_]*)\b')


@dataclass
class Problem:
    path: str
    detail: str
    howto: str

    def emit(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def split(lines: list[str]) -> tuple[list[tuple[int, str]], list[tuple[str, list[str]]]]:
    """コードブロックの外の行と、(言語, 中身の行) のブロックを返す。"""
    prose: list[tuple[int, str]] = []
    found: list[tuple[str, list[str]]] = []
    fence: list[str] | None = None
    language = ""
    for number, line in enumerate(lines):
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith("```"):
                found.append((language, fence))
                fence = None
            else:
                fence.append(stripped)
            continue
        if stripped.startswith("```"):
            fence, language = [], stripped[3:].strip()
            continue
        prose.append((number, line))
    return prose, found


def header_rows(prose: list[tuple[int, str]], headers: list[str]) -> list[int]:
    return [i for i, (_, line) in enumerate(prose) if line.lstrip().startswith("|") and cells(line) == headers]


def er_blocks(found: list[tuple[str, list[str]]]) -> list[list[str]]:
    result = []
    for language, body in found:
        content = [line for line in body if line and not line.startswith("%%")]
        if language == "mermaid" and content and content[0] == "erDiagram":
            result.append(content)
    return result


@dataclass
class Owner:
    classified: set[str]
    columns: dict[str, set[str]]


def read_owner(path: Path) -> Owner | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    prose, found = split(text.splitlines())
    classified: set[str] = set()
    for start in header_rows(prose, CLASSIFICATION_HEADERS):
        for _, line in prose[start + 2:]:
            if not line.lstrip().startswith("|"):
                break
            row = cells(line)
            if len(row) == len(CLASSIFICATION_HEADERS):
                match = TABLE_CELL.fullmatch(row[2])
                if match:
                    classified.add(match.group(1))
    columns: dict[str, set[str]] = {}
    for block in er_blocks(found):
        current = None
        for line in block[1:]:
            opened = ENTITY_OPEN.match(line)
            if opened:
                current = opened.group(1)
                columns.setdefault(current, set())
            elif line == "}":
                current = None
            elif current is not None:
                attr = ATTRIBUTE.match(line)
                if attr:
                    columns[current].add(attr.group(1))
    return Owner(classified, columns)


def check(path: Path, text: str, owners: dict[Path, Owner | None], problems: list[Problem]) -> None:
    label = str(path)
    prose, found = split(text.splitlines())
    check_mapping(label, prose, {"対象外"}, problems)
    if header_rows(prose, CLASSIFICATION_HEADERS):
        problems.append(Problem(f"{label}.classification", "クエリデータモデルが分類の表を持っている", "テーブルはコマンドデータモデルにだけ定義し、この資料では読むテーブルの表で指す"))
    if er_blocks(found):
        problems.append(Problem(f"{label}.er", "クエリデータモデルが erDiagram を持っている", "テーブルの形はコマンドデータモデルの図にだけ描く"))

    starts = header_rows(prose, READ_HEADERS)
    reads: dict[str, str] = {}
    if len(starts) != 1:
        problems.append(Problem(f"{label}.read_tables", f"見出し行が『| {' | '.join(READ_HEADERS)} |』の表が{len(starts)}個ある", "読むテーブルの表を資料に一つだけ置く"))
    else:
        for number, line in prose[starts[0] + 2:]:
            if not line.lstrip().startswith("|"):
                break
            row = cells(line)
            where = f"{label}.read_tables.line[{number + 1}]"
            table = TABLE_CELL.fullmatch(row[0]) if len(row) == 2 else None
            link = LINK.fullmatch(row[1]) if len(row) == 2 else None
            if not table or not link:
                problems.append(Problem(where, "読むテーブルの行が、backtick のテーブル名と持ち主の資料への相対 Markdown リンクの2列になっていない", "読むテーブルと持ち主の資料をこの形で書く"))
                continue
            if table.group(1) in reads:
                problems.append(Problem(where, "同じテーブルが二行ある", "一つのテーブルは一行で書く"))
                continue
            reads[table.group(1)] = link.group(1)

    used: dict[str, set[str]] = {}
    numbers: dict[str, int] = {}
    index = 0
    while index < len(prose):
        number, line = prose[index]
        if not BDD_ANY.match(line):
            index += 1
            continue
        match = BDD.match(line)
        name = f"line[{number + 1}]"
        if not match:
            problems.append(Problem(f"{label}.{name}", "BDD の見出しが「### [BDD-<3桁以上の数字>] <本文>」の形ではない", "番号を3桁以上の数字にし、閉じ括弧の後に返る結果を書く"))
        else:
            name = f"BDD-{match.group(1)}"
            if match.group(1) in numbers:
                problems.append(Problem(f"{label}.{name}", f"BDD の番号が {numbers[match.group(1)]} 行目と重複している", "BDD の番号を資料の中で一意にする"))
            numbers.setdefault(match.group(1), number + 1)
        end = index + 1
        while end < len(prose) and not (HEADING.match(prose[end][1]) and not prose[end][1].startswith("####")):
            end += 1
        section = prose[index + 1:end]
        results = [i for i, (_, text_line) in enumerate(section) if text_line.strip() == RESULT_LABEL]
        if len(results) != 1:
            problems.append(Problem(f"{label}.{name}.取得結果", f"「{RESULT_LABEL}」の行が{len(results)}個ある", "一件の BDD に取得結果を一つだけ置き、返る項目と順を表で書く"))
        else:
            following = [text_line for _, text_line in section[results[0] + 1:] if text_line.strip()]
            if not following or not following[0].lstrip().startswith("|"):
                problems.append(Problem(f"{label}.{name}.取得結果", "取得結果の後に表が無い", "取得結果の下に返る結果の表を置く。0件なら（行なし）の行を一つ置く"))
        for i, (_, text_line) in enumerate(section):
            table = TABLE_LABEL.match(text_line.strip())
            if not table:
                continue
            following = [t for _, t in section[i + 1:] if t.strip()]
            if not following or not following[0].lstrip().startswith("|"):
                problems.append(Problem(f"{label}.{name}.{table.group(1)}", "テーブル名の後に表が無い", "読む列を見出しにした表を置く"))
                continue
            used.setdefault(table.group(1), set()).update(c.strip("`") for c in cells(following[0]) if c)
        index = end

    for table, columns in sorted(used.items()):
        where = f"{label}.{table}"
        if table not in reads:
            problems.append(Problem(where, "BDD に出たテーブルが読むテーブルの表に無い", "読むテーブルの表に、そのテーブルと持ち主のコマンドデータモデルへのリンクを書く"))
            continue
        target = (path.parent / reads[table]).resolve()
        if target not in owners:
            owners[target] = read_owner(target)
        owner = owners[target]
        if owner is None:
            problems.append(Problem(where, f"持ち主の資料を読めない: {target}", "リンクを、実在するコマンドデータモデルへの相対パスにする"))
            continue
        if table not in owner.classified:
            problems.append(Problem(where, f"持ち主の資料がこのテーブルを分類していない: {target}", "リンクを、このテーブルを定義したコマンドデータモデルに直す"))
            continue
        missing = sorted(columns - owner.columns.get(table, set()))
        if missing:
            problems.append(Problem(where, f"持ち主の図に無い列を読んでいる: {missing}", "持ち主の図の列名を使う。列が本当に無いなら、コマンドデータモデルの欠けとして差し戻す"))


MAPPING_HEADERS = ["業務知識のBDD", "この資料のBDD"]
BDD_ID = re.compile(r"^BDD-\d{3,}$")
BDD_LIST = re.compile(r"^BDD-\d{3,}(?:\s*、\s*BDD-\d{3,})*$")
OWN_BDD = re.compile(r"^###\s+\[(BDD-\d{3,})\]\s+\S")


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


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "check":
        print(json.dumps({"error": "usage: query_model.py check <クエリデータモデルのパス>..."}, ensure_ascii=False))
        return 2
    problems: list[Problem] = []
    owners: dict[Path, Owner | None] = {}
    paths = [Path(arg).resolve() for arg in sys.argv[2:]]
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            print(json.dumps({"error": f"読めない: {path}: {error}"}, ensure_ascii=False))
            return 2
        check(path, text, owners, problems)
    if problems:
        for problem in problems:
            print(problem.emit())
        return 1
    print(json.dumps({"status": "ok", "documents": len(paths)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
