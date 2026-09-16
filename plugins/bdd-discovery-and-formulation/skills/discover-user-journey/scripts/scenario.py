#!/usr/bin/env python3
"""ユーザー目的達成BDDの機械判定できる構造だけを検査する。

  scenario.py check --file <場面草案Markdown> --matrix <条件マトリクスJSON>

stdoutへJSONを1行ずつ返す。exit 0 = 違反なし / 1 = 違反あり（各行がline, kind, detail, howto） / 2 = 入力を読めない。
検査するのは場面の連番、Given / When / Thenの有無と順序、場面間の接続、失敗場面のNOTE、
条件マトリクスとの対応だけである。冒頭の段落が誰の何の目的かを運ぶかは意味評価に残す。

読む記法は write-doc の `user-journey-bdd` 型（document_type）の本文形である:
  `## 場面 <連番>: <名前>`、コードフェンス内の `Given: …` / `  And: …` / `When: …` / `Then: …`、
  `  NOTE: Rule: <規則>` と続く `    Source: …` / `    Reason: …`、`**接続**: …`。
keyword の後がコロンでも空白でも同じ step として読む。
"""

import argparse
import json
import re
from pathlib import Path

from scenario_matrix import validate as validate_matrix

SCENE = re.compile(r"^#{2,3}\s+場面\s+(\d+)\s*:\s*(.+?)\s*$")
CONNECTION = re.compile(r"^\*{0,2}接続\*{0,2}\s*:\s*(.*?)\s*$")
STEP = re.compile(r"^\s*(Given|When|Then|And|But|前提|もし|ならば|かつ|しかし)(?::\s*|\s+)(.+?)\s*$")
NOTE = re.compile(r"^\s*NOTE\s*:\s*(?:(Rule|Source|Reason)\s*:\s*(.+?))?\s*$")
NOTE_FIELD = re.compile(r"^\s*(Rule|Source|Reason)\s*:\s*(.+?)\s*$")
KIND = {"Given": "given", "前提": "given", "When": "when", "もし": "when", "Then": "then", "ならば": "then"}
def fail(message, code=2):
    print(json.dumps({"error": message}, ensure_ascii=False))
    raise SystemExit(code)



def parse(text):
    scenes = []
    current = None
    previous_kind = None
    in_note = False
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        match = SCENE.match(line)
        if match:
            current = {
                "line": line_number,
                "number": int(match.group(1)),
                "name": match.group(2).strip(),
                "steps": [],
                "connections": [],
                "notes": [],
            }
            scenes.append(current)
            previous_kind, in_note = None, False
            continue
        if current is None:
            continue
        note_match = NOTE.match(line)
        if note_match:
            fields = {}
            if note_match.group(1):
                fields[note_match.group(1).lower()] = note_match.group(2).strip()
            current["notes"].append({"line": line_number, "fields": fields})
            in_note = True
            continue
        note_field = NOTE_FIELD.match(line)
        if note_field and in_note and current["notes"]:
            current["notes"][-1]["fields"][note_field.group(1).lower()] = note_field.group(2).strip()
            continue
        connection_match = CONNECTION.match(stripped)
        if connection_match:
            current["connections"].append((line_number, connection_match.group(1)))
            continue
        step = STEP.match(line)
        if step:
            in_note = False
            keyword, body = step.groups()
            kind = KIND.get(keyword, previous_kind or "given")
            current["steps"].append({"line": line_number, "kind": kind, "body": body})
            previous_kind = kind
    return scenes


def check(text, matrix):
    scenes = parse(text)
    problems = []

    def add(line, kind, detail, howto):
        problems.append({"line": line, "kind": kind, "detail": detail, "howto": howto})

    if not scenes:
        add(0, "場面数", "場面が0件", "開始地点から最終地点へ進むインタラクション場面を1件以上書く")

    matrix_by_name = {item["name"]: item for item in matrix.get("scenarios", []) if isinstance(item, dict) and isinstance(item.get("name"), str)}
    scene_names = {scene["name"] for scene in scenes if scene["name"]}
    for missing in sorted(scene_names - set(matrix_by_name)):
        add(0, "条件マトリクス", f"場面に対応する条件マトリクスが無い: {missing}", "同じ場面名で条件マトリクスを書く")
    for extra in sorted(set(matrix_by_name) - scene_names):
        add(0, "条件マトリクス", f"場面に無いシナリオがある: {extra}", "場面と条件マトリクスを一対一にする")

    expected = list(range(1, len(scenes) + 1))
    actual = [scene["number"] for scene in scenes]
    if actual != expected:
        add(scenes[0]["line"] if scenes else 0, "場面順", f"番号が{actual}", f"1から順に{expected}とする")

    for index, scene in enumerate(scenes):
        kinds = [step["kind"] for step in scene["steps"]]
        if not scene["name"]:
            add(scene["line"], "場面名", "場面名が空", "その場面で生じる意味のある変化を名前にする")
        if kinds.count("given") < 1:
            add(scene["line"], "Given", "前提が無い", "結果に必要な開始状態と業務条件をすべて書く")
        if kinds.count("when") != 1:
            add(scene["line"], "When", f"主要な働きかけが{kinds.count('when')}件", "1場面の主要な働きかけを1件にする。増える場合は場面を分ける")
        if kinds.count("then") < 1:
            add(scene["line"], "Then", "観測できる応答が無い", "役割から観測できる応答と次へ渡す状態を書く")
        order = {"given": 0, "when": 1, "then": 2}
        if kinds != sorted(kinds, key=order.get):
            add(scene["line"], "step順", "Given / When / Thenの順ではない", "状態、働きかけ、応答の順に並べる")
        if index < len(scenes) - 1:
            if len(scene["connections"]) != 1 or not scene["connections"][0][1]:
                add(scene["line"], "場面の接続", "次の場面への接続が1件明示されていない", "接続: に次の場面へ渡す状態を書く")
        elif len(scene["connections"]) > 1:
            add(scene["line"], "場面の接続", "最後の場面に接続が複数ある", "最終地点との対応だけを書く")

        matrix_item = matrix_by_name.get(scene["name"])
        if matrix_item:
            givens = {step["body"] for step in scene["steps"] if step["kind"] == "given"}
            premises = {item.get("text") for item in matrix_item.get("premises", []) if isinstance(item, dict)}
            if givens != premises:
                add(scene["line"], "Givenと条件マトリクス", "必要条件とGivenが一致しない", "全premisesをGivenへ一件ずつ写す")
            whens = [step for step in scene["steps"] if step["kind"] == "when"]
            trigger = (matrix_item.get("trigger") or {}).get("text")
            if len(whens) == 1 and whens[0]["body"] != trigger:
                add(whens[0]["line"], "Whenと条件マトリクス", "トリガー本文が一致しない", "actionまたはeventとして確定したトリガーを書く")
            failure = matrix_item.get("expected") == "failure"
            notes = scene["notes"]
            if failure and len(notes) != 1:
                add(scene["line"], "NOTE", f"失敗場面のNOTEが{len(notes)}件", "全Thenの直後にNOTEを一つ置く")
            elif not failure and notes:
                add(notes[0]["line"], "NOTE", "成功場面にNOTEがある", "成功場面からNOTEを削る")
            elif failure and notes:
                fields = notes[0]["fields"]
                expected_note = matrix_item.get("note") or {}
                for field in ("rule", "source", "reason"):
                    if fields.get(field) != expected_note.get(field):
                        add(notes[0]["line"], "NOTE", f"{field}が条件マトリクスと一致しない", "外部正本を含む確定済みの失敗理由を写す")
                last_step = max(step["line"] for step in scene["steps"]) if scene["steps"] else scene["line"]
                if notes[0]["line"] <= last_step:
                    add(notes[0]["line"], "NOTE", "Thenの途中にある", "すべてのThenとAndの直後へ移す")

    return problems, len(scenes)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--file", required=True)
    check_parser.add_argument("--matrix", required=True)
    args = parser.parse_args()

    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"story draftを読めない: {exc}")

    try:
        matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"--matrixを読めない: {exc}")
    matrix_problems = validate_matrix(matrix)
    if matrix_problems:
        for problem in matrix_problems:
            print(json.dumps(problem, ensure_ascii=False))
        fail(f"条件マトリクスに{len(matrix_problems)}件の違反", 1)
    problems, scene_count = check(text, matrix)
    for problem in problems:
        print(json.dumps(problem, ensure_ascii=False))
    if problems:
        fail(f"{len(problems)}件の違反", 1)
    print(json.dumps({"check": "clean", "focus": "user-journey", "scenes": scene_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
