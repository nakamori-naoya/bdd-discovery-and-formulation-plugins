#!/usr/bin/env python3
"""業務知識の資料（business-knowledge）が、目印の形に合うかを検査する。

基準資料: write-doc の business-knowledge 型の「検査が読む目印」と、この入口の references/ubiquitous-language.md の
  「一つの語は、業務をまたいでも一か所で決める」。見出しの文言は読まない。
入力: 引数に並べた資料のパス。最初の一本が判定する資料（保存した資料）で、残りは隣の業務知識として重複の照合に読むだけである。
  持ち主の欄のリンクは、判定する資料のディレクトリから解決して読む。
合格述語:
  ユビキタス言語の表（見出し行が「業務の言葉 | 英名 | 種類 | 持ち主」）がコードブロックの外に一つだけある。
  各行の種類は 業務用語・業務イベント・概念・コマンド・クエリ のどれかで、業務の言葉と英名は空でなく、一つの言葉は一行だけにある。
  持ち主の欄は「この資料」か相対 Markdown リンクで、リンク先の資料があれば、その表に同じ言葉が「この資料」の行として
  同じ英名・同じ種類で載っている。リンク先の資料が無いことは未確認として報告し、合否に数えない。
  判定する資料が「この資料」として決めた言葉を、隣の資料も「この資料」として決めていない。判定する資料の英名が、隣の資料で違う言葉に付いていない。
  隣の資料そのものの形の違反は判定しない。
  1行目が --- の Mermaid ブロックと stateDiagram-v2 を含む Mermaid ブロックは、先頭が ---、title: <名前>、---、stateDiagram-v2 の四行である。
  BDD の見出しは「### [BDD-<3桁以上の数字>] <本文>」の形で、番号は資料の中で一意である。
  「#### 拒む理由: <名前>」の名前は資料の中で一意で、gherkin ブロックの「Rule: <名前>」はそのどれかと一致する。
失敗時の診断: {"path", "detail", "howto"} のJSONを1行ずつ標準出力へ。未確認は {"unverified", "detail"} で出し、最後に
  {"status", "subject", "problems", "unverified"} を一行出す。違反があれば終了code 1、未確認だけなら 0。引数が無いかファイルを読めなければ {"error"} と終了code 2。
正例: repository の scripts/fixtures/business-knowledge/ の資料の組。
反例: scripts/test-business-knowledge.sh の、種類の許可値の外、同じ言葉の二行、持ち主の英名の食い違い、持ち主の資料に無い言葉、
  隣の資料と同じ言葉を決める、同じ英名が違う言葉に付く、状態遷移図の先頭の欠け、BDD 番号の重複、宣言に無い Rule。
意味評価として残す範囲: 語が業務の人の言葉か、状態名や業務イベントの名前が作った語でないか、どの資料が語の持ち主であるべきか、
  値が業務の判断を変えるか、決まりと BDD の業務上の正しさ。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


HEADERS = ["業務の言葉", "英名", "種類", "持ち主"]
KINDS = {"業務用語", "業務イベント", "概念", "コマンド", "クエリ"}
OWN = "この資料"
LINK = re.compile(r"^\[[^\]]*\]\(([^)\s]+)\)$")
BDD_ANY = re.compile(r"^###\s+\[BDD-")
BDD = re.compile(r"^###\s+\[BDD-(\d{3,})\]\s+\S")
REASON = re.compile(r"^####\s+拒む理由:\s*(.+?)\s*$")
RULE = re.compile(r"^\s*NOTE:\s*Rule:\s*(.+?)\s*$|^\s*Rule:\s*(.+?)\s*$")


@dataclass
class Problem:
    path: str
    detail: str
    howto: str

    def emit(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def blocks(lines: list[str]) -> tuple[list[tuple[int, str]], list[tuple[str, list[str]]]]:
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
                fence.append(line)
            continue
        if stripped.startswith("```"):
            fence, language = [], stripped[3:].strip()
            continue
        prose.append((number, line))
    return prose, found


@dataclass
class Term:
    word: str
    english: str
    kind: str
    owner: str
    line: int


def read_terms(label: str, prose: list[tuple[int, str]], problems: list[Problem]) -> list[Term]:
    starts = [i for i, (_, line) in enumerate(prose) if line.lstrip().startswith("|") and cells(line) == HEADERS]
    if len(starts) != 1:
        problems.append(Problem(f"{label}.ubiquitous_language", f"見出し行が『| {' | '.join(HEADERS)} |』の表が{len(starts)}個ある", "ユビキタス言語の表を資料に一つだけ置く"))
        return []
    terms: list[Term] = []
    for number, line in prose[starts[0] + 2:]:
        if not line.lstrip().startswith("|"):
            break
        row = cells(line)
        if len(row) != len(HEADERS):
            problems.append(Problem(f"{label}.line[{number + 1}]", "列数がユビキタス言語の表の見出しと一致しない", "各行を4列にする"))
            continue
        word, english, kind, owner = row
        if not word or not english:
            problems.append(Problem(f"{label}.line[{number + 1}]", "業務の言葉か英名が空である", "業務の言葉ごとに英名を一つ書く"))
            continue
        if kind not in KINDS:
            problems.append(Problem(f"{label}.{word}.種類", f"許可値ではない: {kind}", "業務用語・業務イベント・概念・コマンド・クエリのどれか一つにする"))
        if owner != OWN and not LINK.match(owner):
            problems.append(Problem(f"{label}.{word}.持ち主", f"「{OWN}」でも相対 Markdown リンクでもない: {owner}", f"この資料で決めた語は「{OWN}」、ほかの資料の語は持ち主の資料へのリンクにする"))
        terms.append(Term(word, english, kind, owner, number + 1))
    seen: set[str] = set()
    for term in terms:
        if term.word in seen:
            problems.append(Problem(f"{label}.{term.word}", "同じ業務の言葉が表に二行ある", "一つの言葉は一行だけに置き、種類を一つに決める"))
        seen.add(term.word)
    return terms


def check_state_diagrams(label: str, found: list[tuple[str, list[str]]], problems: list[Problem]) -> None:
    for index, (language, body) in enumerate(found):
        if language != "mermaid":
            continue
        content = [line.strip() for line in body if line.strip()]
        if not content:
            continue
        if content[0] != "---" and "stateDiagram-v2" not in content:
            continue
        head = content[:4]
        ok = len(head) == 4 and head[0] == "---" and re.fullmatch(r"title:\s*\S.*", head[1]) and head[2] == "---" and head[3] == "stateDiagram-v2"
        if not ok:
            problems.append(Problem(f"{label}.mermaid[{index}]", "状態遷移図の先頭が ---、title: <名前>、---、stateDiagram-v2 の四行ではない", "状態を持つものごとに、この四行で始まるブロックを一つ置く"))


def check_bdd_and_reasons(label: str, prose: list[tuple[int, str]], found: list[tuple[str, list[str]]], problems: list[Problem]) -> None:
    numbers: dict[str, int] = {}
    for number, line in prose:
        if not BDD_ANY.match(line):
            continue
        match = BDD.match(line)
        if not match:
            problems.append(Problem(f"{label}.line[{number + 1}]", "BDD の見出しが「### [BDD-<3桁以上の数字>] <本文>」の形ではない", "番号を3桁以上の数字にし、閉じ括弧の後に業務結果を書く"))
            continue
        if match.group(1) in numbers:
            problems.append(Problem(f"{label}.BDD-{match.group(1)}", f"BDD の番号が {numbers[match.group(1)]} 行目と重複している", "BDD の番号を資料の中で一意にする"))
        numbers.setdefault(match.group(1), number + 1)
    reasons: set[str] = set()
    for number, line in prose:
        match = REASON.match(line)
        if not match:
            continue
        if match.group(1) in reasons:
            problems.append(Problem(f"{label}.拒む理由.{match.group(1)}", "同じ名前の拒む理由が二つある", "拒む理由の名前を資料の中で一意にする"))
        reasons.add(match.group(1))
    for language, body in found:
        if language != "gherkin":
            continue
        for line in body:
            match = RULE.match(line)
            if not match:
                continue
            name = match.group(1) or match.group(2)
            if name not in reasons:
                problems.append(Problem(f"{label}.Rule.{name}", "BDD の Rule が「#### 拒む理由: <名前>」のどれとも一致しない", "Rule には、業務の行いの節で宣言した拒む理由の名前をそのまま書く"))


def load(path: Path, cache: dict[Path, list[Term] | None]) -> list[Term] | None:
    if path not in cache:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            cache[path] = None
            return None
        prose, _ = blocks(text.splitlines())
        cache[path] = read_terms(str(path), prose, [])
    return cache[path]


def check_owners(path: Path, terms: list[Term], cache: dict[Path, list[Term] | None], problems: list[Problem], unverified: list[dict]) -> None:
    for term in terms:
        match = LINK.match(term.owner)
        if not match:
            continue
        target = (path.parent / match.group(1)).resolve()
        owner_terms = load(target, cache)
        if owner_terms is None:
            unverified.append({"unverified": str(target), "detail": f"持ち主の資料がまだ無いので、「{term.word}」の英名と種類を照合していない"})
            continue
        owned = [t for t in owner_terms if t.word == term.word and t.owner == OWN]
        if not owned:
            problems.append(Problem(f"{path}.{term.word}.持ち主", f"持ち主の資料がこの言葉を「{OWN}」として決めていない: {target}", "持ち主を、その語を決めた資料に直すか、持ち主の資料への変更案として返す"))
            continue
        if owned[0].english != term.english or owned[0].kind != term.kind:
            problems.append(Problem(f"{path}.{term.word}", f"持ち主の資料と英名か種類が違う: 持ち主は {owned[0].english}（{owned[0].kind}）", "持ち主の資料と同じ英名と種類を使う。持ち主を変えたいなら変更案として返す"))


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "check":
        print(json.dumps({"error": "usage: business_knowledge.py check <保存した資料のパス> [<隣の業務知識のパス>...]"}, ensure_ascii=False))
        return 2
    paths = [Path(arg).resolve() for arg in sys.argv[2:]]
    texts: dict[Path, str] = {}
    for path in paths:
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except OSError as error:
            print(json.dumps({"error": f"読めない: {path}: {error}"}, ensure_ascii=False))
            return 2
    subject = paths[0]
    label = str(subject)
    problems: list[Problem] = []
    unverified: list[dict] = []
    cache: dict[Path, list[Term] | None] = {}
    prose, found = blocks(texts[subject].splitlines())
    terms = read_terms(label, prose, problems)
    cache[subject] = terms
    check_state_diagrams(label, found, problems)
    check_bdd_and_reasons(label, prose, found, problems)
    for path in paths[1:]:
        if path == subject:
            continue
        others = load(path, cache) or []
        for term in terms:
            for other in others:
                if term.owner == OWN and other.owner == OWN and term.word == other.word:
                    problems.append(Problem(f"{label}.{term.word}", f"同じ言葉を隣の資料も決めている: {path}", "言葉は、それが指すものを作り、変える業務の資料一本だけで決める。分け方の一覧で自分が持ち主なら相手への変更案として返し、そうでなければ持ち主へのリンクの行にする"))
                if term.english == other.english and term.word != other.word:
                    problems.append(Problem(f"{label}.{term.word}", f"英名 {term.english} が隣の資料で別の言葉「{other.word}」に付いている: {path}", "一つの英名は一つの言葉にだけ付ける"))
    check_owners(subject, terms, cache, problems, unverified)
    for problem in problems:
        print(problem.emit())
    for item in unverified:
        print(json.dumps(item, ensure_ascii=False))
    print(json.dumps({"status": "ng" if problems else "ok", "subject": label, "problems": len(problems), "unverified": len(unverified)}, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
