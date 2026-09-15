#!/usr/bin/env python3
"""線引き資料の決定的な構造を検査し、初回保存する。

語が業務・実装のどちらを意味するかは文脈に依存するため、ここでは判定しない。
"""

import argparse
import json
import os
import re
import subprocess
import sys

REQUIRED_SECTIONS = ("## コア", "## 支援", "## 汎用", "## スコープ外")
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def fail(msg, code=2):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def load_config(raw):
    raw = (raw or "").strip()
    if raw.startswith("{"):
        return json.loads(raw)
    try:
        result = subprocess.run(
            ["yq", "-o=json", "-I=0", ".", raw], capture_output=True,
            text=True, timeout=10, check=True,
        )
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        fail("--config が読めない: {}".format(e))


def read_body(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        fail("本文を読めない: {}".format(e))


def cmd_write(args, cfg):
    topic = args.topic or ""
    if not TOPIC_RE.match(topic) or ".." in topic:
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(topic))
    d = cfg.get("scope_dir") or ""
    if not d:
        fail("設定に scope_dir が無い")

    body = read_body(args.body_file)
    if not body.strip():
        fail("本文が空。線引きの無い線引きは保存しない")
    missing = [s for s in REQUIRED_SECTIONS if s not in body]
    if missing:
        # 節を落とすと「そこは考えなかった」のか「無かった」のかが読めなくなる。
        fail("節が足りない: {}（無いなら『なし』と書く）".format(" / ".join(missing)))
    p = os.path.join(d, "{}.md".format(topic))
    # 既にある線引きを黙って上書きすると、前に決めたことが消えたと気づけない。
    # 兄弟の save 系と同じく、上書きは明示しない限り拒む。
    if os.path.exists(p) and not args.force:
        fail("すでにある: {}（書き換えるなら --force）".format(p), 3)
    try:
        os.makedirs(d, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body if body.endswith("\n") else body + "\n")
    except OSError as e:
        fail("線引きを保存できない: {}".format(e))
    print(json.dumps({"scope": "written", "path": p}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("write")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--body-file", required=True)
    sp.add_argument("--force", action="store_true")

    args = p.parse_args()
    cmd_write(args, load_config(args.config))


if __name__ == "__main__":
    main()
