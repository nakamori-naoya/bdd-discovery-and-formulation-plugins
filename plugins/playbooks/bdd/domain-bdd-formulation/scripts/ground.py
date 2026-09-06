#!/usr/bin/env python3
"""依頼、参照資料、詰めた結果を、根拠づけられた入力へ1つに束ねる。

**この工程は問わない。** 問うのは前の工程であり、ここはその出力を受け取って束ねるだけである。
束ねた結果が `grounded_input` であり、以降の工程はこれ以外を業務事実の根拠にしない。

  ground.py --config <解決済みYAML> --topic <題材slug> --out <置き場>
            --request <依頼を書き出したファイル> --settled <詰めた結果のYAML>
            [--reference <参照資料>]... [--existing <既存資料>] [--scope <線引き>] [--force]

`--settled` に渡すのは、前の工程が `output_to` へ書いた出力YAMLである。
読むのは `status` / `decisions` / `open_questions` の3つだけで、
それ以外の形・置き場・記録方式は前の工程の内部事情として扱わない。

標準出力へJSONを1行返す。exit 0 = 束ねた / 2 = 束ねられない。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

TOPIC_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def die(message: str) -> "None":
    print("[error] " + message, file=sys.stderr)
    raise SystemExit(2)


def read_yaml(path: Path):
    result = subprocess.run(["yq", "-o=json", "-I=0", ".", os.fspath(path)],
                            capture_output=True, text=True)
    if result.returncode:
        die("YAMLとして読めない: " + str(path))
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        die("YAMLとして読めない: " + str(path))


def existing_file(raw: str, label: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = (Path.cwd() / path)
    if path.is_symlink() or not path.is_file():
        die(f"{label} はsymlinkでない既存ファイルでなければならない: {raw}")
    if path.stat().st_size == 0:
        die(f"{label} が空である: {raw}")
    return path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--settled", required=True)
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--existing")
    parser.add_argument("--scope")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.topic or set(args.topic) - TOPIC_ALLOWED or ".." in args.topic:
        die("--topic が不正（英数と . _ - のみ）: " + args.topic)

    config_path = Path(args.config)
    if not config_path.is_file():
        die("--config に解決済みYAMLが要る: " + args.config)
    config = read_yaml(config_path)
    if not isinstance(config, dict):
        die("解決済みYAMLがmappingでない: " + args.config)
    playbook = config.get("playbook") or {}
    sources = ((playbook.get("contract") or {}).get("grounding_sources")) or []
    if not sources:
        die("playbook.contract.grounding_sources が無い。根拠の出所を宣言していない段取りでは束ねない")

    request = existing_file(args.request, "--request")
    settled_path = existing_file(args.settled, "--settled")
    settled = read_yaml(settled_path)
    if not isinstance(settled, dict):
        die("--settled の出力がmappingでない: " + args.settled)
    status = settled.get("status")
    if status != "completed":
        die(f"詰める工程が完了していない（status={status!r}）。未完のまま後続へ渡さない")
    decisions = settled.get("decisions") or []
    open_questions = settled.get("open_questions") or []
    if not isinstance(decisions, list) or not isinstance(open_questions, list):
        die("--settled の decisions / open_questions が配列でない")

    references = [existing_file(raw, "--reference") for raw in args.reference]
    existing = existing_file(args.existing, "--existing") if args.existing else None
    scope = existing_file(args.scope, "--scope") if args.scope else None

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    if out_dir.is_symlink():
        die("--out がsymlinkである: " + args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / f"{args.topic}.grounded-input.md"
    if destination.exists() and not args.force:
        die(f"すでにある: {destination}（上書きするなら --force）")

    lines: list[str] = []
    lines.append(f"# 根拠づけられた入力 — {args.topic}")
    lines.append("")
    lines.append("**ここに無いものを業務事実として扱わない。** 一般知識からもっともらしい事実を足さない。")
    lines.append("")
    lines.append("- 根拠の出所: " + " / ".join(str(s) for s in sources))
    lines.append("")
    lines.append("## 依頼")
    lines.append("")
    lines.append(request.read_text(encoding="utf-8").rstrip())
    lines.append("")
    if existing is not None:
        lines.append("## 反証の対象にした既存資料")
        lines.append("")
        lines.append("- " + str(existing))
        lines.append("")
    if references:
        lines.append("## 参照資料")
        lines.append("")
        lines.extend("- " + str(path) for path in references)
        lines.append("")
    if scope is not None:
        lines.append("## 線引き")
        lines.append("")
        lines.append(scope.read_text(encoding="utf-8").rstrip())
        lines.append("")
    lines.append("## 決めたこと")
    lines.append("")
    if decisions:
        for item in decisions:
            if not isinstance(item, dict):
                die("decisions の要素がmappingでない")
            lines.append(f"- **{item.get('question', '')}** → {item.get('answer', '')}")
            rationale = item.get("rationale")
            if rationale:
                lines.append(f"  - なぜ: {rationale}")
    else:
        lines.append("なし")
    lines.append("")
    lines.append("## 決まらなかったこと")
    lines.append("")
    if open_questions:
        for item in open_questions:
            if not isinstance(item, dict):
                die("open_questions の要素がmappingでない")
            lines.append(f"- [{item.get('state', 'open')}] {item.get('question', '')}")
            reason = item.get("reason")
            if reason:
                lines.append(f"  - 理由: {reason}")
    else:
        lines.append("なし")
    lines.append("")

    try:
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        die("根拠づけられた入力を書けない: " + str(exc))

    print(json.dumps({
        "grounded_input": str(destination.resolve()),
        "existing_document": str(existing) if existing else None,
        "core_scope": str(scope) if scope else None,
        "decisions": len(decisions),
        "open_questions": len(open_questions),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
