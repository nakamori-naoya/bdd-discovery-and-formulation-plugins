#!/usr/bin/env python3
"""Gherkin形式のBDD草案を機械で検査する。

**読みやすさは自動化のしやすさより優先する。** ここで見るのは、
その読みやすさを機械で守れる部分だけである。意図が伝わるかは人の判断に残る。

  scenario.py check --matrix-json '<条件マトリクスJSON>'   < <Gherkin本文>
      -> 違反をstdoutへJSON 1行ずつ出す。exit 0 = 違反なし / 1 = 違反あり（line, kind, detail, howto） / 2 = 入力を読めない
  scenario.py self-test

BDD草案（Gherkin本文）はそのまま標準入力で、条件マトリクスは --matrix-json 引数のJSON文字列で受ける。fileは介さない。
標準入力が空、--matrix-json がJSONでない、objectでない場合は exit 2。
Backgroundは使わない（共通の前提が重複しても各シナリオへ書くほうが読みやすい）。
"""

import argparse
import json
import re
import subprocess
import sys

from scenario_matrix import validate as validate_matrix

FEATURE = re.compile(r"^\s*(Feature|機能)\s*:\s*(.*)$")
RULE = re.compile(r"^\s*(Rule|ルール)\s*:\s*(.*)$")
BACKGROUND = re.compile(r"^\s*(Background|背景)\s*:")
SCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario Template|シナリオテンプレート|シナリオアウトライン|Scenario|シナリオ)\s*:\s*(.*)$")
EXAMPLES = re.compile(r"^\s*(Examples|Scenarios|例)\s*:")
STEP = re.compile(r"^\s*(Given|When|Then|And|But|前提|もし|ならば|かつ|しかし)\s+(.*)$")
KEYWORD_KIND = {"Given": "given", "前提": "given", "When": "when", "もし": "when",
                "Then": "then", "ならば": "then"}
PLACEHOLDER = re.compile(r"<([^<>]+)>")
OLD_CLOSURE = re.compile(r"^\s*#\s*クロージャ\s*:")
NOTE = re.compile(r"^\s*NOTE\s*:\s*$")
NOTE_FIELD = re.compile(r"^\s+(Rule|Source|Reason)\s*:\s*(.+?)\s*$")


def fail(msg, code=2):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)



def read_inputs(matrix_json):
    """標準入力のGherkin本文と --matrix-json の条件マトリクスを読む。読めなければ exit 2。"""
    draft = sys.stdin.read()
    if not draft.strip():
        fail("標準入力が空。BDD草案（Gherkin本文）を標準入力で渡す")
    try:
        matrix = json.loads(matrix_json)
    except json.JSONDecodeError as e:
        fail("--matrix-json がJSONではない: {}".format(e))
    if not isinstance(matrix, dict):
        fail("--matrix-json は条件マトリクスobjectでなければならない")
    return draft, matrix


def parse(text):
    """必要な構造だけを取る。網羅的なパーサではない。"""
    doc = {"features": [], "backgrounds": [], "scenarios": [], "old_closures": []}
    cur = None
    in_examples = False
    in_note = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        if OLD_CLOSURE.match(line):
            doc["old_closures"].append({"line": i})
            continue
        if NOTE.match(line):
            if cur is not None:
                cur["notes"].append({"line": i, "fields": {}})
                in_note = True
            continue
        note_field = NOTE_FIELD.match(line)
        if note_field and cur is not None and in_note and cur["notes"]:
            cur["notes"][-1]["fields"][note_field.group(1).lower()] = {
                "line": i, "text": note_field.group(2).strip()
            }
            continue
        if s.startswith("#"):
            continue
        m = FEATURE.match(line)
        if m:
            doc["features"].append({"line": i, "name": m.group(2).strip()})
            cur, in_examples, in_note = None, False, False
            continue
        if BACKGROUND.match(line):
            doc["backgrounds"].append({"line": i})
            cur, in_examples, in_note = None, False, False
            continue
        if RULE.match(line):
            cur, in_examples, in_note = None, False, False
            continue
        m = SCENARIO.match(line)
        if m:
            cur = {"line": i, "keyword": m.group(1), "name": m.group(2).strip(),
                   "outline": "Outline" in m.group(1) or "Template" in m.group(1)
                              or "テンプレート" in m.group(1) or "アウトライン" in m.group(1),
                   "steps": [], "examples": [], "notes": []}
            doc["scenarios"].append(cur)
            in_examples, in_note = False, False
            continue
        if EXAMPLES.match(line):
            in_examples = bool(cur)
            in_note = False
            continue
        if s.startswith("|") and in_examples and cur is not None:
            cells = [c.strip() for c in s.strip("|").split("|")]
            cur["examples"].append({"line": i, "cells": cells})
            continue
        m = STEP.match(line)
        if m and cur is not None:
            in_note = False
            kw, body = m.group(1), m.group(2).strip()
            kind = KEYWORD_KIND.get(kw)
            if kind is None:  # And / But / かつ / しかし は直前を継ぐ
                kind = cur["steps"][-1]["kind"] if cur["steps"] else "given"
            cur["steps"].append({"line": i, "keyword": kw, "kind": kind, "text": body})
    return doc


def check(doc, allow_background, matrix):
    problems = []

    def bad(line, kind, detail, howto):
        problems.append({"line": line, "kind": kind, "detail": detail, "howto": howto})

    if len(doc["features"]) != 1:
        bad(doc["features"][0]["line"] if doc["features"] else 0, "機能の数",
            "1つのファイルに機能が {} 個".format(len(doc["features"])),
            "1ファイル1機能にする")
    if doc["backgrounds"] and not allow_background:
        bad(doc["backgrounds"][0]["line"], "背景",
            "背景を使っている",
            "共通の前提が重複しても、各シナリオへ書くほうが読みやすい")
    if not doc["scenarios"]:
        bad(0, "シナリオ", "シナリオが1つも無い", "具体例を1つずつシナリオにする")
    for closure in doc["old_closures"]:
        bad(closure["line"], "クロージャ宣言", "廃止されたクロージャ宣言がある",
            "必要条件をGivenへ明示し、条件マトリクスで検査する")

    matrix_by_name = {item["name"]: item for item in matrix.get("scenarios", []) if isinstance(item, dict) and isinstance(item.get("name"), str)}
    document_names = {item["name"] for item in doc["scenarios"] if item["name"]}
    for missing in sorted(document_names - set(matrix_by_name)):
        bad(0, "条件マトリクス", "BDDに対応する条件マトリクスが無い: {}".format(missing), "同じシナリオ名で条件マトリクスを書く")
    for extra in sorted(set(matrix_by_name) - document_names):
        bad(0, "条件マトリクス", "BDD本文に無いシナリオがある: {}".format(extra), "BDD本文と条件マトリクスを一対一にする")

    seen_names = {}
    for sc in doc["scenarios"]:
        name, ln = sc["name"], sc["line"]
        if not name:
            bad(ln, "シナリオ名", "名前が無い", "何の話かが1行で分かる名前を付ける")
        if name:
            if name in seen_names:
                bad(ln, "シナリオ名", "同じ名前が {} 行目にもある".format(seen_names[name]),
                    "どこが違うのかを名前に出す")
            seen_names[name] = ln

        givens = [s for s in sc["steps"] if s["kind"] == "given"]
        whens = [s for s in sc["steps"] if s["kind"] == "when"]
        thens = [s for s in sc["steps"] if s["kind"] == "then"]
        if not givens:
            bad(ln, "Given", "前提が無い", "結果に必要な業務条件をすべてGivenへ書く")
        if len(whens) != 1:
            bad(ln, "行いの数", "1つのシナリオに行いが {} 個".format(len(whens)),
                "行いは1つ。増えるなら片方は前提か、まとめ方が足りない")
        if not thens:
            bad(ln, "Then", "結果が無い", "業務上の結果をThenへ書く")
        kinds = [s["kind"] for s in sc["steps"]]
        order = {"given": 0, "when": 1, "then": 2}
        if kinds != sorted(kinds, key=order.get):
            bad(ln, "ステップの順序", "Given / When / Then の順になっていない",
                "すでにある前提、検証する唯一の入力、観測可能な結果の順に並べる")
        matrix_item = matrix_by_name.get(name)
        if matrix_item:
            premise_texts = {item.get("text") for item in matrix_item.get("premises", []) if isinstance(item, dict)}
            given_texts = {item["text"] for item in givens}
            if premise_texts != given_texts:
                bad(ln, "Givenと条件マトリクス", "必要条件とGivenが一致しない",
                    "条件マトリクスの全premisesをGivenへ一件ずつ写し、余分なGivenも無くす")
            trigger_text = (matrix_item.get("trigger") or {}).get("text")
            if len(whens) == 1 and whens[0]["text"] != trigger_text:
                bad(whens[0]["line"], "Whenと条件マトリクス", "トリガー本文が一致しない",
                    "actionまたはeventとして確定した一つのトリガーをWhenへ写す")
            expected_failure = matrix_item.get("expected") == "failure"
            notes = sc["notes"]
            if expected_failure and len(notes) != 1:
                bad(ln, "NOTE", "失敗シナリオのNOTEが {} 個".format(len(notes)),
                    "全Thenの直後にRule、必要ならSource、Reasonを持つNOTEを一つ置く")
            elif not expected_failure and notes:
                bad(notes[0]["line"], "NOTE", "成功シナリオにNOTEがある", "成功シナリオからNOTEを削る")
            elif expected_failure and notes:
                note = notes[0]
                fields = {key: value["text"] for key, value in note["fields"].items()}
                expected_note = matrix_item.get("note") or {}
                for field in ("rule", "reason"):
                    if fields.get(field) != expected_note.get(field):
                        bad(note["line"], "NOTE", "{}が条件マトリクスと一致しない".format(field),
                            "条件マトリクスで確定した失敗理由を写す")
                if fields.get("source") != expected_note.get("source"):
                    bad(note["line"], "NOTE", "sourceが条件マトリクスと一致しない",
                        "外部正式な定義なら相対Markdownリンクを写し、同じ資料ならSourceを省略する")
                content_lines = [s["line"] for s in sc["steps"]] + [e["line"] for e in sc["examples"]]
                if content_lines and note["line"] <= max(content_lines):
                    bad(note["line"], "NOTE", "Thenの途中にある", "すべてのThenとAndの直後へ移す")

        norm = {}
        for st in sc["steps"]:
            t, sl = st["text"], st["line"]
            if st["kind"] == "given":
                key = re.sub(r"\s+", "", t)
                if key in norm:
                    bad(sl, "前提の重複", "{} 行目と同じ前提".format(norm[key]),
                        "同じ前提を2回置かない")
                norm[key] = sl
        for g in givens:
            for w in whens:
                if re.sub(r"\s+", "", g["text"]) == re.sub(r"\s+", "", w["text"]):
                    bad(w["line"], "前提と行いが同じ", g["text"],
                        "すでに済んでいることか、いま行うことか、どちらかに決める")

        used = {p for st in sc["steps"] for p in PLACEHOLDER.findall(st["text"])}
        if sc["outline"]:
            if not sc["examples"]:
                bad(ln, "例の表", "テンプレートなのに表が無い", "表を付けるか、通常のシナリオにする")
            else:
                header = sc["examples"][0]["cells"]
                rows = sc["examples"][1:]
                for h in header:
                    if h and h not in used:
                        bad(sc["examples"][0]["line"], "使われていない列", h,
                            "使わない列は消す")
                for u in used:
                    if u not in header:
                        bad(ln, "表に無い差し込み", u, "列を足すか、差し込みをやめる")
                seen_rows = {}
                for r in rows:
                    key = tuple(r["cells"])
                    if key in seen_rows:
                        bad(r["line"], "同じ行", "{} 行目と同じ".format(seen_rows[key]),
                            "本質的に同じ振る舞いを示す行は1つでよい")
                    seen_rows[key] = r["line"]
        elif used:
            bad(ln, "差し込み", "通常のシナリオに <{}> がある".format("> <".join(sorted(used))),
                "テンプレートにするか、実際の値を書く")
    return problems



def check_matrix(matrix):
    matrix_problems = validate_matrix(matrix)
    if matrix_problems:
        for item in matrix_problems:
            print(json.dumps(item, ensure_ascii=False))
        fail("条件マトリクスに {} 件の違反".format(len(matrix_problems)), 1)


def cmd_check(args):
    draft, matrix = read_inputs(args.matrix_json)
    doc = parse(draft)
    check_matrix(matrix)
    problems = check(doc, False, matrix)
    for p in problems:
        print(json.dumps(p, ensure_ascii=False))
    if problems:
        print(json.dumps({"error": "{} 件の違反".format(len(problems))}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps({"check": "clean", "scenarios": len(doc["scenarios"])}, ensure_ascii=False))


def self_test():
    draft = (
        "Feature: 予約\n"
        "Scenario: 停止中の予約者は成立しない\n"
        "  Given 予約者が候補を選べる\n"
        "  And 予約者は仮押さえ停止中である\n"
        "  When 予約者が候補を選ぶ\n"
        "  Then 予約は成立しない\n"
        "  NOTE:\n"
        "    Rule: 予約成立規則\n"
        "    Reason: 停止中顧客は新しい利用枠を確保できないため\n"
    )
    matrix = {"scenarios": [{
        "name": "停止中の予約者は成立しない", "kind": "single_failure", "expected": "failure", "rule": "予約成立規則",
        "trigger": {"kind": "action", "text": "予約者が候補を選ぶ"},
        "premises": [
            {"text": "予約者が候補を選べる", "state": "satisfied", "target": False, "source": "予約資料"},
            {"text": "予約者は仮押さえ停止中である", "state": "unsatisfied", "target": True, "source": "予約成立規則"},
        ],
        "note": {"rule": "予約成立規則", "reason": "停止中顧客は新しい利用枠を確保できないため"},
    }]}
    assert check(parse(draft), False, matrix) == [], "正例: GherkinとマトリクスがGiven/When/NOTEで一致"
    two_when = draft.replace("  Then 予約は成立しない", "  When 予約は成立しない")
    assert any(p["kind"] == "行いの数" for p in check(parse(two_when), False, matrix)), "反例: Whenが2つ"
    wrong_reason = draft.replace("停止中顧客は新しい利用枠を確保できないため\n", "違う理由\n")
    assert any(p["kind"] == "NOTE" for p in check(parse(wrong_reason), False, matrix)), "反例: NOTEのReasonが不一致"

    def run(stdin_text, *argv):
        return subprocess.run([sys.executable, __file__, "check", *argv], input=stdin_text, text=True, capture_output=True)

    matrix_arg = json.dumps(matrix, ensure_ascii=False)
    assert run("", "--matrix-json", matrix_arg).returncode == 2, "境界例: 空stdinはexit 2"
    assert run(draft, "--matrix-json", "{broken").returncode == 2, "境界例: 不正JSONはexit 2"
    assert run(draft, "--matrix-json", "[]").returncode == 2, "境界例: objectでないマトリクスはexit 2"
    assert run(draft).returncode == 2, "境界例: --matrix-json 欠落はargparseが拒否"
    assert run(draft, "--file", "x", "--matrix", "y").returncode == 2, "境界例: 旧引数 --file / --matrix はargparseが拒否"
    assert run(draft, "--matrix-json", matrix_arg).returncode == 0, "正例: stdin本文＋引数マトリクスで通る"
    assert run(two_when, "--matrix-json", matrix_arg).returncode == 1, "反例: 違反はexit 1"
    print(json.dumps({"self_test": "passed", "cases": 10}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check")
    check.add_argument("--matrix-json", required=True, help="条件マトリクスJSON文字列")
    sub.add_parser("self-test")
    args = p.parse_args()
    if args.cmd == "self-test":
        self_test()
        return
    cmd_check(args)


if __name__ == "__main__":
    main()
