#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    existing = Path(args.existing)
    output = Path(args.output)
    if not existing.is_file() or existing.is_symlink():
        raise SystemExit("[error] 入力はsymlinkではない既存のRDB論理設計資料でなければならない")
    if existing.resolve() != output.resolve():
        raise SystemExit("[error] data-model-formulationは新規の論理資料を作らず、入力資料と同じパスを更新する")
    print(json.dumps({"logical_update_target": str(existing.resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
