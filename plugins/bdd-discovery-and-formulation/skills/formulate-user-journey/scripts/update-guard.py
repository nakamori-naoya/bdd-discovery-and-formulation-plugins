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
        raise SystemExit("[error] 入力はsymlinkではない既存のuser-journey-bdd正本でなければならない")
    if existing.resolve() != output.resolve():
        raise SystemExit("[error] formulationは新規資料を作らず、入力されたuser-journey-bdd正本と同じパスを更新する")
    print(json.dumps({"update_target": str(existing.resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
