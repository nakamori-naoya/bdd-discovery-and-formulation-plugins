#!/usr/bin/env python3
"""BDD条件マトリクスに隠れた前提がないか検査する。

  scenario_matrix.py check   < <条件マトリクスJSON>
      -> 違反をstdoutへJSON 1行ずつ出す。exit 0 = 違反なし / 1 = 違反あり（path, detail, howto） / 2 = 入力を読めない
  scenario_matrix.py self-test

基準資料: BDDの前提・トリガー・失敗理由（scenario-premises.md）が定める条件マトリクスの形。
入力: agentが同じ文脈で作った条件マトリクスJSONを標準入力で受ける。fileは介さない。
合格述語: scenarios が空でないlistで、各シナリオの kind / expected / rule / trigger / premises / note が
  種別ごとの成立条件（成功は全前提satisfied、単一失敗は対象1件unsatisfied、境界は対象1件boundary、
  相互作用は対象2件以上、失敗にはrule/source一致のnote）を満たす。
意味評価として残す範囲: 前提が業務上必要十分か、rule と source が正しい業務ルールを指すか。
"""

import argparse
import json
import re
import sys

KINDS = {"success", "single_failure", "boundary", "interaction"}
EXPECTED = {"success", "failure"}
STATES = {"satisfied", "unsatisfied", "boundary"}
TRIGGERS = {"action", "event"}
RELATIVE_LINK = re.compile(r"^\[[^\]]+\]\((?!/|https?://|file:)[^)]+#[^)]+\)$", re.I)


def problem(path, detail, howto):
    return {"path": path, "detail": detail, "howto": howto}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(data):
    problems = []
    scenarios = data.get("scenarios") if isinstance(data, dict) else None
    if not isinstance(scenarios, list) or not scenarios:
        return [problem("scenarios", "シナリオが無い", "1件以上の条件マトリクスを書く")]

    names = set()
    for index, scenario in enumerate(scenarios):
        base = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            problems.append(problem(base, "objectではない", "シナリオをobjectで書く"))
            continue
        name = scenario.get("name")
        if not nonempty(name):
            problems.append(problem(f"{base}.name", "シナリオ名が無い", "BDD本文と同じ名前を書く"))
        elif name in names:
            problems.append(problem(f"{base}.name", "シナリオ名が重複している", "一意な名前にする"))
        else:
            names.add(name)

        kind = scenario.get("kind")
        expected = scenario.get("expected")
        if kind not in KINDS:
            problems.append(problem(f"{base}.kind", f"不正な種別: {kind!r}", f"{sorted(KINDS)}から選ぶ"))
        if expected not in EXPECTED:
            problems.append(problem(f"{base}.expected", f"不正な期待結果: {expected!r}", f"{sorted(EXPECTED)}から選ぶ"))
        if not nonempty(scenario.get("rule")):
            problems.append(problem(f"{base}.rule", "対象業務ルールが無い", "BDDより上または外部正式な定義の業務ルールを書く"))

        source = scenario.get("source")
        if source is not None and (not nonempty(source) or not RELATIVE_LINK.match(source.strip())):
            problems.append(problem(f"{base}.source", "相対Markdownリンクと見出しアンカーではない", "[資料名](相対path.md#見出し)で書く"))

        trigger = scenario.get("trigger")
        if not isinstance(trigger, dict):
            problems.append(problem(f"{base}.trigger", "Whenのトリガーが無い", "actionまたはeventと本文を書く"))
        else:
            if trigger.get("kind") not in TRIGGERS:
                problems.append(problem(f"{base}.trigger.kind", "actionまたはeventではない", "Thenを発生させる業務アクションか業務イベントを選ぶ"))
            if not nonempty(trigger.get("text")):
                problems.append(problem(f"{base}.trigger.text", "When本文が無い", "Thenを発生させる一つのトリガーを書く"))

        premises = scenario.get("premises")
        if not isinstance(premises, list) or not premises:
            problems.append(problem(f"{base}.premises", "Givenに対応する必要条件が無い", "必要条件を一件ずつ書く"))
            premises = []
        texts = set()
        targets = []
        for p_index, premise in enumerate(premises):
            p_base = f"{base}.premises[{p_index}]"
            if not isinstance(premise, dict):
                problems.append(problem(p_base, "objectではない", "前提をobjectで書く"))
                continue
            text = premise.get("text")
            if not nonempty(text):
                problems.append(problem(f"{p_base}.text", "Given本文が無い", "業務条件を具体的に書く"))
            elif text in texts:
                problems.append(problem(f"{p_base}.text", "同じGivenが重複している", "一件だけ残す"))
            else:
                texts.add(text)
            if premise.get("state") not in STATES:
                problems.append(problem(f"{p_base}.state", "条件の状態が不明", f"{sorted(STATES)}から選ぶ"))
            if not isinstance(premise.get("target"), bool):
                problems.append(problem(f"{p_base}.target", "検証対象かが真偽値ではない", "trueまたはfalseで書く"))
            elif premise["target"]:
                targets.append(premise)
            if not nonempty(premise.get("source")):
                problems.append(problem(f"{p_base}.source", "入力根拠が無い", "業務ルールまたは確認済み決定を書く"))

        non_targets = [p for p in premises if isinstance(p, dict) and p.get("target") is False]
        for premise in non_targets:
            if premise.get("state") != "satisfied":
                problems.append(problem(f"{base}.premises", "検証対象以外に未成立または境界の条件がある", "検証対象以外の必要条件をすべて成立させる"))

        if kind == "success":
            if expected != "success" or targets or any(p.get("state") != "satisfied" for p in premises if isinstance(p, dict)):
                problems.append(problem(base, "成功シナリオで全必要条件が成立していない", "全条件をsatisfied、targetをfalseにする"))
        elif kind == "single_failure":
            if expected != "failure" or len(targets) != 1 or (targets and targets[0].get("state") != "unsatisfied"):
                problems.append(problem(base, "単一失敗の検証対象が一件のunsatisfiedではない", "対象一件だけをunsatisfiedにする"))
        elif kind == "boundary":
            if len(targets) != 1 or (targets and targets[0].get("state") != "boundary"):
                problems.append(problem(base, "境界の検証対象が一件のboundaryではない", "対象一件だけをboundaryにする"))
        elif kind == "interaction" and len(targets) < 2:
            problems.append(problem(base, "相互作用の検証対象が二件未満", "相互作用させる条件を二件以上明示する"))

        note = scenario.get("note")
        if expected == "failure":
            if not isinstance(note, dict):
                problems.append(problem(f"{base}.note", "失敗理由のNOTEが無い", "rule、必要ならsource、reasonを書く"))
            else:
                if note.get("rule") != scenario.get("rule"):
                    problems.append(problem(f"{base}.note.rule", "対象業務ルールと一致しない", "scenario.ruleと同じ値を書く"))
                if note.get("source") != source:
                    problems.append(problem(f"{base}.note.source", "外部参照元が一致しない", "scenario.sourceと同じ値を書く。内部ルールなら両方省略する"))
                if not nonempty(note.get("reason")):
                    problems.append(problem(f"{base}.note.reason", "拒否理由が無い", "抵触した必要条件と拒否理由を書く"))
        elif note is not None:
            problems.append(problem(f"{base}.note", "成功シナリオにNOTEがある", "成功シナリオからNOTEを削る"))
    return problems


def read_stdin_json():
    """標準入力を条件マトリクスJSONとして読む。読めなければ (None, 診断) を返す。"""
    raw = sys.stdin.read()
    if not raw.strip():
        return None, "標準入力が空。条件マトリクスJSONを標準入力で渡す"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"標準入力がJSONではない: {exc}"
    if not isinstance(data, dict):
        return None, "条件マトリクスはobjectでなければならない"
    return data, None


def cmd_check():
    data, error = read_stdin_json()
    if error:
        print(json.dumps({"error": f"条件マトリクスを読めない: {error}"}, ensure_ascii=False))
        return 2
    problems = validate(data)
    for item in problems:
        print(json.dumps(item, ensure_ascii=False))
    if problems:
        print(json.dumps({"error": f"{len(problems)}件の違反"}, ensure_ascii=False))
        return 1
    print(json.dumps({"check": "clean", "scenarios": len(data["scenarios"])}, ensure_ascii=False))
    return 0


def self_test():
    import subprocess

    good = {"scenarios": [
        {"name": "成功", "kind": "success", "expected": "success", "rule": "R",
         "trigger": {"kind": "event", "text": "受付が起きる"},
         "premises": [{"text": "Aが成立", "state": "satisfied", "target": False, "source": "業務規則"}]},
        {"name": "単一失敗", "kind": "single_failure", "expected": "failure", "rule": "R",
         "trigger": {"kind": "action", "text": "確認する"},
         "premises": [{"text": "Aが成立", "state": "satisfied", "target": False, "source": "業務規則"},
                      {"text": "Bが不成立", "state": "unsatisfied", "target": True, "source": "業務規則"}],
         "note": {"rule": "R", "reason": "Bに抵触"}},
        {"name": "境界", "kind": "boundary", "expected": "success", "rule": "R",
         "trigger": {"kind": "action", "text": "判定する"},
         "premises": [{"text": "Aが境界", "state": "boundary", "target": True, "source": "業務規則"}]},
        {"name": "組合せ", "kind": "interaction", "expected": "success", "rule": "R",
         "trigger": {"kind": "event", "text": "同時に起きる"},
         "premises": [{"text": "A", "state": "satisfied", "target": True, "source": "業務規則"},
                      {"text": "B", "state": "satisfied", "target": True, "source": "業務規則"}]},
    ]}
    assert validate(good) == [], "正例: 4種別が通る"
    implicit = json.loads(json.dumps(good, ensure_ascii=False))
    implicit["scenarios"][1]["premises"][0]["state"] = "unsatisfied"
    assert validate(implicit), "反例: 検証対象以外の未成立を拒否"
    assert validate({"scenarios": []}), "反例: シナリオ0件"

    def run(stdin_text):
        return subprocess.run([sys.executable, __file__, "check"], input=stdin_text, text=True, capture_output=True)

    assert run("").returncode == 2, "境界例: 空stdinはexit 2"
    assert run("{not json").returncode == 2, "境界例: 不正JSONはexit 2"
    assert run("[]").returncode == 2, "境界例: objectでない入力はexit 2"
    assert run(json.dumps(good, ensure_ascii=False)).returncode == 0, "正例: stdin経由で通る"
    assert run(json.dumps(implicit, ensure_ascii=False)).returncode == 1, "反例: stdin経由で違反はexit 1"
    old_form = subprocess.run([sys.executable, __file__, "check", "--file", "x"], text=True, capture_output=True)
    assert old_form.returncode == 2, "境界例: 旧引数 --file はargparseが拒否する"
    print(json.dumps({"self_test": "passed", "cases": 9}, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "self-test":
        return self_test()
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
