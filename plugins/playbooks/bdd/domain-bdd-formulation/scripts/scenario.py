#!/usr/bin/env python3
"""シナリオを機械で検査し、通ったものだけを保存する。

**読みやすさは自動化のしやすさより優先する。** ここで見るのは、
その読みやすさを機械で守れる部分だけである。意図が伝わるかは人の判断に残る。

  scenario.py check --config <解決済みplaybook YAML> --file <path>
                    [--allow <語>]...
      -> 違反を1件ずつ出し、1つでもあれば異常終了する

  scenario.py save --config <json|path> --topic <題材> --file <path> [--force]
      -> 検査を通ったものだけを scenario_dir へ保存する

  scenario.py vocabulary --config <解決済みplaybook YAML>
      -> その高さで書けない語と、その理由を出す
"""

import argparse
import json
import os
import re
import subprocess
import sys

FOCUSES = ("domain", "use-case", "journey")

# 高さごとに書けない語。**同じ規律を3つの高さへ当てるのが間違いのもとである。**
STORAGE = ["テーブル", "カラム", "SQL", "スキーマ", "インデックス", "主キー"]
WIRE = ["エンドポイント", "リクエスト", "レスポンス", "HTTP", "gRPC", "JSON", "ペイロード"]
SCREEN = ["画面", "ボタン", "クリック", "押下", "入力欄", "プルダウン", "モーダル", "URL", "タブ"]
CODE = ["クラス", "メソッド", "関数", "enum", "セレクタ", "HTML", "CSS"]
FORBIDDEN = {
    "domain": STORAGE + WIRE + SCREEN + CODE,
    "use-case": STORAGE + SCREEN + CODE,
    "journey": STORAGE + WIRE + CODE,
}
WHY = {
    "domain": "業務の決まりは、作りを変えても変わらない言葉だけで書く",
    "use-case": "要求と応答の話に、保存や画面の都合を持ち込まない",
    "journey": "通しの確認に、保存や境界の実装を持ち込まない",
}

FEATURE = re.compile(r"^\s*(Feature|機能)\s*:\s*(.*)$")
RULE = re.compile(r"^\s*(Rule|ルール)\s*:\s*(.*)$")
BACKGROUND = re.compile(r"^\s*(Background|背景)\s*:")
SCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario Template|シナリオテンプレート|シナリオアウトライン|Scenario|シナリオ)\s*:\s*(.*)$")
EXAMPLES = re.compile(r"^\s*(Examples|Scenarios|例)\s*:")
STEP = re.compile(r"^\s*(Given|When|Then|And|But|前提|もし|ならば|かつ|しかし)\s+(.*)$")
KEYWORD_KIND = {"Given": "given", "前提": "given", "When": "when", "もし": "when",
                "Then": "then", "ならば": "then"}
PLACEHOLDER = re.compile(r"<([^<>]+)>")
VAGUE_NAME = re.compile(r"^(テスト|test|scenario\s*\d*|シナリオ\s*\d*|確認)$", re.I)
# または／or は、そのシナリオが何を主張しているのかを決められなくする。
DISJUNCTION = re.compile(r"(または|もしくは|\bor\b)", re.I)
FIRST_PERSON = re.compile(r"(^|[^ぁ-んァ-ン一-龥])私([^ぁ-んァ-ン一-龥]|$)")
CLOSURE = re.compile(r"^\s*#\s*クロージャ\s*:\s*(.*)$")
CLOSURE_BODY = "このシナリオの Given に書かれていない業務条件は、成立・結果に影響しない。"


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
    doc = {"features": [], "backgrounds": [], "scenarios": []}
    cur = None
    in_examples = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        m = CLOSURE.match(line)
        if m:
            if cur is not None:
                cur["closures"].append({"line": i, "text": m.group(1).strip()})
            continue
        if s.startswith("#"):
            continue
        m = FEATURE.match(line)
        if m:
            doc["features"].append({"line": i, "name": m.group(2).strip()})
            cur, in_examples = None, False
            continue
        if BACKGROUND.match(line):
            doc["backgrounds"].append({"line": i})
            cur, in_examples = None, False
            continue
        if RULE.match(line):
            cur, in_examples = None, False
            continue
        m = SCENARIO.match(line)
        if m:
            cur = {"line": i, "keyword": m.group(1), "name": m.group(2).strip(),
                   "outline": "Outline" in m.group(1) or "Template" in m.group(1)
                              or "テンプレート" in m.group(1) or "アウトライン" in m.group(1),
                   "steps": [], "examples": [], "closures": []}
            doc["scenarios"].append(cur)
            in_examples = False
            continue
        if EXAMPLES.match(line):
            in_examples = bool(cur)
            continue
        if s.startswith("|") and in_examples and cur is not None:
            cells = [c.strip() for c in s.strip("|").split("|")]
            cur["examples"].append({"line": i, "cells": cells})
            continue
        m = STEP.match(line)
        if m and cur is not None:
            kw, body = m.group(1), m.group(2).strip()
            kind = KEYWORD_KIND.get(kw)
            if kind is None:  # And / But / かつ / しかし は直前を継ぐ
                kind = cur["steps"][-1]["kind"] if cur["steps"] else "given"
            cur["steps"].append({"line": i, "keyword": kw, "kind": kind, "text": body})
    return doc


def check(doc, focus, max_steps, allow_background, limits, allow):
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

    forbidden = [w for w in FORBIDDEN[focus] if w not in set(allow)]
    seen_names = {}
    for sc in doc["scenarios"]:
        name, ln = sc["name"], sc["line"]
        if not name:
            bad(ln, "シナリオ名", "名前が無い", "何の話かが1行で分かる名前を付ける")
        elif VAGUE_NAME.match(name):
            bad(ln, "シナリオ名", "意図を説明していない名前: {}".format(name),
                "そのシナリオが何を主張するかを名前にする")
        if name:
            if name in seen_names:
                bad(ln, "シナリオ名", "同じ名前が {} 行目にもある".format(seen_names[name]),
                    "どこが違うのかを名前に出す")
            seen_names[name] = ln

        givens = [s for s in sc["steps"] if s["kind"] == "given"]
        whens = [s for s in sc["steps"] if s["kind"] == "when"]
        thens = [s for s in sc["steps"] if s["kind"] == "then"]
        if len(whens) != 1:
            bad(ln, "行いの数", "1つのシナリオに行いが {} 個".format(len(whens)),
                "行いは1つ。増えるなら片方は前提か、まとめ方が足りない")
        if not thens:
            bad(ln, "結果", "結果が無い", "何が起きるべきかを書く")
        kinds = [s["kind"] for s in sc["steps"]]
        order = {"given": 0, "when": 1, "then": 2}
        if kinds != sorted(kinds, key=order.get):
            bad(ln, "ステップの順序", "Given / When / Then の順になっていない",
                "すでにある前提、検証する唯一の入力、観測可能な結果の順に並べる")
        if len(sc["steps"]) > max_steps:
            bad(ln, "長さ", "ステップが {} 個（上限 {}）".format(len(sc["steps"]), max_steps),
                "説明に要らないステップを削る")

        closures = sc["closures"]
        if len(closures) != 1:
            bad(ln, "クロージャ宣言", "宣言が {} 個".format(len(closures)),
                "シナリオの最後に規定のクロージャ宣言を1行だけ置く")
        else:
            closure = closures[0]
            if closure["text"] != CLOSURE_BODY:
                bad(closure["line"], "クロージャ宣言", "規定の文言と一致しない",
                    "書かれていない業務条件の扱いを規定の文言で宣言する")
            content_lines = [s["line"] for s in sc["steps"]] + [e["line"] for e in sc["examples"]]
            if content_lines and closure["line"] <= max(content_lines):
                bad(closure["line"], "クロージャ宣言", "シナリオの途中にある",
                    "全stepとExamplesの後へ移す")

        norm = {}
        for st in sc["steps"]:
            t, sl = st["text"], st["line"]
            if DISJUNCTION.search(t):
                bad(sl, "または", "1文が2つのことを言っている: {}".format(t),
                    "シナリオを2つに分ける。または は、何を主張しているか決められなくする")
            if FIRST_PERSON.search(t):
                bad(sl, "一人称", "「私」を使っている: {}".format(t),
                    "役割の名前で書く")
            for w in forbidden:
                if w in t:
                    bad(sl, "この焦点で書けない語", "{}（{}）".format(w, t), WHY[focus])
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
                if len(header) > limits["columns"]:
                    bad(sc["examples"][0]["line"], "表の幅",
                        "{} 列（上限 {}）".format(len(header), limits["columns"]),
                        "1画面に収まらない表は、共通理解を壊す")
                if len(rows) > limits["rows"]:
                    bad(sc["examples"][0]["line"], "表の高さ",
                        "{} 行（上限 {}）".format(len(rows), limits["rows"]),
                        "同じ振る舞いを示す行は消す。行を足す前に、その値の意味を言えるか確かめる")
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
    if focus not in FOCUSES:
        fail("playbookのfocusが不正: {!r}（{}）".format(focus, " / ".join(FOCUSES)))
    return focus


def limits_of(cfg):
    lim = playbook_config(cfg).get("examples_limits") or {}
    try:
        return {"rows": int(lim.get("rows", 10)), "columns": int(lim.get("columns", 6))}
    except (TypeError, ValueError):
        fail("examples_limits が数値でない")


def run_check(cfg, path, focus, allow):
    pb = playbook_config(cfg)
    doc = parse(read_text(path))
    try:
        max_steps = int(pb.get("max_steps", 5))
    except (TypeError, ValueError):
        fail("max_steps が数値でない")
    problems = check(doc, focus, max_steps, bool(pb.get("allow_background")),
                     limits_of(cfg), allow)
    return doc, problems


def cmd_check(args, cfg):
    focus = resolve_focus(cfg)
    doc, problems = run_check(cfg, args.file, focus, args.allow)
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
    doc, problems = run_check(cfg, args.file, focus, args.allow)
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


def cmd_vocabulary(args, cfg):
    focus = resolve_focus(cfg)
    print(json.dumps({"focus": focus, "forbidden": FORBIDDEN[focus], "why": WHY[focus]},
                     ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("check")
    sp.add_argument("--config", required=True)
    sp.add_argument("--file", required=True)
    sp.add_argument("--allow", action="append", default=[])

    sp = sub.add_parser("save")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--file", required=True)
    sp.add_argument("--allow", action="append", default=[])
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("vocabulary")
    sp.add_argument("--config", required=True)

    args = p.parse_args()
    cfg = load_config(args.config)
    {"check": cmd_check, "save": cmd_save, "vocabulary": cmd_vocabulary}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
