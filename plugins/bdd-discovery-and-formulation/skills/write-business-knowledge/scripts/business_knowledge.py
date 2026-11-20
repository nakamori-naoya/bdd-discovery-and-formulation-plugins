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
  check-set では、さらに、制約、状況、計算の名前を二つの資料が定義していない（前提は持ち主の資料を指す項目なので照合しない）。
  前提の節にある相対リンクの先の資料が無いことは、未確認として報告し、合否に数えない。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。未確認は {"unverified", "detail"} で出し、最後に
  check は {"status", "subject", "problems"}、check-set は {"status", "documents", "problems", "unverified"} を一行出す。
  違反があれば終了code 1、未確認だけなら 0。引数の形が違うかファイルを読めなければ {"error"} と終了code 2。
正例: repository の scripts/fixtures/business-knowledge/ の資料の組（入室の前提が予約の資料を指す）。
反例: scripts/test-business-knowledge.sh の、節の欠け・順の入れ替え・余分な節・二つ目の表題、四つの節をまたぐ同じ名前、
  見出し行の違う表・二つ目の表・節の外の表、列数の違う行、無い状況、状況を持つ資料のいつでも、いつの欄の「—」、無い決まり、計算だけによるできない行、できない行の「—」、「、」を含む項目の名前、
  BDD の見出しの形・番号の重複・節の外の BDD・BDD の節の BDD でない見出し、制約でも前提でも状況でもない Rule、二つの資料が定義する同じ制約。
意味評価として残す範囲: その事実がその節にあるべきか、表が状況と行いの組み合わせを網羅しているか、挙げた決まりがその判断を本当に支えるか、拒否の BDD に NOTE があるか、
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
    tables: list[tuple[str, int, list[tuple[int, str]]]] = []
    table: list[tuple[int, str]] = []
    bdd_numbers: dict[str, int] = {}

    def close_table() -> None:
        if table:
            tables.append((section, table[0][0], list(table)))
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
            continue
        level, title = len(match.group(1)), match.group(2)
        if level <= 2:
            section = title if level == 2 else ""
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
        if section == "前提":
            document.premise_lines.append(line)
    close_table()

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


def check_table(label: str, document: Document, tables: list[tuple[str, int, list[tuple[int, str]]]], problems: list[Problem]) -> None:
    situations = set(document.items["状況"])
    bases = set().union(*(document.items[section] for section in ITEM_SECTIONS))
    rejecting = set(document.items["前提"]) | set(document.items["制約"]) | situations
    decision_tables = 0
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
            situation, _, _, happens, basis = row
            refused = happens.startswith(REFUSED)
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
