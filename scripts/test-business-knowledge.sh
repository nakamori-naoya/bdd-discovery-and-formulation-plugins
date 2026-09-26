#!/usr/bin/env bash
# business_knowledge.py（write-business-knowledge が保存した業務知識に一回かける検査）を、正例・反例で確かめる。
# fixture は scripts/fixtures/business-knowledge/ にあり、反例は一時ディレクトリへ写した fixture を一か所だけ変えて作る。
# 反例の合格述語は「検査が違反として exit 1 を返し、診断に決まった文言が出る」だけにする。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
checker="$ROOT/plugins/bdd-discovery-and-formulation/skills/write-business-knowledge/scripts/business_knowledge.py"
fixtures="$ROOT/scripts/fixtures/business-knowledge"
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
for cmd in python3 perl rg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[error] command $cmd が無い" >&2; exit 2; }
done
export PYTHONDONTWRITEBYTECODE=1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
owner="$work/k/予約/business-knowledge.md"
user="$work/k/入室/business-knowledge.md"

fresh() { rm -rf "$work/k"; mkdir -p "$work/k"; cp -R "$fixtures"/. "$work/k/"; }
accepts() { local name=$1; shift; python3 "$checker" check "$@" >/dev/null 2>&1 && pass "$name" || fail "$name"; }
rejects() {
  local name=$1 expected=$2; shift 2
  local output status mode=check
  if [ "$1" = check-set ]; then mode=check-set; shift; fi
  output=$(python3 "$checker" "$mode" "$@" 2>&1); status=$?
  if [ "$status" -eq 1 ] && rg -F -- "$expected" <<< "$output" >/dev/null; then pass "$name"; else fail "$name（exit $status）"; fi
}
edit() { perl -0pi -e "$2" "$1"; }

fresh; accepts "持ち主と参照する資料の組の正例" "$owner" "$user"
fresh; accepts "参照する資料だけでも持ち主をリンクから読む" "$user"
fresh; edit "$owner" 's/\| 予約する \| Reserve \| コマンド \|/| 予約する | Reserve | 手続き |/'; rejects "種類の許可値の外を拒否" "許可値ではない: 手続き" "$owner"
fresh; edit "$owner" 's/(\| 予約 \| Reservation \| 業務用語 \| この資料 \|\n)/$1| 予約 | Booking | 概念 | この資料 |\n/'; rejects "同じ言葉の二行を拒否" "同じ業務の言葉が表に二行ある" "$owner"
fresh; edit "$user" 's/\| 予約 \| Reservation \|/| 予約 | Booking |/'; rejects "持ち主と英名が違う参照を拒否" "持ち主の資料と英名か種類が違う" "$user"
fresh; edit "$user" 's#\.\./予約/business-knowledge\.md#../無い/business-knowledge.md#'
output=$(python3 "$checker" check "$user" 2>&1); status=$?
[ "$status" -eq 0 ] && rg -F '"unverified"' <<< "$output" >/dev/null && pass "まだ無い持ち主は未確認として報告し、合否に数えない" || fail "まだ無い持ち主の扱い（exit $status）"
fresh; edit "$user" 's/\| 入室する \| Enter \| コマンド \|/| 入室する | Enter | 手続き |/'; accepts "残りの引数の資料の違反では判定する資料を落とさない" "$owner" "$user"
fresh; edit "$user" 's/\| 予約 \| Reservation \| 業務用語 \| \[[^\n]*/| 予約 | Reservation | 業務用語 | この資料 |/'; rejects "隣の資料も同じ言葉を決めていれば判定する資料で拒否" "同じ言葉を隣の資料も決めている" "$owner" "$user"
fresh; edit "$user" 's/\| 入室した \| Entered \|/| 入室した | Reserved |/'; rejects "隣の資料で同じ英名が違う言葉に付けば判定する資料で拒否" "英名 Reserved が隣の資料で別の言葉" "$owner" "$user"
fresh; edit "$owner" 's/---\ntitle: 予約\n---\n//'; rejects "先頭の三行が無い状態遷移図を拒否" "状態遷移図の先頭が" "$owner"
fresh; edit "$owner" 's/\[BDD-002\]/[BDD-001]/'; rejects "BDD 番号の重複を拒否" "BDD の番号が" "$owner"
fresh; edit "$owner" 's/\[BDD-002\]/[BDD-2]/'; rejects "3桁未満の BDD 番号を拒否" "3桁以上の数字" "$owner"
fresh; edit "$owner" 's/Rule: 本人ではない/Rule: 他人の予約/'; rejects "宣言に無い Rule を拒否" "拒む理由: <名前>」のどれとも一致しない" "$owner"
fresh; edit "$owner" 's/^## 予約$/## 予約は取り消すまで続く/m'; accepts "見出しの文言に依らず目印で読む" "$owner"
fresh; edit "$owner" 's/\| 予約 \| Reservation \|/| 予約 | ReservationID |/'; rejects "大文字が続く英名を拒否" "先頭だけを大文字にした形ではない" "$owner"
fresh; edit "$user" 's/\| 予約 \| Reservation \| 業務用語 \| \[予約の業務知識\]\(\.\.\/予約\/business-knowledge\.md\)/| 予約 | 未定 | 業務用語 | [予約の業務知識](..\/無い\/business-knowledge.md)/'
output=$(python3 "$checker" check "$user" 2>&1); status=$?
[ "$status" -eq 0 ] && rg -F '"unverified"' <<< "$output" >/dev/null && pass "持ち主の資料が無い間の未定は未確認として通す" || fail "持ち主の資料が無い間の未定（exit $status）"
rejects "集合の検査は残った未確認を違反に数える" "集合がそろった後も持ち主の資料が無い" check-set "$owner" "$user"
fresh; edit "$user" 's/\| 予約 \| Reservation \|/| 予約 | 未定 |/'; rejects "持ち主の資料があるのに残った未定を拒否" "英名が「未定」のまま残っている" "$user"
fresh; edit "$owner" 's/\| 予約 \| Reservation \|/| 予約 | 未定 |/'; rejects "この資料が決める語の未定を拒否" "この資料が決める語の英名が「未定」である" "$owner"
fresh; python3 "$checker" check-set "$owner" "$user" >/dev/null 2>&1 && pass "そろった集合の検査の正例" || fail "そろった集合の検査の正例"
python3 "$checker" check >/dev/null 2>&1; [ $? -eq 2 ] && pass "引数の無い呼び出しは exit 2" || fail "引数の無い呼び出しの終了code"

printf '\nbusiness_knowledge.py: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
