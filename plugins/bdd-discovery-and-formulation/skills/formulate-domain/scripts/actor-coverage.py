#!/usr/bin/env python3
"""domain-rule資料の「コマンドとクエリ」表と「誰が行えるか」表の第1列が一致するかを検査する。

  actor-coverage.py check --file <domain-rule Markdownの絶対path>
  actor-coverage.py self-test

正本: 資料の `## コマンドとクエリ` 表と `# 誰が行えるか` 表（templateが定める見出しと第1列）。
入力: 検査対象Markdownの絶対path。
正規化: 2つの見出し配下のMarkdown表を読み、第1列の文字列を前後空白除去して集合にする。
合格述語: 両表が存在し空でなく、第1列集合が両方向で一致する。
失敗時の診断: 片方にしか無い行い名の一覧（stdoutへJSON 1行ずつ）。
exit 0 = 一致 / 1 = 不一致または表が無い / 2 = 入力を読めない。

表記ゆれ（「投稿する」と「投稿を作成する」）は不一致として報告し、同義かどうかは意味評価へ返す。
行える役割が正しいか、成立条件・常に守られること・誰が行えるか・拒むときの理由・BDDの5か所が
意味的に揃っているか、書かないもの（トークン、レート制限、管理者操作）が混ざっていないかは判定しない。
"""

import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
COMMANDS_HEADING = "コマンドとクエリ"
ACTORS_HEADING = "誰が行えるか"


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))


def sections(text):
    """見出し名 -> その配下の行（次の同階層以上の見出しまで）。コードブロック内は見出しに数えない。"""
    found = {}
    current = None
    level = 0
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if in_code:
            if current is not None:
                found[current].append(line)
            continue
        match = HEADING.match(line)
        if match:
            depth = len(match.group(1))
            title = match.group(2).strip()
            if current is not None and depth <= level:
                current = None
            if title in (COMMANDS_HEADING, ACTORS_HEADING):
                current = title
                level = depth
                found.setdefault(current, [])
            continue
        if current is not None:
            found[current].append(line)
    return found


def first_column(lines):
    """Markdown表の本文行から第1列を拾う。見出し行と区切り行は除く。"""
    rows = []
    table_started = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if table_started:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not table_started:
            table_started = True
            continue  # 見出し行
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
            continue  # 区切り行
        if cells and cells[0]:
            rows.append(cells[0])
    return rows


def check(text):
    found = sections(text)
    problems = []
    for title in (COMMANDS_HEADING, ACTORS_HEADING):
        if title not in found:
            problems.append({"kind": "見出し", "detail": f"「{title}」の見出しが無い", "howto": "templateの見出しと表を置く"})
    if problems:
        return problems
    commands = first_column(found[COMMANDS_HEADING])
    actors = first_column(found[ACTORS_HEADING])
    if not commands:
        problems.append({"kind": "表", "detail": f"「{COMMANDS_HEADING}」表に行が無い", "howto": "すべてのコマンドとクエリを載せる"})
    if not actors:
        problems.append({"kind": "表", "detail": f"「{ACTORS_HEADING}」表に行が無い", "howto": "すべてのコマンドとクエリに誰が行えるかの行を置く"})
    if problems:
        return problems
    command_set, actor_set = set(commands), set(actors)
    for missing in sorted(command_set - actor_set):
        problems.append({"kind": "誰が行えるか", "detail": f"「{ACTORS_HEADING}」に無い行い: {missing}", "howto": "同じ行い名で誰が行えるかの行を足す。表記ゆれなら第1列を揃える"})
    for extra in sorted(actor_set - command_set):
        problems.append({"kind": "コマンドとクエリ", "detail": f"「{COMMANDS_HEADING}」に無い行い: {extra}", "howto": "同じ行い名でコマンドとクエリの行を足す。表記ゆれなら第1列を揃える"})
    return problems


def cmd_check(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        emit({"error": f"資料を読めない: {exc}"})
        return 2
    problems = check(text)
    for problem in problems:
        emit(problem)
    if problems:
        emit({"error": f"{len(problems)}件の違反"})
        return 1
    emit({"check": "clean", "actions": len(set(first_column(sections(text)[COMMANDS_HEADING])))})
    return 0


def self_test():
    good = (
        "# 題材\n\n# ユビキタス言語\n\n## 業務イベント\n\n| 業務イベント | 起きた事実 | 変わる判断 |\n|---|---|---|\n| 投稿された | x | y |\n\n"
        "## コマンドとクエリ\n\n| 業務上の行い | 種別 | 起こす業務イベント |\n|---|---|---|\n| 投稿する | コマンド | 投稿された |\n| 投稿を見る | クエリ | なし |\n\n"
        "# 概念\n\n# 誰が行えるか\n\n| 業務上の行い | 種別 | 行える役割 | 行えない場合の業務上の理由 | 実現を担うもの |\n|---|---|---|---|---|\n"
        "| 投稿する | コマンド | 登録済みの利用者 | 未登録者の投稿は責任を問えない | 認証・認可 |\n| 投稿を見る | クエリ | 誰でも | なし | 業務判断 |\n\n# 業務ルール\n"
    )
    assert check(good) == [], "正例: 2行が両表にある"
    missing = good.replace("| 投稿を見る | クエリ | 誰でも | なし | 業務判断 |\n", "")
    problems = check(missing)
    assert len(problems) == 1 and "投稿を見る" in problems[0]["detail"], "反例: 誰が行えるかに無い"
    variant = good.replace("| 投稿する | コマンド | 登録済みの利用者", "| 投稿を作成する | コマンド | 登録済みの利用者")
    problems = check(variant)
    assert len(problems) == 2, "境界例: 表記ゆれは両方向の不一致として報告する"
    no_table = good.replace("# 誰が行えるか\n\n| 業務上の行い | 種別 | 行える役割 | 行えない場合の業務上の理由 | 実現を担うもの |\n|---|---|---|---|---|\n", "# 誰が行えるか\n\n")
    no_table = re.sub(r"\| 投稿する \| コマンド \| 登録済み.*\n\| 投稿を見る \| クエリ \| 誰でも.*\n", "", no_table)
    problems = check(no_table)
    assert problems and problems[0]["kind"] == "表", "反例: 表が空"
    fenced = good.replace("# 業務ルール\n", "# 業務ルール\n\n```text\n# 誰が行えるか\n| 別の行い |\n```\n")
    assert check(fenced) == [], "境界例: コードブロック内の見出しは数えない"
    emit({"self_test": "passed", "cases": 5})
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--file", required=True)
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "self-test":
        return self_test()
    return cmd_check(args.file)


if __name__ == "__main__":
    sys.exit(main())
