#!/usr/bin/env python3
"""業務知識の資料（business-knowledge）が、目印の形に合うかを検査する。

基準資料: write-doc の business-knowledge 型の「検査が読む目印」と、この入口の references/judgment.md の
  「業務をまたぐ決まりと名前は、一か所だけが持つ」。`###` の項目の名前と表のセルの名前は照合するが、本文の文言は読まない。
入力: check は、判定する資料（保存した資料）のパス一本。check-set は、明示された業務知識のパスで、それぞれを check と同じく判定し、
  あわせて資料どうしを照合する。前提のリンクは、その資料のディレクトリから解決する。
合格述語:
  コードブロックの外で、`#` の見出しは表題の一つだけで、`##` の見出しは「この業務の核、前提、制約、状況、計算、行動・出来事と判断、
  まだ決まっていないこと、BDD」の八つがこの順に一度ずつあり、ほかに無い。
  前提、制約、状況、計算の `###` の名前は、この四つの節を通して一意で、「、」を含まない。状況の名前は、末尾の「（<英名>）」を外したものとする。
  見出し行が「| いつ | 誰が | 何をすると | 何が起きる | どの決まりによるか |」の表は資料に高々一つで、行動・出来事と判断の節にあり、
  その節にほかの表は無い。表の各行は五列である。いつの欄は「、」で区切った状況の名前で、状況の節に項目が無い資料だけ「いつでも」である。
  どの決まりによるかの欄を「、」で区切った各名前は前提、制約、状況、計算のどれかの名前である。
  何が起きるの欄が「できない。」で始まる行（できない行）には、制約、前提、状況の名前が一つ以上ある。ほかの行だけ、欄を「—」にしてよい。
  「### [BDD-」で始まる見出しは BDD の節の下にだけあり、BDD の節の `###` はすべて「### [BDD-<3桁以上の数字>] <業務結果>」の形で、番号は資料の中で一意である。
  gherkin ブロックの「NOTE: Rule: <名前>」の名前は、制約、前提、状況の名前のどれかである。NOTE の無い BDD が拒否かどうかは決まらないので判定しない。
  決定表: 制約か計算の項目の下で、見出し行の最後の列が「答え」の表を決定表とする。計算の一項目に決定表は高々一つである。各行は見出しと同じ列数で、空の欄が無い。
  条件の列ごとに、その列に現れる「どれでも」以外の値を取りうる値とし、取りうる値の組み合わせのどれにも、当てはまる行（同じ値か「どれでも」）がちょうど一つある。
  答えが「起こらない（<名前>）」の行の名前は、制約か前提の名前である。
  列挙: 「列挙：<名前> = <値> | <値> | …」の行は計算の項目の中か状況の節にあり、名前は資料の中で一意、値は空でなく互いに異なる。
  決定表の列の名前が列挙の名前なら、その列の値は列挙の値か「どれでも」で、網羅はその列では列挙の値で数える。
  計算がその項目の名前の列挙を持つなら、決定表の答えは列挙の値か「起こらない（<名前>）」で、分かれ目の答えはその列挙の値で数える。
  式: 計算の項目で「式：」で始まる行は「<その項目の名前> = <式>」の形で、その項目に「単位：」と「丸め：」で始まる行がある。
  判定の前提: 制約の項目で「判定の前提：」で始まる行の、「、」で区切った各名前は制約か前提の名前で、判定の前提をたどって同じ制約へ戻らない。
  判断の表の網羅: 何をするとの欄は「<行い>」か「<行い>（<分かれ目>）」で、誰がと行いの組（行いの組）ごとに、状況の節のどの状況にも（状況を持たない資料はいつでもに）その行いの組の行がある。
  同じ状況と同じ行いの組の行が二つ以上あるか分かれ目を持つときは、どの行も分かれ目を持ち、分かれ目は「<計算の名前>が<答え>」を「、」で区切ったものである。
  その計算は決定表を持ち、答えはその決定表の「起こらない」でない答えの一つである。分かれ目に現れない計算を「どれでも」とみなし、決定表と同じく、答えの組み合わせのどれにもちょうど一つの行が当てはまる。
  拒む理由の示し方: どの決まりによるかに制約と前提の名前を二つ以上置くできない行があれば、行動・出来事と判断の節に「拒む理由の示し方：当たったすべて」か「拒む理由の示し方：欄の順で最初の一つ」の行がある。
  check-set では、さらに、制約、状況、計算の名前を二つの資料が定義していない（前提は持ち主の資料を指す項目なので照合しない）。
  前提の節にある相対リンクの先の資料が無いことは、未確認として報告し、合否に数えない。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。未確認は {"unverified", "detail"} で出し、最後に
  check は {"status", "subject", "problems"}、check-set は {"status", "documents", "problems", "unverified"} を一行出す。
  違反があれば終了code 1、未確認だけなら 0。引数の形が違うかファイルを読めなければ {"error"} と終了code 2。
正例: repository の scripts/fixtures/business-knowledge/ の資料の組（入室の前提が予約の資料を指す）。
反例: scripts/test-business-knowledge.sh の、節の欠け・順の入れ替え・余分な節・二つ目の表題、四つの節をまたぐ同じ名前、
  見出し行の違う表・二つ目の表・節の外の表、列数の違う行、無い状況、状況を持つ資料のいつでも、いつの欄の「—」、無い決まり、計算だけによるできない行、できない行の「—」、「、」を含む項目の名前、
  BDD の見出しの形・番号の重複・節の外の BDD・BDD の節の BDD でない見出し、制約でも前提でも状況でもない Rule、二つの資料が定義する同じ制約、
  決定表の網羅の欠け・重なる行・空の欄・制約でも前提でもない起こらない・計算の二つ目の決定表、左辺の違う式・単位や丸めの無い式、
  状況と行いの組の欠け・分かれ目の無い同じ組の行・計算の答えでない分かれ目・分かれ目の答えの組の欠けと重なり、示し方の無い複数の理由、無い名前や循環する判定の前提、
  列挙に無い条件の値・列挙に無い答え・列挙の値の書き忘れによる網羅の欠け・同じ名前の列挙・置き場の違う列挙。
意味評価として残す範囲: 列挙の値と、列挙を持たない決定表の条件の列の取りうる値が、入力のすべての場合を尽くしているか（列挙の無い列では書かれていない値は数えられない）、場合分けを文で書いた計算や制約が残っていないか、
  式が業務の言葉で正しいか、単位と丸めと境界が正しいか、分かれ目が自由文の行の網羅、判定の前提の置き方が正しいか、その事実がその節にあるべきか、表が状況と行いの組み合わせを網羅しているか、挙げた決まりがその判断を本当に支えるか、拒否の BDD に NOTE があるか、
  名前が業務の言葉か、英名の付け方、BDD が本文の判断を正しく例示するか、どの資料が決まりの持ち主であるべきか。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


SECTIONS = ["この業務の核", "前提", "制約", "状況", "計算", "行動・出来事と判断", "まだ決まっていないこと", "BDD"]
ITEM_SECTIONS = ["前提", "制約", "状況", "計算"]
TABLE_SECTION = "行動・出来事と判断"
TABLE_HEADERS = ["いつ", "誰が", "何をすると", "何が起きる", "どの決まりによるか"]
REFUSED = "できない。"
ALWAYS = "いつでも"
NO_RULE = "—"
ANSWER = "答え"
ANY = "どれでも"
NEVER = re.compile(r"^起こらない（(.+)）$")
ACTION = re.compile(r"^(.*?)（([^（）]*)）$")
DECLARE = "拒む理由の示し方："
DECLARE_VALUES = {"当たったすべて", "欄の順で最初の一つ"}
FORMULA = "式："
PREREQ = "判定の前提："
ENUM = re.compile(r"^列挙：\s*(.+?)\s*=\s*(.+?)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ENGLISH_SUFFIX = re.compile(r"（[^（）]*）$")
SEPARATOR = re.compile(r"^\|?(\s*:?-+:?\s*\|)*\s*:?-+:?\s*\|?$")
BDD_ANY = re.compile(r"^\[BDD-")
BDD = re.compile(r"^\[BDD-(\d{3,})\]\s+\S")
RULE = re.compile(r"^\s*NOTE:\s*Rule:\s*(.+?)\s*$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


@dataclass
class Problem:
    path: str
    detail: str
    howto: str

    def emit(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


@dataclass
class Document:
    path: Path
    items: dict[str, dict[str, int]] = field(default_factory=lambda: {name: {} for name in ITEM_SECTIONS})
    premise_lines: list[str] = field(default_factory=list)
    answers: dict[str, set[str]] = field(default_factory=dict)
    prereqs: dict[str, list[tuple[int, list[str]]]] = field(default_factory=dict)
    declarations: list[str] = field(default_factory=list)
    enums: dict[str, list[str]] = field(default_factory=dict)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def split_names(cell: str) -> list[str]:
    return [name.strip() for name in cell.split("、") if name.strip()]


def outside_fences(lines: list[str]) -> tuple[list[tuple[int, str]], list[tuple[str, list[str]]]]:
    """コードブロックの外の (行番号, 行) と、(言語, 中身の行) のブロックを返す。"""
    prose: list[tuple[int, str]] = []
    found: list[tuple[str, list[str]]] = []
    fence: list[str] | None = None
    language = ""
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith("```"):
                found.append((language, fence))
                fence = None
            else:
                fence.append(line)
            continue
        if stripped.startswith("```"):
            fence, language = [], stripped[3:].strip()
            continue
        prose.append((number, line))
    return prose, found


def check_document(path: Path, text: str, problems: list[Problem]) -> Document:
    label = str(path)
    document = Document(path)
    prose, found = outside_fences(text.splitlines())

    titles = [number for number, line in prose if (m := HEADING.match(line)) and len(m.group(1)) == 1]
    if len(titles) != 1:
        problems.append(Problem(f"{label}.title", f"`#` の見出しが{len(titles)}個ある", "`#` は資料の表題として一つだけ置く"))
    found_sections = [m.group(2) for _, line in prose if (m := HEADING.match(line)) and len(m.group(1)) == 2]
    if found_sections != SECTIONS:
        problems.append(Problem(f"{label}.sections", f"`##` の見出しが「{'、'.join(SECTIONS)}」の順の八つではない: {'、'.join(found_sections) or 'なし'}", "`##` を八つの名前でこの順に置き、中身が無い節も消さず無いことを一文で書く"))

    section = ""
    item_owner: dict[str, str] = {}
    item = ""
    tables: list[tuple[str, int, list[tuple[int, str]]]] = []
    item_tables: list[tuple[str, str, int, list[tuple[int, str]]]] = []
    table: list[tuple[int, str]] = []
    bdd_numbers: dict[str, int] = {}
    formulas: dict[str, list[tuple[int, str]]] = {}
    marks: dict[str, set[str]] = {}

    def close_table() -> None:
        if table:
            tables.append((section, table[0][0], list(table)))
            if section in ("制約", "計算") and item:
                item_tables.append((section, item, table[0][0], list(table)))
            table.clear()

    for number, line in prose:
        if line.lstrip().startswith("|"):
            table.append((number, line))
            continue
        close_table()
        match = HEADING.match(line)
        if not match:
            if section == "前提":
                document.premise_lines.append(line)
            stripped = line.strip()
            if section == TABLE_SECTION and stripped.startswith(DECLARE):
                document.declarations.append(stripped[len(DECLARE):].strip())
            if section == "計算" and item:
                for mark in (FORMULA, "単位：", "丸め："):
                    if stripped.startswith(mark):
                        marks.setdefault(item, set()).add(mark)
                if stripped.startswith(FORMULA):
                    formulas.setdefault(item, []).append((number, stripped[len(FORMULA):].strip()))
            enum = ENUM.match(stripped)
            if enum and stripped.startswith("列挙："):
                where = f"{label}.line[{number}]"
                values = [value.strip() for value in enum.group(2).split("|")]
                if not ((section == "計算" and item) or section == "状況"):
                    problems.append(Problem(where, "列挙が計算の項目の中にも状況の節にも無い", "列挙は、それを使う計算の項目の中か、状況の節に置く"))
                elif enum.group(1) in document.enums:
                    problems.append(Problem(where, f"同じ名前の列挙が二つある: {enum.group(1)}", "列挙の名前を資料の中で一意にする"))
                elif any(not value for value in values) or len(set(values)) != len(values):
                    problems.append(Problem(where, "列挙の値に空か重なりがある", "「列挙：<名前> = <値> | <値> | …」の値を空でなく、互いに異なるものにする"))
                else:
                    document.enums[enum.group(1)] = values
            if section == "制約" and item and stripped.startswith(PREREQ):
                document.prereqs.setdefault(item, []).append((number, split_names(stripped[len(PREREQ):])))
            continue
        level, title = len(match.group(1)), match.group(2)
        if level <= 2:
            section = title if level == 2 else ""
            item = ""
            continue
        if level != 3:
            continue
        if BDD_ANY.match(title) and section != "BDD":
            problems.append(Problem(f"{label}.line[{number}]", "BDD の見出しが BDD の節の外にある", "BDD は資料の最後の `## BDD` の下にだけ置く"))
        if section == "BDD":
            bdd = BDD.match(title)
            if not bdd:
                problems.append(Problem(f"{label}.line[{number}]", "BDD の節の見出しが「### [BDD-<3桁以上の数字>] <業務結果>」の形ではない", "番号を3桁以上の数字にし、閉じ括弧の後に業務結果を書く"))
            elif bdd.group(1) in bdd_numbers:
                problems.append(Problem(f"{label}.BDD-{bdd.group(1)}", f"BDD の番号が {bdd_numbers[bdd.group(1)]} 行目と重複している", "BDD の番号を資料の中で一意にする"))
            else:
                bdd_numbers[bdd.group(1)] = number
        if section in ITEM_SECTIONS:
            name = ENGLISH_SUFFIX.sub("", title).strip() if section == "状況" else title
            if "、" in name:
                problems.append(Problem(f"{label}.{section}.{name}", "項目の名前が「、」を含む", "「、」は表の欄の区切りに使うので、名前に含めない"))
            if name in item_owner:
                problems.append(Problem(f"{label}.{section}.{name}", f"同じ名前が{item_owner[name]}の節にもある", "前提、制約、状況、計算の項目の名前を、四つの節を通して一意にする"))
            else:
                item_owner[name] = section
                document.items[section][name] = number
            item = name
        if section == "前提":
            document.premise_lines.append(line)
    close_table()

    check_items(label, document, item_tables, formulas, marks, problems)
    check_table(label, document, tables, problems)
    rejecting = set(document.items["制約"]) | set(document.items["前提"]) | set(document.items["状況"])
    for language, body in found:
        if language != "gherkin":
            continue
        for line in body:
            rule = RULE.match(line)
            if rule and rule.group(1) not in rejecting:
                problems.append(Problem(f"{label}.Rule.{rule.group(1)}", "NOTE: Rule の名前が、制約にも前提にも状況にも無い", "拒否の BDD の Rule には、表のその行のどの決まりによるかにある制約、前提、状況の名前をそのまま書く"))
    return document


def coverage(columns: list[str], rows: list[tuple[int, dict[str, str]]], domains: dict[str, set[str]] | None = None) -> tuple[list[dict[str, str]], list[tuple[dict[str, str], list[int]]]]:
    """取りうる値の組み合わせのうち、当てはまる行が無いものと、二つ以上あるもの（と行番号）を返す。
    domains が無ければ、列ごとに行に現れた「どれでも」以外の値を取りうる値とする。"""
    if domains is None:
        domains = {column: {row[column] for _, row in rows if row.get(column, ANY) != ANY} for column in columns}
    combos: list[dict[str, str]] = [{}]
    for column in columns:
        if domains[column]:
            combos = [dict(combo, **{column: value}) for combo in combos for value in sorted(domains[column])]
    missing: list[dict[str, str]] = []
    overlapping: list[tuple[dict[str, str], list[int]]] = []
    for combo in combos:
        hits = [number for number, row in rows if all(row.get(column, ANY) in (ANY, value) for column, value in combo.items())]
        if not hits:
            missing.append(combo)
        elif len(hits) > 1:
            overlapping.append((combo, hits))
    return missing, overlapping


def show(combo: dict[str, str]) -> str:
    return "、".join(f"{column}={value}" for column, value in combo.items()) or "（条件なし）"


def check_items(label: str, document: Document, item_tables, formulas, marks, problems: list[Problem]) -> None:
    rejecting = set(document.items["制約"]) | set(document.items["前提"])
    seen: set[str] = set()
    for section, item, start, rows in item_tables:
        header = cells(rows[0][1])
        if header[-1] != ANSWER:
            continue
        where = f"{label}.{section}.{item}"
        if section == "計算" and item in seen:
            problems.append(Problem(where, "計算の一項目に決定表が二つある", "一つの計算の場合分けは一つの決定表にまとめる"))
            continue
        seen.add(item)
        body = rows[1:]
        if body and SEPARATOR.match(body[0][1].strip()):
            body = body[1:]
        columns = header[:-1]
        parsed: list[tuple[int, dict[str, str]]] = []
        answers: set[str] = set()
        answer_enum = document.enums.get(item) if section == "計算" else None
        for number, line in body:
            row = cells(line)
            if len(row) != len(header):
                problems.append(Problem(f"{label}.line[{number}]", "列数が決定表の見出しと一致しない", "各行を見出しと同じ列数にする"))
                continue
            if any(not cell for cell in row):
                problems.append(Problem(f"{label}.line[{number}]", "決定表に空の欄がある", f"どの値でもよい条件は「{ANY}」と書く"))
                continue
            for column, value in zip(columns, row[:-1]):
                if column in document.enums and value != ANY and value not in document.enums[column]:
                    problems.append(Problem(f"{label}.line[{number}]", f"列挙「{column}」に無い値: {value}", f"列の名前が列挙の名前なら、値は列挙の値か「{ANY}」にする"))
            never = NEVER.match(row[-1])
            if answer_enum is not None and not never and row[-1] not in answer_enum:
                problems.append(Problem(f"{label}.line[{number}]", f"列挙「{item}」に無い答え: {row[-1]}", "列挙を持つ計算の答えは、列挙の値か「起こらない（<名前>）」にする"))
            if never:
                for name in split_names(never.group(1)):
                    if name not in rejecting:
                        problems.append(Problem(f"{label}.line[{number}]", f"起こらないの名前が制約にも前提にも無い: {name}", "起こらない組み合わせは、それを起こさない制約か前提の名前で「起こらない（<名前>）」と書く"))
            else:
                answers.add(row[-1])
            parsed.append((number, dict(zip(columns, row[:-1]))))
        domains = {column: set(document.enums[column]) if column in document.enums else {row[column] for _, row in parsed if row.get(column, ANY) != ANY} for column in columns}
        missing, overlapping = coverage(columns, parsed, domains)
        for combo in missing:
            problems.append(Problem(where, f"決定表に当てはまる行が無い組み合わせ: {show(combo)}", f"その組み合わせの行を足す。起こりえないなら答えを「起こらない（<制約の名前>）」にした行を置く"))
        for combo, hits in overlapping:
            problems.append(Problem(where, f"決定表で二つ以上の行が当てはまる組み合わせ: {show(combo)}（{'、'.join(map(str, hits))}行目）", f"「{ANY}」を値に分け、どの組み合わせにも行がちょうど一つ当てはまるようにする"))
        if section == "計算":
            document.answers[item] = set(answer_enum) if answer_enum is not None else answers
    for item, lines in formulas.items():
        for number, formula in lines:
            left = formula.split("=", 1)[0].strip() if "=" in formula else None
            if left != item:
                problems.append(Problem(f"{label}.line[{number}]", "式が「<計算の名前> = <式>」の形ではない", "式の左辺を、その計算の見出しの名前にする"))
        for mark in ("単位：", "丸め："):
            if mark not in marks.get(item, set()):
                problems.append(Problem(f"{label}.計算.{item}", f"式を持つ計算に「{mark}」の行が無い", "式には、単位と丸めを一行ずつ添える。丸めないなら「丸め：丸めない」と書く"))
    graph: dict[str, list[str]] = {}
    for item, lines in document.prereqs.items():
        for number, names in lines:
            for name in names:
                if name not in rejecting:
                    problems.append(Problem(f"{label}.line[{number}]", f"判定の前提の名前が制約にも前提にも無い: {name}", "判定の前提には、満たされないとこの制約を判定できない制約か前提の名前を書く"))
                elif name in document.items["制約"]:
                    graph.setdefault(item, []).append(name)
    for start in graph:
        stack, visited = list(graph[start]), set()
        while stack:
            node = stack.pop()
            if node == start:
                problems.append(Problem(f"{label}.制約.{start}", "判定の前提をたどると同じ制約へ戻る", "判定の前提は、先に判定する制約へだけ向ける"))
                break
            if node not in visited:
                visited.add(node)
                stack.extend(graph.get(node, []))


def check_table(label: str, document: Document, tables: list[tuple[str, int, list[tuple[int, str]]]], problems: list[Problem]) -> None:
    situations = set(document.items["状況"])
    bases = set().union(*(document.items[section] for section in ITEM_SECTIONS))
    rejecting = set(document.items["前提"]) | set(document.items["制約"]) | situations
    decision_tables = 0
    groups: dict[tuple[str, str, str], list[tuple[int, str]]] = {}
    actions: dict[tuple[str, str], int] = {}
    multi_reason = 0
    for section, start, rows in tables:
        is_decision = cells(rows[0][1]) == TABLE_HEADERS
        if not is_decision:
            if section == TABLE_SECTION:
                problems.append(Problem(f"{label}.line[{start}]", f"{TABLE_SECTION}の節に、見出し行が『| {' | '.join(TABLE_HEADERS)} |』ではない表がある", "この節の表は、見出し行をこの五列にした一つだけにする"))
            continue
        decision_tables += 1
        if section != TABLE_SECTION:
            problems.append(Problem(f"{label}.line[{start}]", f"判断の表が{TABLE_SECTION}の節の外にある", f"判断の表は「## {TABLE_SECTION}」の下に置く"))
        if decision_tables > 1:
            problems.append(Problem(f"{label}.line[{start}]", "判断の表が二つ目である", "状況と行いの組み合わせは、一つの表に一行ずつ置く"))
        body = rows[1:]
        if body and SEPARATOR.match(body[0][1].strip()):
            body = body[1:]
        for number, line in body:
            row = cells(line)
            where = f"{label}.line[{number}]"
            if len(row) != len(TABLE_HEADERS):
                problems.append(Problem(where, "列数が判断の表の見出しと一致しない", "各行を、いつ、誰が、何をすると、何が起きる、どの決まりによるかの五列にする"))
                continue
            situation, who, doing, happens, basis = row
            refused = happens.startswith(REFUSED)
            action = ACTION.match(doing)
            verb, branch = (action.group(1).strip(), action.group(2).strip()) if action else (doing, "")
            actions.setdefault((who, verb), number)
            for name in (split_names(situation) or [situation]):
                groups.setdefault((name, who, verb), []).append((number, branch))
            if refused and basis != NO_RULE and sum(name in (set(document.items["前提"]) | set(document.items["制約"])) for name in split_names(basis)) >= 2:
                multi_reason = number
            if situation == ALWAYS:
                if situations:
                    problems.append(Problem(where, f"状況を持つ資料のいつの欄が「{ALWAYS}」である", "いつの欄には状況の名前を書く。対象がまだ無い在り方も状況の名前にする"))
            else:
                for name in split_names(situation) or [situation]:
                    if name not in situations:
                        problems.append(Problem(where, f"いつの欄の名前が状況の節に無い: {name}", f"状況の節の名前を「、」で区切って書くか、状況を持たない業務では「{ALWAYS}」にする"))
            if basis == NO_RULE:
                if refused:
                    problems.append(Problem(where, f"できない行のどの決まりによるかが「{NO_RULE}」である", "できない行には、拒む決まりになる制約、前提、状況の名前を一つ以上置く"))
                continue
            names = split_names(basis)
            for name in names:
                if name not in bases:
                    problems.append(Problem(where, f"どの決まりによるかの名前が前提、制約、状況、計算のどれにも無い: {name}", f"前提、制約、状況、計算の項目の名前を「、」で区切って書く。できない行でなく頼る決まりが無ければ「{NO_RULE}」にする"))
            if refused and not any(name in rejecting for name in names):
                problems.append(Problem(where, "できない行のどの決まりによるかに、制約、前提、状況の名前が無い", "できない行には、拒む決まりになる制約、前提、状況の名前を一つ以上置く"))
    check_cover(label, document, groups, actions, problems)
    if multi_reason and not any(value in DECLARE_VALUES for value in document.declarations):
        problems.append(Problem(f"{label}.line[{multi_reason}]", "制約と前提を二つ以上置くできない行があるのに、拒む理由の示し方が無い", f"表の前に「{DECLARE}当たったすべて」か「{DECLARE}欄の順で最初の一つ」の行を置く"))


def check_cover(label: str, document: Document, groups, actions, problems: list[Problem]) -> None:
    situations = list(document.items["状況"]) or [ALWAYS]
    for (who, verb), number in actions.items():
        for situation in situations:
            if (situation, who, verb) not in groups:
                problems.append(Problem(f"{label}.line[{number}]", f"判断の表に無い組み合わせ: {situation} × {who}が{verb}", "その状況でその行いをしたときの行を足す。受けないなら、できない行にして状況の名前を根拠に置く"))
    calcs = sorted(document.answers, key=len, reverse=True)
    for (situation, who, verb), rows in groups.items():
        if len(rows) == 1 and not rows[0][1]:
            continue
        where = f"{label}.line[{rows[0][0]}]"
        parsed: list[tuple[int, dict[str, str]]] = []
        columns: list[str] = []
        for number, branch in rows:
            if not branch:
                problems.append(Problem(f"{label}.line[{number}]", f"{situation} × {who}が{verb}の行が二つ以上あるのに、分かれ目が無い", "何をするとを「<行い>（<計算の名前>が<答え>）」にして、行を分けるものを書く"))
                parsed = []
                break
            conditions: dict[str, str] = {}
            for condition in split_names(branch):
                calc = next((name for name in calcs if condition.startswith(name + "が")), None)
                if calc is None or condition[len(calc) + 1:] not in document.answers[calc]:
                    problems.append(Problem(f"{label}.line[{number}]", f"分かれ目が、決定表を持つ計算の答えの形ではない: {condition}", "分かれ目は「<計算の名前>が<答え>」にし、その計算の決定表に答えを置く"))
                    parsed = []
                    break
                conditions[calc] = condition[len(calc) + 1:]
                if calc not in columns:
                    columns.append(calc)
            else:
                parsed.append((number, conditions))
                continue
            break
        if not parsed:
            continue
        domains = {calc: document.answers[calc] for calc in columns}
        # 取りうる値は、分かれ目に現れた値ではなく、計算の決定表の答えのすべてにする
        missing, overlapping = coverage(columns, parsed, domains)
        for combo in missing:
            problems.append(Problem(where, f"{situation} × {who}が{verb}で、当てはまる行が無い分かれ目: {show(combo)}", "その答えの行を足す"))
        for combo, hits in overlapping:
            problems.append(Problem(where, f"{situation} × {who}が{verb}で、二つ以上の行が当てはまる分かれ目: {show(combo)}（{'、'.join(map(str, hits))}行目）", "分かれ目を分け、どの答えの組にも行がちょうど一つ当てはまるようにする"))



def premise_links(document: Document) -> list[Path]:
    targets: list[Path] = []
    for line in document.premise_lines:
        for target in LINK.findall(line):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            targets.append((document.path.parent / target.split("#", 1)[0]).resolve())
    return targets


def read_all(paths: list[Path]) -> dict[Path, str] | None:
    texts: dict[Path, str] = {}
    for path in paths:
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except OSError as error:
            print(json.dumps({"error": f"読めない: {path}: {error}"}, ensure_ascii=False))
            return None
    return texts


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in {"check", "check-set"} or len(sys.argv) < 3 or (command == "check" and len(sys.argv) != 3):
        print(json.dumps({"error": "usage: business_knowledge.py check <保存した資料のパス> | check-set <照合する業務知識のパス>..."}, ensure_ascii=False))
        return 2
    paths = [Path(arg).resolve() for arg in sys.argv[2:]]
    texts = read_all(paths)
    if texts is None:
        return 2
    problems: list[Problem] = []
    documents = [check_document(path, texts[path], problems) for path in paths]
    unverified: list[dict] = []
    if command == "check-set":
        for index, document in enumerate(documents):
            defined = {name: section for section in ("制約", "状況", "計算") for name in document.items[section]}
            for earlier in documents[:index]:
                for section in ("制約", "状況", "計算"):
                    for name in earlier.items[section]:
                        if name in defined:
                            problems.append(Problem(f"{document.path}.{defined[name]}.{name}", f"同じ名前を{earlier.path}も{section}として定義している", "決まりと名前は持ち主の資料一か所だけで定義し、ほかの資料は前提として名前と持ち主へのリンクで指す"))
            for target in premise_links(document):
                if not target.exists():
                    unverified.append({"unverified": str(target), "detail": f"{document.path} の前提が指す資料がまだ無い"})
    for problem in problems:
        print(problem.emit())
    for item in unverified:
        print(json.dumps(item, ensure_ascii=False))
    status = "ng" if problems else "ok"
    if command == "check":
        print(json.dumps({"status": status, "subject": str(paths[0]), "problems": len(problems)}, ensure_ascii=False))
    else:
        print(json.dumps({"status": status, "documents": len(paths), "problems": len(problems), "unverified": len(unverified)}, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
