#!/usr/bin/env python3
"""formulationの更新先が、入力された既存正本と同じ実体であることを検査する。

  update-guard.py check --existing <既存正本の絶対path> --output <更新先として決めた絶対path>
      -> exit 0 で {"update_target": <解決済み絶対path>} をstdoutへ返す
         exit 1 = 既存正本がsymlinkか通常fileでない、または両pathが別の実体を指す（stdoutへ {"error": ...}）
  update-guard.py self-test

正本: 入力 `existing_*_path`（symlinkではない既存file）。
入力: 2つのpath引数だけ。本文は受け取らない（fileの中身を読まず、実体の同一性だけを見る）。
合格述語: existing が symlink でない通常 file で、resolve() が output の resolve() と一致する。
意味評価として残す範囲: その正本が本当に更新対象として妥当か、更新内容が正本の型に合うか。
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))


def guard(existing_path, output_path):
    """(問題文字列 or None, 解決済みpath or None)"""
    existing = Path(existing_path)
    output = Path(output_path)
    if existing.is_symlink() or not existing.is_file():
        return "入力はsymlinkではない既存の正本fileでなければならない: {}".format(existing_path), None
    if existing.resolve() != output.resolve():
        return "formulationは新規資料を作らず、入力された正本と同じpathを更新する: existing={} output={}".format(existing_path, output_path), None
    return None, str(existing.resolve())


def cmd_check(args):
    problem, target = guard(args.existing, args.output)
    if problem:
        emit({"error": problem})
        return 1
    emit({"update_target": target})
    return 0


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        existing = Path(tmp) / "existing.md"
        existing.write_text("# 正本\n", encoding="utf-8")
        other = Path(tmp) / "other.md"
        link = Path(tmp) / "link.md"
        os.symlink(existing, link)
        assert guard(existing, existing)[0] is None, "正例: 同一path"
        assert guard(existing, Path(tmp) / "." / "existing.md")[0] is None, "境界例: 表記が違っても同じ実体なら受理"
        assert guard(existing, other)[0], "反例: 別pathへの出力"
        assert guard(link, link)[0], "反例: symlinkの正本"
        assert guard(Path(tmp) / "missing.md", Path(tmp) / "missing.md")[0], "反例: 存在しない正本"

        def run(*argv):
            return subprocess.run([sys.executable, __file__, "check", *map(str, argv)], text=True, capture_output=True)

        ok = run("--existing", existing, "--output", existing)
        assert ok.returncode == 0 and json.loads(ok.stdout)["update_target"] == str(existing.resolve()), "正例: CLIでupdate_targetを返す"
        bad = run("--existing", existing, "--output", other)
        assert bad.returncode == 1 and "error" in json.loads(bad.stdout), "反例: CLIでexit 1とJSON診断"
    emit({"self_test": "passed", "cases": 7})
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--existing", required=True)
    check.add_argument("--output", required=True)
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "self-test":
        return self_test()
    return cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
