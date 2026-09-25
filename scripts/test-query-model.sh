#!/usr/bin/env bash
# query_model.py（model-query-data が保存したクエリデータモデルに一回かける検査）を、正例・反例で確かめる。
# fixture は scripts/fixtures/query-data-model/valid.md で、持ち主は scripts/fixtures/command-data-model/valid.md である。
# 反例は一時ディレクトリへ写した fixture を一か所だけ変えて作り、合格述語は「exit 1 と決まった診断の文言」だけにする。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
checker="$ROOT/plugins/bdd-discovery-and-formulation/skills/model-query-data/scripts/query_model.py"
fixtures="$ROOT/scripts/fixtures"
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
for cmd in python3 perl rg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[error] command $cmd が無い" >&2; exit 2; }
done
export PYTHONDONTWRITEBYTECODE=1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
doc="$work/f/query-data-model/valid.md"

fresh() { rm -rf "$work/f"; mkdir -p "$work/f"; cp -R "$fixtures/query-data-model" "$fixtures/command-data-model" "$work/f/"; }
accepts() { local name=$1; shift; python3 "$checker" check "$@" >/dev/null 2>&1 && pass "$name" || fail "$name"; }
rejects() {
  local name=$1 expected=$2; shift 2
  local output status
  output=$(python3 "$checker" check "$@" 2>&1); status=$?
  if [ "$status" -eq 1 ] && rg -F -- "$expected" <<< "$output" >/dev/null; then pass "$name"; else fail "$name（exit $status）"; fi
}
edit() { perl -0pi -e "$1" "$doc"; }

fresh; accepts "正例" "$doc"
fresh; edit 's/\| reservation_id \| room_code \| use_on \| status \|/| reservation_id | room_name | use_on | status |/'; rejects "持ち主の図に無い列を拒否" "持ち主の図に無い列を読んでいる" "$doc"
fresh; edit 's/\n\| `reservations` \| \[[^\n]*//'; rejects "読むテーブルの表に無いテーブルを拒否" "読むテーブルの表に無い" "$doc"
fresh; edit 's/\*\*`reservations`\*\*/**`entries`**/; s/\| `reservations` \|/| `entries` |/'; rejects "持ち主が分類していないテーブルを拒否" "持ち主の資料がこのテーブルを分類していない" "$doc"
fresh; edit 's#\.\./command-data-model/valid\.md#../command-data-model/none.md#'; rejects "実在しない持ち主を拒否" "持ち主の資料を読めない" "$doc"
fresh; edit 's/\*\*取得結果\*\*\n\n\| 会議室 \| 予約 \|\n\|---\|---\|\n\| A \| R-2 \|\n\| B \| R-1 \|\n//'; rejects "取得結果の無い BDD を拒否" "「**取得結果**」の行が0個ある" "$doc"
fresh; edit 's/(\*\*取得結果\*\*\n)/$1\n| 会議室 |\n|---|\n| A |\n\n$1/'; rejects "取得結果が二つある BDD を拒否" "「**取得結果**」の行が2個ある" "$doc"
fresh; edit 's/\[BDD-002\]/[BDD-001]/'; rejects "BDD 番号の重複を拒否" "BDD の番号が" "$doc"
fresh; printf '\n| 系列 | 性質 | 論理テーブル | 保存表現 | 時刻 | 変化 | 根拠 |\n|---|---|---|---|---|---|---|\n' >> "$doc"; rejects "分類の表を持つ資料を拒否" "クエリデータモデルが分類の表を持っている" "$doc"
fresh; edit 's/^## 読むテーブル$/## 予約のテーブルだけを読む/m'; accepts "見出しの文言に依らず目印で読む" "$doc"
python3 "$checker" check >/dev/null 2>&1; [ $? -eq 2 ] && pass "引数の無い呼び出しは exit 2" || fail "引数の無い呼び出しの終了code"

printf '\nquery_model.py: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
