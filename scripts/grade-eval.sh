#!/usr/bin/env bash
# claude plugin eval が残した作業場所の成果物を、別の Claude（採点役）に条件ごとに判定させる。
#
#   bash scripts/grade-eval.sh <ケースのディレクトリ> <作業場所> [期待する判定の expected.md]
#
# <作業場所> は、--keep-temp で残した一時ディレクトリ（例 /private/tmp/e-XXXX）か、
# 資料と記録を置いたディレクトリ（out/ と grill-log/ を持つもの）である。
# 採点役は Read、Glob、Grep だけを使い、写しを置いた採点用のディレクトリの中だけを読める。
# 残した作業場所の中では何も実行しない（git の設定を読ませないため）。成果物は写してから読む。
# expected.md を渡すと、採点役の判定と条件ごとに突き合わせ、一致の数を出す。
#
# 環境変数: GRADE_MODEL（既定 sonnet）、GRADE_MAX_BUDGET_USD（既定 2）
set -euo pipefail

[ $# -ge 2 ] || { echo "使い方: bash scripts/grade-eval.sh <ケースのディレクトリ> <作業場所> [expected.md]" >&2; exit 2; }
CASE_DIR=$(cd "$1" && pwd)
KEPT=$2
EXPECTED=${3:-}
MODEL=${GRADE_MODEL:-sonnet}
BUDGET=${GRADE_MAX_BUDGET_USD:-2}

# 共通の条件と採点役への指示は evals/criteria/ に、固有の条件はケースの grading/criteria.md にある。
# 固有の条件の先頭の注記が、共通の条件の種類と、判定する資料と記録のパスを決める。
SPECIFIC="$CASE_DIR/grading/criteria.md"
[ -f "$SPECIFIC" ] || { echo "ケースに grading/criteria.md が無い: $CASE_DIR" >&2; exit 2; }
note() { sed -n "s/^<!-- $1: \(.*\) -->\$/\1/p" "$SPECIFIC" | head -1; }
KIND=$(note common); DOCUMENT=$(note document); GRILL_LOG=$(note grill-log)
[ -n "$KIND" ] && [ -n "$DOCUMENT" ] && [ -n "$GRILL_LOG" ] || { echo "grading/criteria.md の先頭に common、document、grill-log の注記が無い" >&2; exit 2; }
EVALS_DIR=$(cd "$CASE_DIR" && while [ "$(basename "$PWD")" != evals ] && [ "$PWD" != / ]; do cd ..; done; pwd)
BRIEF="$EVALS_DIR/criteria/brief.md"
COMMON="$EVALS_DIR/criteria/$KIND.md"
[ -f "$BRIEF" ] && [ -f "$COMMON" ] || { echo "共通の指示か条件が無い: $BRIEF $COMMON" >&2; exit 2; }
# 要件と業務の分け方は、ケースの materials/ か、お題の materials/ にある。
if [ -d "$CASE_DIR/materials" ]; then MATERIALS="$CASE_DIR/materials"; else MATERIALS="$CASE_DIR/../materials"; fi
[ -f "$MATERIALS/split.md" ] || { echo "materials/split.md が無い: $MATERIALS" >&2; exit 2; }

# 残した作業場所は封じられている（mode 000）ので、読める mode に戻してから成果物の場所を決める。
if [ -d "$KEPT/sealed" ]; then
  chmod 700 "$KEPT" "$KEPT/sealed"
  WORK="$KEPT/sealed/home/cwd"
else
  WORK=$KEPT
fi
[ -f "$WORK/$DOCUMENT" ] || { echo "判定する資料が無い: $WORK/$DOCUMENT" >&2; exit 2; }

STAGE=$(mktemp -d "${TMPDIR:-/tmp}/grade-eval.XXXXXX")
mkdir -p "$STAGE/work" "$STAGE/materials"
cp -R "$WORK/out" "$STAGE/work/out"
[ -d "$WORK/grill-log" ] && cp -R "$WORK/grill-log" "$STAGE/work/grill-log"
cp -R "$MATERIALS/." "$STAGE/materials/"

CASE_NAME=$(basename "$CASE_DIR")
RESULTS="$EVALS_DIR/results/grading"
mkdir -p "$RESULTS"
STAMP=$(date -u +%Y-%m-%dT%H-%M-%SZ)
REPORT="$RESULTS/$CASE_NAME-$STAMP.md"
RAW="$RESULTS/$CASE_NAME-$STAMP.json"

TARGET=$(printf '## この採点の対象\n\n- 判定する資料: `work/%s`\n- grill の記録: `work/%s`\n' "$DOCUMENT" "$GRILL_LOG")
PROMPT=$(printf '%s\n\n%s\n\n---\n\n%s\n\n---\n\n%s\n' "$(cat "$BRIEF")" "$TARGET" "$(cat "$COMMON")" "$(grep -v '^<!-- ' "$SPECIFIC")")

# 採点役は採点用のディレクトリを作業場所にし、そこから外は読めない。
(cd "$STAGE" && claude -p "$PROMPT" \
  --model "$MODEL" \
  --restricted --strict-mcp-config \
  --tools Read Glob Grep \
  --allowed-tools Read Glob Grep \
  --permission-mode dontAsk \
  --no-session-persistence \
  --max-budget-usd "$BUDGET" \
  --output-format json < /dev/null) > "$RAW"

python3 - "$RAW" "$REPORT" "$EXPECTED" <<'PY'
import json, re, sys
raw, report, expected = sys.argv[1], sys.argv[2], sys.argv[3]
result = json.load(open(raw))
text = result.get("result") or ""
open(report, "w").write(text)
print(f"採点の報告: {report}")
print(f"費用: ${result.get('total_cost_usd', 0):.2f}  ターン: {result.get('num_turns')}  結果: {result.get('subtype')}")
got = dict(re.findall(r"^### (\S+)\s*\n判定:\s*(PASS|FAIL)", text, re.M))
if not expected:
    sys.exit(0)
want, border = {}, set()
for name, verdict, note in re.findall(r"^- (\S+): (PASS|FAIL)(（境目）)?", open(expected).read(), re.M):
    want[name] = verdict
    if note:
        border.add(name)
match = 0
for name, verdict in want.items():
    mark = "一致" if got.get(name) == verdict else "不一致"
    match += got.get(name) == verdict
    print(f"{mark}\t{name}\t期待 {verdict}\t採点役 {got.get(name, '無し')}{'（境目）' if name in border else ''}")
firm = [n for n in want if n not in border]
print(f"一致: {match}/{len(want)}（境目を除くと {sum(got.get(n) == want[n] for n in firm)}/{len(firm)}）")
PY
