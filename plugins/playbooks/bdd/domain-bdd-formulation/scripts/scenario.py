#!/usr/bin/env python3
"""シナリオを機械で検査し、通ったものだけを保存する。

**読みやすさは自動化のしやすさより優先する。** ここで見るのは、
その読みやすさを機械で守れる部分だけである。意図が伝わるかは人の判断に残る。

  scenario.py check --config <解決済みplaybook YAML> --file <path> --matrix <condition-matrix.json>
      -> 違反を1件ずつ出し、1つでもあれば異常終了する

  scenario.py save --config <json|path> --topic <題材> --file <path> --matrix <condition-matrix.json> [--force]
      -> 検査を通ったものだけを scenario_dir へ保存する

"""

import argparse
import json
import os
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


def load_config(raw):
    raw = (raw or "").strip()
    if raw.startswith("{"):
        return json.loads(raw)
    try:
        r = subprocess.run(["yq", "-o=json", "-I=0", ".", raw], capture_output=True,
                           text=True, timeout=10, check=True)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        fail("--config が読めない: {}".format(e))


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        fail("シナリオを読めない: {}".format(e))


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
                        "外部正本なら相対Markdownリンクを写し、同じ資料ならSourceを省略する")
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


def playbook_config(cfg):
    value = cfg.get("playbook")
    return value if isinstance(value, dict) else cfg


def resolve_focus(cfg):
    focus = playbook_config(cfg).get("focus") or ""
    if focus != "domain":
        fail("playbookのfocusが不正: {!r}（domainのみ）".format(focus))
    return focus


def load_matrix(path):
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as e:
        fail("--matrix がJSONではない: {}".format(e))
    matrix_problems = validate_matrix(data)
    if matrix_problems:
        for item in matrix_problems:
            print(json.dumps(item, ensure_ascii=False))
        fail("条件マトリクスに {} 件の違反".format(len(matrix_problems)), 1)
    return data


def run_check(cfg, path, matrix_path):
    pb = playbook_config(cfg)
    doc = parse(read_text(path))
    matrix = load_matrix(matrix_path)
    problems = check(doc, bool(pb.get("allow_background")), matrix)
    return doc, problems


def cmd_check(args, cfg):
    focus = resolve_focus(cfg)
    doc, problems = run_check(cfg, args.file, args.matrix)
    for p in problems:
        print(json.dumps(p, ensure_ascii=False))
    if problems:
        print(json.dumps({"error": "{} 件の違反".format(len(problems)), "focus": focus},
                         ensure_ascii=False))
        sys.exit(1)
    print(json.dumps({"check": "clean", "focus": focus,
                      "scenarios": len(doc["scenarios"])}, ensure_ascii=False))


def cmd_save(args, cfg):
    focus = resolve_focus(cfg)
    topic = args.topic or ""
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$", topic) or ".." in topic:
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(topic))
    pb = playbook_config(cfg)
    d = pb.get("scenario_dir") or ""
    if not d:
        fail("playbookに scenario_dir が無い")
    if not os.path.isabs(d) and cfg.get("repo_root"):
        d = os.path.join(cfg["repo_root"], d)
    doc, problems = run_check(cfg, args.file, args.matrix)
    if problems:
        for p in problems:
            print(json.dumps(p, ensure_ascii=False))
        print(json.dumps({"error": "{} 件の違反があるため保存しない".format(len(problems))},
                         ensure_ascii=False))
        sys.exit(1)
    dest = os.path.join(d, "{}.feature".format(topic))
    if os.path.exists(dest) and not args.force:
        # 承認済みのシナリオを黙って書き換えない。シナリオの変更は仕様の変更である。
        fail("すでにある: {}（書き換えるなら --force）".format(dest), 3)
    try:
        os.makedirs(d, exist_ok=True)
        body = read_text(args.file)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(body if body.endswith("\n") else body + "\n")
    except OSError as e:
        fail("保存できない: {}".format(e))
    print(json.dumps({"saved": dest, "focus": focus, "scenarios": len(doc["scenarios"])},
                     ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("check")
    sp.add_argument("--config", required=True)
    sp.add_argument("--file", required=True)
    sp.add_argument("--matrix", required=True)

    sp = sub.add_parser("save")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--file", required=True)
    sp.add_argument("--matrix", required=True)
    sp.add_argument("--force", action="store_true")

    args = p.parse_args()
    cfg = load_config(args.config)
    {"check": cmd_check, "save": cmd_save}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
