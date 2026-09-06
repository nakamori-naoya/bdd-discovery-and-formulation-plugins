#!/usr/bin/env python3
"""資料を保存したあとに、この段取りが自分で作った作業用ファイルだけを消す。

**後片付けは自分でする。** 外部pluginの後片付け機能へ委譲しない。

消してよいのは、`playbook.contract.cleanup.delete_after_document` に宣言した
中間成果物のうち、次をすべて満たすものだけである。

- repository の中にある、symlinkでない通常ファイル
- `preserve` に宣言した最終資料と入力資料のどれとも別のファイル
- **git が追跡していない**ファイル（追跡済みは、宣言に載っていても消さない）

  cleanup.py --config <解決済みYAML> --artifact <名前>=<path> [...] [--dry-run]

標準出力へJSONを1行返す。exit 0 = 後片付け完了 / 2 = 実行できない。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


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


def contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def tracked(repo_root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", os.fspath(repo_root), "ls-files", "--error-unmatch", "--", os.fspath(path)],
        capture_output=True, text=True)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        die("--config に解決済みYAMLが要る: " + args.config)
    config = read_yaml(config_path)
    if not isinstance(config, dict):
        die("解決済みYAMLがmappingでない: " + args.config)

    repo_raw = config.get("repo_root")
    if not isinstance(repo_raw, str) or not repo_raw:
        die("解決済みYAMLに repo_root が無い")
    repo_root = Path(repo_raw).resolve()
    if not repo_root.is_dir():
        die("repo_root がdirectoryでない: " + repo_raw)

    cleanup = ((config.get("playbook") or {}).get("contract") or {}).get("cleanup") or {}
    delete_names = cleanup.get("delete_after_document")
    preserve_names = cleanup.get("preserve")
    if not isinstance(delete_names, list) or not delete_names:
        die("playbook.contract.cleanup.delete_after_document が無い")
    if not isinstance(preserve_names, list) or not preserve_names:
        die("playbook.contract.cleanup.preserve が無い")
    declared = set(delete_names) | set(preserve_names)

    artifacts: dict[str, str] = {}
    for raw in args.artifact:
        if "=" not in raw:
            die("--artifact は <名前>=<path> の形で渡す: " + raw)
        name, value = raw.split("=", 1)
        name = name.strip()
        if name not in declared:
            die(f"contract.cleanup に宣言の無い成果物は扱わない: {name}")
        if name in artifacts:
            die("同じ成果物を2度渡している: " + name)
        artifacts[name] = value.strip()

    missing = sorted(declared - set(artifacts))
    if missing:
        die("宣言した成果物の場所が渡されていない: " + ", ".join(missing))

    protected: set[Path] = set()
    for name in preserve_names:
        value = artifacts.get(name) or ""
        if not value:
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        try:
            protected.add(candidate.resolve())
        except OSError:
            continue

    deleted: list[str] = []
    kept: list[dict[str, str]] = []

    def keep(path: str, reason: str) -> None:
        kept.append({"path": path, "reason": reason})

    for name in delete_names:
        value = artifacts[name]
        if not value:
            keep("", f"{name}: 場所が空")
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        if candidate.is_symlink():
            keep(str(candidate), f"{name}: symlink")
            continue
        if not candidate.exists():
            keep(str(candidate), f"{name}: 既に無い")
            continue
        resolved = candidate.resolve()
        if not resolved.is_file():
            keep(str(resolved), f"{name}: 通常ファイルでない")
            continue
        if not contained(repo_root, resolved):
            keep(str(resolved), f"{name}: repositoryの外")
            continue
        if ".git" in resolved.relative_to(repo_root).parts:
            keep(str(resolved), f"{name}: .git の中")
            continue
        if resolved in protected:
            keep(str(resolved), f"{name}: 保持対象と同じファイル")
            continue
        if tracked(repo_root, resolved):
            keep(str(resolved), f"{name}: gitが追跡済み")
            continue
        if args.dry_run:
            keep(str(resolved), f"{name}: dry-run")
            continue
        try:
            resolved.unlink()
        except OSError as exc:
            die(f"{name} を消せない: {exc}")
        deleted.append(str(resolved))

    print(json.dumps({
        "repo_root": str(repo_root),
        "deleted": deleted,
        "kept": kept,
        "preserved": sorted(str(path) for path in protected),
        "dry_run": bool(args.dry_run),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
