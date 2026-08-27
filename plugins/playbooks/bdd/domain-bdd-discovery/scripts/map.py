#!/usr/bin/env python3
"""ユビキタス言語・ルール・振る舞い断面・具体例・疑問を1枚のマップへ積む。

中心となる成果物は `render --format discovery` で出す「業務振る舞い発見資料」である。
業務イベントと事前状態を起点に、役割、条件、判断、結果、次状態、引継ぎを残す。
Given/When/Then は発見資料から定式化工程へ渡すための草稿にすぎない。

  map.py term    --config <json|path> --topic <題材> --name <ユビキタス言語の候補> --meaning <使われ方と境界>
  map.py rule    --config <json|path> --topic <題材> --statement <ルール>
  map.py behavior --config <json|path> --topic <題材> --rule <RU-001> --title <見出し>
                  --goal <目的> --actor <起点役割> --collaborators <協働役割|なし>
                  --prior-state <事前状態> --event <業務イベント> --condition <条件|追加条件なし>
                  --decision <業務判断> --decision-owner <判断権者> --outcome <観測できる結果>
                  --next-state <次状態> --handoff <引継ぎ|なし>
                  --downstream-event <後続イベント|なし> [--variation <種別>]
  map.py example --config <json|path> --topic <題材> --rule <RU-001> --title <見出し>
                 --context <前提> --action <行い> --outcome <結果> [--source <出所>]
  map.py question --config <json|path> --topic <題材> --text <問い> --owner <回答責任者>
                  [--about <RU-001|EX-001>]
  map.py answer  --config <json|path> --topic <題材> --id <QU-001> --answer <答え>
  map.py accept  --config <json|path> --topic <題材> --id <EX-001>
  map.py reject  --config <json|path> --topic <題材> --id <EX-001> --why <理由>
  map.py status  --config <json|path> --topic <題材>
  map.py exclude --config <json|path> --topic <題材> --text <技術事項> --destination <移す先>
  map.py render  --config <json|path> --topic <題材> [--format discovery|map|gherkin]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
TOPIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ID_RE = re.compile(r"^(TM|RU|BH|EX|QU|XT)-\d{3}$")


def fail(msg, code=2):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def load_config(raw):
    raw = (raw or "").strip()
    if raw.startswith("{"):
        return json.loads(raw)
    try:
        r = subprocess.run(["yq", "-o=json", "-I=0", ".", raw], capture_output=True,
                           text=True, timeout=10, check=True)
        return json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        fail("--config が読めない: {}".format(e))


def safe_topic(t):
    if not TOPIC_RE.match(t or "") or ".." in (t or ""):
        fail("--topic が不正（英数と . _ - のみ、128文字まで）: {!r}".format(t))
    return t


def playbook_config(cfg):
    value = cfg.get("playbook")
    return value if isinstance(value, dict) else cfg


def focus_of(cfg):
    focus = playbook_config(cfg).get("focus") or ""
    if focus != "domain":
        fail("playbookのfocusが不正: {!r}".format(focus))
    return focus


def map_path(cfg, topic):
    d = playbook_config(cfg).get("map_dir") or ""
    if not d:
        fail("playbookに map_dir が無い")
    if not os.path.isabs(d) and cfg.get("repo_root"):
        d = os.path.join(cfg["repo_root"], d)
    return os.path.join(d, "{}.jsonl".format(topic))


def read_map(cfg, topic):
    p = map_path(cfg, topic)
    if not os.path.exists(p):
        return []
    rows = []
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError as e:
        fail("マップを読めない: {}".format(e))
    return rows


def write_map(cfg, topic, rows):
    p = map_path(cfg, topic)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except OSError as e:
        fail("マップへ書けない: {}".format(e))
    return p


def next_id(rows, prefix):
    n = sum(1 for r in rows if r.get("kind") == prefix)
    labels = {"term": "TM", "rule": "RU", "behavior": "BH", "example": "EX",
              "question": "QU", "exclusion": "XT"}
    return "{}-{:03d}".format(labels[prefix], n + 1)


def now():
    return datetime.now(JST).isoformat(timespec="seconds")


def require(value, label, why):
    if not (value or "").strip():
        fail("{} が空。{}".format(label, why))
    return value.strip()


def cmd_term(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    name = require(args.name, "--name", "ユビキタス言語の候補名が無い")
    meaning = require(args.meaning, "--meaning", "業務の人が同じ意味で使える定義が無い")
    if any(r.get("kind") == "term" and r.get("name") == name for r in rows):
        fail("同じユビキタス言語の候補がすでにある: {}".format(name), 3)
    entry = {"ts": now(), "kind": "term", "id": next_id(rows, "term"), "topic": topic,
             "name": name, "meaning": meaning}
    rows.append(entry)
    print(json.dumps({"term": entry["id"], "path": write_map(cfg, topic, rows)},
                     ensure_ascii=False))


def cmd_rule(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    statement = require(args.statement, "--statement", "ルールの無いマップは、例を束ねる先が無い")
    if any(r.get("kind") == "rule" and r.get("statement") == statement for r in rows):
        fail("同じルールがすでにある: {}".format(statement), 3)
    entry = {"ts": now(), "kind": "rule", "id": next_id(rows, "rule"),
             "topic": topic, "statement": statement}
    rows.append(entry)
    print(json.dumps({"rule": entry["id"], "path": write_map(cfg, topic, rows)},
                     ensure_ascii=False))


def cmd_behavior(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    if not ID_RE.match(args.rule or "") or not any(
            r.get("kind") == "rule" and r.get("id") == args.rule for r in rows):
        fail("--rule が既存のルールを指していない: {!r}".format(args.rule))
    fields = {
        "title": (args.title, "見出しが無い"),
        "goal": (args.goal, "役割が達成したい業務目的が無い"),
        "actor": (args.actor, "振る舞いを起動する業務上の役割が無い"),
        "collaborators": (args.collaborators, "協働役割が無い場合も「なし」と明記する"),
        "prior_state": (args.prior_state, "事前の業務状態が無い"),
        "business_event": (args.event, "判断を必要にした業務上の出来事が無い"),
        "condition": (args.condition, "結果を分ける条件が無い場合も「追加条件なし」と明記する"),
        "decision": (args.decision, "出来事に対する業務判断が無い"),
        "decision_owner": (args.decision_owner, "誰の権限で判断するかが無い"),
        "outcome": (args.outcome, "業務上観測できる結果が無い"),
        "next_state": (args.next_state, "判断後の業務状態が無い"),
        "handoff": (args.handoff, "引継ぎが無い場合も「なし」と明記する"),
        "downstream_event": (args.downstream_event, "後続イベントが無い場合も「なし」と明記する"),
    }
    values = {key: require(value, "--" + key.replace("_", "-"), why)
              for key, (value, why) in fields.items()}
    entry = {"ts": now(), "kind": "behavior", "id": next_id(rows, "behavior"),
             "topic": topic, "rule": args.rule, **values,
             "variation": args.variation, "status": "candidate",
             "source": (args.source or "").strip(), "focus": focus_of(cfg)}
    rows.append(entry)
    print(json.dumps({"behavior": entry["id"], "status": "candidate",
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def cmd_example(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    if not ID_RE.match(args.rule or "") or not any(
            r.get("kind") == "rule" and r.get("id") == args.rule for r in rows):
        fail("--rule が既存のルールを指していない: {!r}".format(args.rule))
    title = require(args.title, "--title", "見出しの無い例は、後から何の話か分からない")
    # 前提は自明に見えても省略しない。見落とした前提が、そのまま仕様の穴になる。
    context = require(args.context, "--context",
                      "前提の無い例は、読む人がそれぞれ別の初期状態を思い浮かべる")
    action = require(args.action, "--action", "何をしたのかが無い")
    outcome = require(args.outcome, "--outcome", "何が起きるべきかが無い")
    entry = {"ts": now(), "kind": "example", "id": next_id(rows, "example"), "topic": topic,
             "rule": args.rule, "title": title, "context": context, "action": action,
             "outcome": outcome, "status": "candidate", "source": (args.source or "").strip(),
             "focus": focus_of(cfg)}
    rows.append(entry)
    print(json.dumps({"example": entry["id"], "status": "candidate",
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def cmd_question(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    text = require(args.text, "--text", "問いの本文が無い")
    # 答える人が決まっていない問いは、誰も答えないまま残る。
    owner = require(args.owner, "--owner", "答える責任者の決まっていない問いは、宙に浮いたまま残る")
    about = (args.about or "").strip()
    if about and not any(r.get("id") == about for r in rows):
        fail("--about が既存の項目を指していない: {!r}".format(about))
    entry = {"ts": now(), "kind": "question", "id": next_id(rows, "question"), "topic": topic,
             "text": text, "owner": owner, "about": about, "status": "open", "answer": ""}
    rows.append(entry)
    print(json.dumps({"question": entry["id"], "owner": owner,
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def cmd_exclude(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    text = require(args.text, "--text", "業務資料から外す技術事項が無い")
    destination = require(args.destination, "--destination", "技術事項を検討する別資料の行き先が無い")
    entry = {"ts": now(), "kind": "exclusion", "id": next_id(rows, "exclusion"),
             "topic": topic, "text": text, "destination": destination}
    rows.append(entry)
    print(json.dumps({"exclusion": entry["id"], "path": write_map(cfg, topic, rows)},
                     ensure_ascii=False))


def cmd_answer(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    hit = [r for r in rows if r.get("kind") == "question" and r.get("id") == args.id]
    if not hit:
        fail("その問いが無い: {}".format(args.id))
    answer = require(args.answer, "--answer", "答えの本文が無い")
    hit[0]["status"] = "answered"
    hit[0]["answer"] = answer
    hit[0]["answered_at"] = now()
    print(json.dumps({"question": args.id, "status": "answered",
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def open_questions_for(rows, item):
    """その候補と、それが説明するルールに紐づく、未回答の問い。"""
    targets = {item["id"], item.get("rule")}
    return [r for r in rows if r.get("kind") == "question"
            and r.get("status") == "open" and r.get("about") in targets]


def cmd_accept(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    hit = [r for r in rows if r.get("kind") in ("behavior", "example") and r.get("id") == args.id]
    if not hit:
        fail("その振る舞い断面または具体例が無い: {}".format(args.id))
    ex = hit[0]
    pend = open_questions_for(rows, ex)
    if pend:
        # 未回答の問いを抱えたまま厳密化へ進むと、穴を残したまま形だけ整う。
        fail("未回答の問いが {} 件残っている: {}".format(
            len(pend), ", ".join("{}({})".format(q["id"], q["owner"]) for q in pend)), 3)
    ex["status"] = "accepted"
    ex["accepted_at"] = now()
    print(json.dumps({"behavior" if ex.get("kind") == "behavior" else "example": args.id,
                      "status": "accepted",
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def cmd_reject(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    hit = [r for r in rows if r.get("kind") in ("behavior", "example") and r.get("id") == args.id]
    if not hit:
        fail("その振る舞い断面または具体例が無い: {}".format(args.id))
    item = hit[0]
    item["status"] = "rejected"
    item["why_rejected"] = require(args.why, "--why", "落とした理由が無いと、同じ候補がまた出てくる")
    print(json.dumps({"behavior" if item.get("kind") == "behavior" else "example": args.id,
                      "status": "rejected",
                      "path": write_map(cfg, topic, rows)}, ensure_ascii=False))


def cmd_status(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    if not rows:
        fail("マップが空: {}".format(map_path(cfg, topic)), 3)
    rules = [r for r in rows if r.get("kind") == "rule"]
    behaviors = [r for r in rows if r.get("kind") == "behavior"]
    examples = [r for r in rows if r.get("kind") == "example"]
    questions = [r for r in rows if r.get("kind") == "question"]
    open_q = [q for q in questions if q.get("status") == "open"]
    bare = [r["id"] for r in rules
            if not [e for e in behaviors + examples if e.get("rule") == r["id"]
                    and e.get("status") != "rejected"]]
    accepted = [e for e in behaviors + examples if e.get("status") == "accepted"]
    print(json.dumps({
        "topic": topic, "focus": focus_of(cfg),
        "rules": len(rules), "behaviors": len(behaviors), "examples": len(examples),
        "accepted": len(accepted),
        "questions_open": len(open_q),
        "rules_without_example": bare,
        "open_question_owners": sorted({q["owner"] for q in open_q}),
        # 完了は網羅ではなく合意である。ここは判断材料であって、合否ではない。
        "ready_for_formulation": len(accepted),
    }, ensure_ascii=False))
    if bare:
        print(json.dumps({"warning": "具体例の無いルールがある", "rules": bare},
                         ensure_ascii=False), file=sys.stderr)
    if open_q:
        print(json.dumps({"warning": "未回答の問いがある",
                          "questions": [{"id": q["id"], "owner": q["owner"]} for q in open_q]},
                         ensure_ascii=False), file=sys.stderr)


def cmd_render(args, cfg):
    topic = safe_topic(args.topic)
    rows = read_map(cfg, topic)
    if not rows:
        fail("マップが空: {}".format(map_path(cfg, topic)), 3)
    rules = [r for r in rows if r.get("kind") == "rule"]
    terms = [r for r in rows if r.get("kind") == "term"]
    behaviors = [r for r in rows if r.get("kind") == "behavior"]
    examples = [r for r in rows if r.get("kind") == "example"]
    questions = [r for r in rows if r.get("kind") == "question"]
    exclusions = [r for r in rows if r.get("kind") == "exclusion"]

    def cell(s):
        return str(s or "").replace("|", "\\|").replace("\n", "<br>")

    if args.format == "gherkin":
        out = ["# {} — 探索の草稿".format(topic), "",
               "# **これは草稿である。** 文言は定式化の工程で厳密にする。", ""]
        for r in rules:
            out += ["ルール: {}".format(r["statement"]), ""]
            for b in [x for x in behaviors if x.get("rule") == r["id"]
                      and x.get("status") != "rejected"]:
                mark = "" if b.get("status") == "accepted" else "  # 未採用"
                out += ["  シナリオ: {}{}".format(b["title"], mark),
                        "    前提 {}、かつ {}".format(b["prior_state"], b["condition"]),
                        "    もし {}（起点役割: {}）".format(b["business_event"], b["actor"]),
                        "    ならば 業務判断は「{}」となり、{}。次状態は{}".format(
                            b["decision"], b["outcome"], b["next_state"]), ""]
            for e in [x for x in examples if x.get("rule") == r["id"]
                      and x.get("status") != "rejected"]:
                mark = "" if e.get("status") == "accepted" else "  # 未採用"
                out += ["  シナリオ: {}{}".format(e["title"], mark),
                        "    前提 {}".format(e["context"]),
                        "    もし {}".format(e["action"]),
                        "    ならば {}".format(e["outcome"]), ""]
        open_q = [q for q in questions if q.get("status") == "open"]
        if open_q:
            out += ["# 未回答の問い（答えが出るまで、この草稿は確定ではない）"]
            out += ["#   {} {} — {}".format(q["id"], q["text"], q["owner"]) for q in open_q]
        print("\n".join(out))
        return

    if args.format == "discovery":
        label = {"candidate": "候補", "accepted": "合意済み", "rejected": "取り下げ"}
        variation = {"typical": "典型", "alternative": "代替", "rejection": "拒否"}
        active_behaviors = [b for b in behaviors if b.get("status") != "rejected"]
        rejected_behaviors = [b for b in behaviors if b.get("status") == "rejected"]
        out = ["# 業務振る舞い発見資料 — {}".format(topic), "",
               "> BDDへ定式化する前に、業務の言葉で判断の構造と役割間の協働を合意する資料。", "",
               "## ユビキタス言語", "", "| 言葉 | この文脈での使われ方と境界 |", "|---|---|"]
        out += (["| {} | {} |".format(cell(t["name"]), cell(t["meaning"])) for t in terms]
                or ["| — | **未整理** |"])
        out += ["", "## 業務ルール", ""]
        out += (["- **{}** {}".format(r["id"], r["statement"]) for r in rules]
                or ["- **未整理**"])
        out += ["", "## アクターと協働", "",
                "| 振る舞い | 起点役割と目的 | 協働役割 | 判断権者 | 引継ぎ |",
                "|---|---|---|---|---|"]
        out += (["| {} | {}：{} | {} | {} | {} |".format(
                    b["id"], cell(b["actor"]), cell(b["goal"]), cell(b["collaborators"]),
                    cell(b["decision_owner"]), cell(b["handoff"])) for b in active_behaviors]
                or ["| — | **未整理** | | | |"])
        out += ["", "## 振る舞い断面", ""]
        if not active_behaviors:
            out += ["**未整理。** 業務イベントと事前状態から振る舞いを発見する。", ""]
        for b in active_behaviors:
            out += ["### {} {}（{}・{}）".format(
                        b["id"], b["title"], variation.get(b.get("variation"), "?"),
                        label.get(b.get("status"), "?")), "",
                    "`{} + {} + {} + {} → {} → {} + {} + {} + {}`".format(
                        b["actor"], b["prior_state"], b["business_event"], b["condition"],
                        b["decision"], b["outcome"], b["next_state"], b["handoff"],
                        b["downstream_event"]), "",
                    "- 目的: {}".format(b["goal"]),
                    "- 協働する役割: {}".format(b["collaborators"]),
                    "- 判断権者: {}".format(b["decision_owner"]),
                    "- 根拠ルール: {}".format(b["rule"]), ""]
        out += ["## 状態と業務イベント", "",
                "| 振る舞い | 事前状態 | 業務イベント | 条件 | 判断 | 次状態 | 後続イベント |",
                "|---|---|---|---|---|---|---|"]
        out += (["| {} | {} | {} | {} | {} | {} | {} |".format(
                    b["id"], cell(b["prior_state"]), cell(b["business_event"]),
                    cell(b["condition"]), cell(b["decision"]), cell(b["next_state"]),
                    cell(b["downstream_event"])) for b in active_behaviors]
                or ["| — | **未整理** | | | | | |"])
        out += ["", "## 代表BDD", ""]
        accepted = [b for b in behaviors if b.get("status") == "accepted"]
        if not accepted:
            out += ["- 合意済みの振る舞い断面はまだ無い。", ""]
        for b in accepted:
            out += ["### {} {}".format(b["id"], b["title"]), "",
                    "- Given: {}、かつ {}".format(b["prior_state"], b["condition"]),
                    "- When: {}（起点役割: {}）".format(b["business_event"], b["actor"]),
                    "- Then: 業務判断は「{}」となり、{}。次状態は{}".format(
                        b["decision"], b["outcome"], b["next_state"]), ""]
        if rejected_behaviors:
            out += ["## 取り下げた振る舞い", "",
                    "> 前提条件が抽象的で、異なるチケット構成を混同したため、主表から外した履歴。", "",
                    "| ID | 見出し | 取り下げ理由 |", "|---|---|---|"]
            out += ["| {} | {} | {} |".format(
                b["id"], cell(b["title"]), cell(b.get("why_rejected") or "—"))
                for b in rejected_behaviors]
            out.append("")
        out += ["## 未回答の問い", "", "| ID | 問い | 対象 | 回答責任者 | 状態 |",
                "|---|---|---|---|---|"]
        out += (["| {} | {} | {} | {} | {} |".format(
                    q["id"], cell(q["text"]), q.get("about") or "—", cell(q["owner"]),
                    "未回答" if q.get("status") == "open" else "回答済み") for q in questions]
                or ["| — | なし | | | |"])
        out += ["", "## この資料に書かないもの", "",
                "| 技術事項 | 検討する別資料 |", "|---|---|"]
        out += (["| {} | {} |".format(cell(x["text"]), cell(x["destination"])) for x in exclusions]
                or ["| API、DTO、通信・保存方式などの実現方法 | 技術設計資料 |"])
        out.append("")
        print("\n".join(out))
        return

    label = {"candidate": "候補", "accepted": "採用", "rejected": "取り下げ"}
    out = ["# 実例マップ — {}（焦点: {}）".format(topic, focus_of(cfg)), ""]
    for r in rules:
        out += ["## {} {}".format(r["id"], r["statement"]), "",
                "| ID | 見出し | 前提 | 行い | 結果 | 状態 |", "|---|---|---|---|---|---|"]
        mine = [x for x in behaviors + examples if x.get("rule") == r["id"]]
        if not mine:
            out += ["| — | **具体例が無い** | | | | |"]
        for e in mine:
            context = e.get("context") or "{} / {}".format(e["prior_state"], e["condition"])
            action = e.get("action") or "{}: {}".format(e["actor"], e["business_event"])
            outcome = e.get("outcome", "")
            out.append("| {} | {} | {} | {} | {} | {} |".format(
                e["id"], cell(e["title"]), cell(context), cell(action),
                cell(outcome), label.get(e.get("status"), "?")))
        out.append("")
    out += ["## 疑問", "", "| ID | 問い | 対象 | 回答責任者 | 状態 |", "|---|---|---|---|---|"]
    if not questions:
        out += ["| — | なし | | | |"]
    for q in questions:
        out.append("| {} | {} | {} | {} | {} |".format(
            q["id"], cell(q["text"]), q.get("about") or "—", cell(q["owner"]),
            "未回答" if q.get("status") == "open" else "回答済み"))
    out.append("")
    print("\n".join(out))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--config", required=True)
        sp.add_argument("--topic", required=True)
        return sp

    sp = common(sub.add_parser("term"))
    sp.add_argument("--name", required=True); sp.add_argument("--meaning", required=True)
    sp = common(sub.add_parser("rule")); sp.add_argument("--statement", required=True)
    sp = common(sub.add_parser("behavior"))
    for opt in ("--rule", "--title", "--goal", "--actor", "--collaborators", "--prior-state",
                "--event", "--condition", "--decision", "--decision-owner", "--outcome",
                "--next-state", "--handoff", "--downstream-event"):
        sp.add_argument(opt, required=True)
    sp.add_argument("--variation", choices=("typical", "alternative", "rejection"), default="typical")
    sp.add_argument("--source", default="")
    sp = common(sub.add_parser("example"))
    for opt in ("--rule", "--title", "--context", "--action", "--outcome"):
        sp.add_argument(opt, required=True)
    sp.add_argument("--source", default="")
    sp = common(sub.add_parser("question"))
    sp.add_argument("--text", required=True); sp.add_argument("--owner", required=True)
    sp.add_argument("--about", default="")
    sp = common(sub.add_parser("answer"))
    sp.add_argument("--id", required=True); sp.add_argument("--answer", required=True)
    sp = common(sub.add_parser("accept")); sp.add_argument("--id", required=True)
    sp = common(sub.add_parser("reject"))
    sp.add_argument("--id", required=True); sp.add_argument("--why", required=True)
    sp = common(sub.add_parser("exclude"))
    sp.add_argument("--text", required=True); sp.add_argument("--destination", required=True)
    common(sub.add_parser("status"))
    sp = common(sub.add_parser("render"))
    sp.add_argument("--format", choices=("discovery", "map", "gherkin"), default="discovery")

    args = p.parse_args()
    cfg = load_config(args.config)
    {"term": cmd_term, "rule": cmd_rule, "behavior": cmd_behavior, "example": cmd_example,
     "question": cmd_question, "answer": cmd_answer, "exclude": cmd_exclude,
     "accept": cmd_accept, "reject": cmd_reject, "status": cmd_status,
     "render": cmd_render}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
