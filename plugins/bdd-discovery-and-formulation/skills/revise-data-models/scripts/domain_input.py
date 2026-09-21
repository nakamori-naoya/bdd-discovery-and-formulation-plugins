#!/usr/bin/env python3
"""Validate explicit business-knowledge inputs before data modeling starts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def diagnostic(path: str, detail: str, howto: str) -> dict[str, str]:
    return {"path": path, "detail": detail, "howto": howto}


def tracked_files(root: Path) -> dict[str, str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=True, stdout=subprocess.PIPE)
    allowed: dict[str, str] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        candidate = root / raw.decode("utf-8")
        if candidate.is_symlink() or not candidate.is_file():
            continue
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        allowed[os.path.normpath(str(candidate))] = str(resolved)
    return allowed


def validate_file(value: object, path: str, allowed: dict[str, str], problems: list[dict[str, str]]) -> str | None:
    if not isinstance(value, str) or not value:
        problems.append(diagnostic(path, "空でない絶対pathではない", "通常fileの絶対pathを指定する"))
        return None
    if not os.path.isabs(value):
        problems.append(diagnostic(path, "相対pathである", "通常fileの絶対pathを指定する"))
        return None
    result = allowed.get(os.path.normpath(value))
    if result is None:
        problems.append(diagnostic(path, "対象repositoryの追跡済み通常fileではない", "対象repositoryへ記録済みの正式な定義のfileを指定する"))
    return result


def validate_paths(values: object, path: str, allowed: dict[str, str], problems: list[dict[str, str]]) -> list[str]:
    if not isinstance(values, list) or not values:
        problems.append(diagnostic(path, "1件以上のlistではない", "対応する業務知識の絶対pathを1件以上指定する"))
        return []
    normalized: list[str] = []
    for index, value in enumerate(values):
        result = validate_file(value, f"{path}[{index}]", allowed, problems)
        if result is not None:
            normalized.append(result)
    if len(set(normalized)) != len(normalized):
        problems.append(diagnostic(path, "同じfileが重複している", "重複を除いて一度だけ指定する"))
    return normalized


def check(payload: object) -> tuple[list[dict[str, str]], dict[str, object]]:
    problems: list[dict[str, str]] = []
    root = Path.cwd().resolve()
    allowed = tracked_files(root)
    if not isinstance(payload, dict):
        return [diagnostic("$", "JSON objectではない", "入力objectを渡す")], {}

    if "targets" in payload:
        targets = payload["targets"]
        if not isinstance(targets, list) or not targets:
            return [diagnostic("targets", "1件以上のlistではない", "改訂対象を1件以上指定する")], {}
        normalized_targets: list[dict[str, object]] = []
        logical_paths: list[str] = []
        for index, target in enumerate(targets):
            base = f"targets[{index}]"
            if not isinstance(target, dict) or set(target) != {"logical_document_path", "business_knowledge_paths"}:
                problems.append(diagnostic(base, "必要な2keyだけを持つobjectではない", "logical_document_pathとbusiness_knowledge_pathsを指定する"))
                continue
            logical = validate_file(target["logical_document_path"], f"{base}.logical_document_path", allowed, problems)
            knowledge = validate_paths(target["business_knowledge_paths"], f"{base}.business_knowledge_paths", allowed, problems)
            if logical is not None:
                logical_paths.append(logical)
                normalized_targets.append({"logical_document_path": logical, "business_knowledge_paths": knowledge})
        if len(set(logical_paths)) != len(logical_paths):
            problems.append(diagnostic("targets", "同じ論理資料が複数targetにある", "論理資料ごとにtargetを一つにする"))
        return problems, {"targets": normalized_targets}

    if set(payload) != {"business_knowledge_paths"}:
        return [diagnostic("$", "business_knowledge_pathsだけを持つobjectではない", "必須入力だけを渡す")], {}
    knowledge = validate_paths(payload["business_knowledge_paths"], "business_knowledge_paths", allowed, problems)
    return problems, {"business_knowledge_paths": knowledge}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] != "check":
        print(json.dumps({"error": "usage: domain_input.py check"}, ensure_ascii=False))
        return 2
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "標準入力が空である"}, ensure_ascii=False))
        return 2
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        print(json.dumps({"error": f"JSONを読めない: {error.msg}"}, ensure_ascii=False))
        return 2
    try:
        problems, normalized = check(payload)
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as error:
        print(json.dumps({"error": f"対象repositoryの追跡済みfileを読めない: {error}"}, ensure_ascii=False))
        return 2
    if problems:
        for problem in problems:
            print(json.dumps(problem, ensure_ascii=False))
        return 1
    print(json.dumps(normalized, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
