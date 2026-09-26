#!/usr/bin/env bash
# claude plugin eval が残した作業場所の成果物を、別の Claude（採点役）に条件ごとに判定させ、点数にする。
#
#   bash scripts/grade-eval.sh <ケースのディレクトリ> <作業場所> [期待する判定の expected.md]
#
# <作業場所> は、--keep-temp で残した一時ディレクトリ（例 /private/tmp/e-XXXX）か、
# 資料と記録を置いたディレクトリ（out/ と grill-log/ を持つもの）である。
# 採点役は Read、Glob、Grep だけを使い、写しを置いた採点用のディレクトリの中だけを読める。
# 残した作業場所の中では何も実行しない（git の設定を読ませないため）。成果物は写してから読む。
# 採点役は既定で3回、互いに独立に回し、条件ごとに多数決を取る。多数決の判定に条件の重みを掛け、
# 100点満点の点数にする。expected.md を渡すと、多数決の判定と条件ごとに突き合わせ、一致の数を出す。
#
# 環境変数: GRADE_MODEL（既定 sonnet）、GRADE_RUNS（既定 3、奇数）、GRADE_MAX_BUDGET_USD（1回あたり、既定 2）
set -euo pipefail

[ $# -ge 2 ] || { echo "使い方: bash scripts/grade-eval.sh <ケースのディレクトリ> <作業場所> [expected.md]" >&2; exit 2; }
CASE_DIR=$(cd "$1" && pwd)
KEPT=$2
EXPECTED=${3:-}
MODEL=${GRADE_MODEL:-sonnet}
RUNS=${GRADE_RUNS:-3}
BUDGET=${GRADE_MAX_BUDGET_USD:-2}
[ $((RUNS % 2)) -eq 1 ] || { echo "GRADE_RUNS は多数決が割れない奇数にする: $RUNS" >&2; exit 2; }

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

CASE_NAME=$(basename "$CASE_DIR")
RESULTS="$EVALS_DIR/results/grading"
mkdir -p "$RESULTS"
STAMP=$(date -u +%Y-%m-%dT%H-%M-%SZ)
BASE="$RESULTS/$CASE_NAME-$STAMP"

# 資料が無ければ採点役を呼ばず、すべての条件を FAIL として点数にする（0点）。
if [ ! -f "$WORK/$DOCUMENT" ]; then
  echo "判定する資料が無い: $WORK/$DOCUMENT（すべての条件を FAIL として点数にする）" >&2
  RUNS=0
fi

STAGE=$(mktemp -d "${TMPDIR:-/tmp}/grade-eval.XXXXXX")
mkdir -p "$STAGE/work" "$STAGE/materials"
[ -d "$WORK/out" ] && cp -R "$WORK/out" "$STAGE/work/out"
[ -d "$WORK/grill-log" ] && cp -R "$WORK/grill-log" "$STAGE/work/grill-log"
cp -R "$MATERIALS/." "$STAGE/materials/"

TARGET=$(printf '## この採点の対象\n\n- 判定する資料: `work/%s`\n- grill の記録: `work/%s`\n' "$DOCUMENT" "$GRILL_LOG")
CRITERIA=$(printf '%s\n\n---\n\n%s\n' "$(cat "$COMMON")" "$(grep -v '^<!-- ' "$SPECIFIC")")
PROMPT=$(printf '%s\n\n%s\n\n---\n\n%s\n' "$(cat "$BRIEF")" "$TARGET" "$CRITERIA")
printf '%s\n' "$CRITERIA" > "$BASE.criteria.md"

# 採点役は採点用のディレクトリを作業場所にし、そこから外は読めない。回ごとに独立に並べて走らせる。
pids=()
for i in $(seq 1 "$RUNS"); do
  (cd "$STAGE" && claude -p "$PROMPT" \
    --model "$MODEL" \
    --restricted --strict-mcp-config \
    --tools Read Glob Grep \
    --allowed-tools Read Glob Grep \
    --permission-mode dontAsk \
    --no-session-persistence \
    --max-budget-usd "$BUDGET" \
    --output-format json < /dev/null) > "$BASE.vote$i.json" &
  pids+=($!)
done
for pid in "${pids[@]}"; do wait "$pid"; done

python3 "$(dirname "${BASH_SOURCE[0]}")/grade_eval_score.py" "$BASE" "$RUNS" "$EXPECTED"
