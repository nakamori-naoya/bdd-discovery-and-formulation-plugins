#!/usr/bin/env python3
"""User Journey mapの機械判定できる構造だけを検査し、初回保存する。"""

import argparse
import json
import re
from pathlib import Path

LABELS = ("ユーザー", "目的", "開始地点", "最終地点", "完了条件", "中心の問い", "Journeyとして扱う理由", "Journeyに含めない問い")
FIELDS = ("直前の状態", "行う役割", "働きかけ", "観測できる応答", "次の状態", "接続")
LABEL = re.compile(r"^-\s+\*{0,2}(ユーザー|目的|開始地点|最終地点|完了条件|中心の問い|Journeyとして扱う理由|Journeyに含めない問い)\*{0,2}\s*:\s*(.*?)\s*$")
SCENE = re.compile(r"^###\s+場面\s+(\d+)\s*:\s*(.+?)\s*$")
FIELD = re.compile(r"^-\s+\*{0,2}(直前の状態|行う役割|働きかけ|観測できる応答|次の状態|接続)\*{0,2}\s*:\s*(.*?)\s*$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
FORBIDDEN = (
    "画面", "ボタン", "クリック", "押下", "入力欄", "url", "api", "endpoint", "request", "response",
    "db", "table", "テーブル", "class", "method", "test runner", "テストランナー", "ci", "flaky",
)


def emit_error(message, problems=None, code=2):
    for problem in problems or []:
        print(json.dumps(problem, ensure_ascii=False))
    print(json.dumps({"error": message}, ensure_ascii=False))
    raise SystemExit(code)


def contains(text, word):
    if word.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", text.lower()) is not None
    return word in text


def validate(text):
    labels = {name: [] for name in LABELS}
    scenes = []
    current = None
    sections = set()
    problems = []
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped in {"## 場面", "## 分岐", "## 未決"}:
            sections.add(stripped)
        match = LABEL.match(stripped)
        if match:
            labels[match.group(1)].append((number, match.group(2)))
        match = SCENE.match(line)
        if match:
            current = {"line": number, "number": int(match.group(1)), "name": match.group(2), "fields": {}}
            scenes.append(current)
            continue
        match = FIELD.match(stripped)
        if match and current is not None:
            current["fields"].setdefault(match.group(1), []).append((number, match.group(2)))

    for name, values in labels.items():
        if len(values) != 1 or not values[0][1]:
            problems.append({"line": values[0][0] if values else 0, "kind": "Journeyの両端", "detail": f"{name}が空または1件ではない"})
    for section in ("## 場面", "## 分岐", "## 未決"):
        if section not in sections:
            problems.append({"line": 0, "kind": "必須節", "detail": f"{section}が無い"})
    if len(scenes) < 2:
        problems.append({"line": scenes[0]["line"] if scenes else 0, "kind": "Journey境界", "detail": "意味のある場面が二つ未満。単一責任または単一振る舞いとして扱う"})
    expected = list(range(1, len(scenes) + 1))
    actual = [scene["number"] for scene in scenes]
    if actual != expected:
        problems.append({"line": scenes[0]["line"] if scenes else 0, "kind": "場面順", "detail": f"番号が{actual}。{expected}にする"})
    for scene in scenes:
        if not scene["name"].strip():
            problems.append({"line": scene["line"], "kind": "場面名", "detail": "場面名が空"})
        for name in FIELDS:
            values = scene["fields"].get(name, [])
            if len(values) != 1 or not values[0][1]:
                problems.append({"line": values[0][0] if values else scene["line"], "kind": "場面構造", "detail": f"{name}が空または1件ではない"})
            elif any(contains(values[0][1], word) for word in FORBIDDEN):
                problems.append({"line": values[0][0], "kind": "責務外", "detail": f"{name}に実装またはテスト実行の語がある"})
    return problems, labels, scenes


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        emit_error(f"Journey mapを読めない: {exc}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--file", required=True)
    write = sub.add_parser("write")
    write.add_argument("--repo", required=True)
    write.add_argument("--slug", required=True)
    write.add_argument("--file", required=True)
    args = parser.parse_args()

    text = read(args.file)
    problems, labels, scenes = validate(text)
    if problems:
        emit_error(f"Journey mapに{len(problems)}件の違反", problems, 1)
    result = {"check": "clean", "scenes": len(scenes), "user": labels["ユーザー"][0][1], "purpose": labels["目的"][0][1]}
    if args.command == "check":
        print(json.dumps(result, ensure_ascii=False))
        return
    if not SLUG.fullmatch(args.slug):
        emit_error("--slugは小文字英数字とハイフン、128文字までにする")
    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        emit_error("--repoがdirectoryではない")
    target = repo / "bdd" / "discovery" / "user-journey" / f"{args.slug}.md"
    if target.exists():
        emit_error(f"既存Journey mapは上書きしない: {target}", code=3)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    result.update({"written": str(target)})
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
