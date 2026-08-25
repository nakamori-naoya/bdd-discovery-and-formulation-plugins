#!/usr/bin/env python3
"""業務の話に実装の関心が混ざっていないかを機械で見て、線引きを保存する。

**「実装語を書かない」を散文の注意だけで守れたことは無い。**
書けてしまう限り必ず混ざるので、書けなくする。

  check.py scan --file <path> [--allow <語>]...
      -> 実装の語を拾う。1つでもあれば異常終了する

  check.py write --config <json|path> --topic <題材> --body-file <path> [--allow <語>]... [--force]
      -> 必須の節と実装語を検査し、通ったものだけ scope_dir へ保存する

  check.py terms
      -> 拾う語と、業務の言葉への言い換え先を出す
"""

import argparse
import json
import os
import re
import subprocess
import sys

# 拾う語 → 業務の言葉へどう言い換えるか。
# **ここが正本である。** 文書側へ書き写すと、片方だけ増えて食い違う。
TERMS = {
    "保存の都合": (
        ["テーブル", "カラム", "スキーマ", "インデックス", "外部キー", "主キー",
         "マイグレーション", "SQL", "RDB", "データベース", "レコード"],
        "業務上どういう状態になったかへ言い換える",
    ),
    "境界の都合": (
        ["エンドポイント", "gRPC", "RPC", "REST", "HTTP", "リクエスト", "レスポンス",
         "ペイロード", "JSON", "proto", "API", "ステータスコード", "エラーコード"],
        "誰が誰へ何を求め、業務として何が返るかへ言い換える",
    ),
    "画面の都合": (
        ["画面", "ボタン", "押下", "ダイアログ", "モーダル", "入力欄", "プルダウン",
         "URL", "画面遷移", "タブ"],
        "その操作で業務上何が起きたかへ言い換える",
    ),
    "コードの都合": (
        ["クラス", "インターフェース", "メソッド", "関数", "enum", "変数",
         "リポジトリ実装", "DTO", "フィールド"],
        "業務の概念とその属性へ言い換える",
    ),
    "組み立ての都合": (
        ["ユースケース", "アプリケーションサービス", "コントローラ", "ハンドラ",
         "サービス層", "バッチ", "キャッシュ", "キュー", "デプロイ"],
        "業務のどの決まりを表しているかへ言い換える。表せないなら業務の話ではない",
    ),
}
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


def find_hits(text, allow):
    """行番号つきで実装語を拾う。引用（コードフェンス内）も見る。

    フェンスの中だけ許すと、そこへ実装の話が溜まる。
    """
    allowed = {a.strip() for a in allow if a.strip()}
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        # 言い換え先を示す表そのものは検査対象にしない（この規律を説明できなくなる）。
        if line.lstrip().startswith("<!--") or line.lstrip().startswith("[//]:"):
            continue
        for kind, (terms, howto) in TERMS.items():
            for t in terms:
                if t in allowed:
                    continue
                if t in line:
                    hits.append({"line": i, "term": t, "kind": kind,
                                 "howto": howto, "text": line.strip()[:120]})
    return hits


def report(hits):
    for h in hits:
        print(json.dumps(h, ensure_ascii=False))
    print(json.dumps({
        "error": "実装の関心が {} 箇所混ざっている".format(len(hits)),
        "hint": "業務の言葉へ言い換えるか、スコープ外として理由つきで落とす。"
                "業務語として正しい場合だけ --allow で明示する",
    }, ensure_ascii=False))


def cmd_scan(args, _cfg=None):
    hits = find_hits(read_body(args.file), args.allow)
    if hits:
        report(hits)
        sys.exit(1)
    print(json.dumps({"scan": "clean", "file": args.file}, ensure_ascii=False))


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
    hits = find_hits(body, args.allow)
    if hits:
        report(hits)
        sys.exit(1)

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


def cmd_terms(_args, _cfg=None):
    for kind, (terms, howto) in TERMS.items():
        print(json.dumps({"kind": kind, "terms": terms, "howto": howto},
                         ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan")
    sp.add_argument("--file", required=True)
    sp.add_argument("--allow", action="append", default=[])

    sp = sub.add_parser("write")
    sp.add_argument("--config", required=True)
    sp.add_argument("--topic", required=True)
    sp.add_argument("--body-file", required=True)
    sp.add_argument("--allow", action="append", default=[])
    sp.add_argument("--force", action="store_true")

    sub.add_parser("terms")

    args = p.parse_args()
    if args.cmd == "write":
        cmd_write(args, load_config(args.config))
    elif args.cmd == "scan":
        cmd_scan(args)
    else:
        cmd_terms(args)


if __name__ == "__main__":
    main()
