#!/usr/bin/env bash
# immutable_model.py（model-logical-data が保存した論理データモデル資料に一回かける検査）を、正例・反例・境界例で確かめる。
# fixture は scripts/fixtures/logical-data-model/ にあり、反例はそこから一行だけ変えて作る。
# 反例の合格述語は「検査が違反として exit 1 を返し、診断に決まった文言が出る」だけにする。exit 2（入力を読めない）を拒否と誤認しない。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
immutable_model="$ROOT/plugins/bdd-discovery-and-formulation/skills/model-logical-data/scripts/immutable_model.py"
fixtures="$ROOT/scripts/fixtures/logical-data-model"
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
rejects() { "$@" >/dev/null 2>&1; [ "$?" -eq 1 ]; }
for cmd in python3 perl sed rg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[error] command $cmd が無い" >&2; exit 2; }
done
export PYTHONDONTWRITEBYTECODE=1

python3 "$immutable_model" check < "$fixtures/valid.md" >/dev/null \
  && pass "immutable_model.pyの構造正例" || fail "immutable_model.pyの構造正例"
sed "s/| 保存表現 |/| 保存の形 |/" "$fixtures/valid.md" | python3 "$immutable_model" check >/dev/null 2>&1
header_status=${PIPESTATUS[1]}
[ "$header_status" -eq 1 ] \
  && pass "immutable_model.pyは列名が契約と違う分類表を拒否（exit 1）" || fail "immutable_model.pyが列名の違う分類表を拒否できない"
resource_event_output=$(sed 's/| 現在状態 |/| イベント列 |/' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1)
resource_event_status=$?
if [ "$resource_event_status" -eq 1 ] \
  && rg -F 'リソース系の論理テーブルに対し、分類表の「保存表現」列でイベント列を選択している' <<< "$resource_event_output" >/dev/null; then
  pass "immutable_model.pyはリソース系と保存表現の不整合を対象・関係・値が明確な診断で拒否"
else
  fail "immutable_model.pyのリソース系と保存表現の不整合診断"
fi
rejects python3 "$immutable_model" check < "$fixtures/event-updated.md" \
  && pass "immutable_model.pyはイベントの更新宣言を拒否（exit 1）" || fail "immutable_model.pyがイベントの更新宣言を拒否できない"
rejects python3 "$immutable_model" check < "$fixtures/unclassified.md" \
  && pass "immutable_model.pyは未分類テーブルを拒否（exit 1）" || fail "immutable_model.pyが未分類テーブルを拒否できない"
python3 "$immutable_model" check < "$fixtures/conditional-null.md" >/dev/null \
  && pass "immutable_model.pyは意味評価対象の列名・NULLを拒否しない" || fail "immutable_model.pyが意味評価対象を誤検知"
(perl -pe 's/timestamptz occurred_at "要求した時点"/timestamptz requested_at "要求した時点"/' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F 'occurred_at の列が無い' >/dev/null \
  && pass "immutable_model.pyは occurred_at の無い技術イベントを拒否" || fail "immutable_model.pyが occurred_at の無い技術イベントを拒否できない"
(perl -pe 's/^(\s+text reason "取消の理由")$/$1\n        timestamptz occurred_at "取り消した時点"/' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F '詳細イベントが occurred_at の列を持つ' >/dev/null \
  && pass "immutable_model.pyは occurred_at を持つ詳細イベントを拒否" || fail "immutable_model.pyが occurred_at を持つ詳細イベントを拒否できない"
perl -pe 's/^(\s+text reason "取消の理由")$/$1\n        timestamptz cancelled_at "取り消した時点"/' "$fixtures/valid.md" | python3 "$immutable_model" check >/dev/null \
  && pass "immutable_model.pyは名前が _at で終わるだけの詳細イベントの列を拒否しない（時点かは読んで評価する）" || fail "immutable_model.pyが列の名前の語尾で判定している"
perl -pe 's/^(\s+timestamptz occurred_at "起きた時点")$/$1\n        timestamptz recorded_at "記録した時点"/' "$fixtures/valid.md" | python3 "$immutable_model" check >/dev/null \
  && pass "immutable_model.pyは名前が _at で終わるだけの基底イベントの列を拒否しない（二本目の時点かは読んで評価する）" || fail "immutable_model.pyが列の名前の語尾で判定している"
(sed 's/timestamptz occurred_at "起きた時点"/date occurred_at "起きた時点"/' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F 'occurred_at の型が timestamptz ではない' >/dev/null \
  && pass "immutable_model.pyは timestamptz でない occurred_at を拒否" || fail "immutable_model.pyが occurred_at の型を拒否できない"
(perl -pe 's/\| `occurred_at` \|/| 起きた時点は`occurred_at` |/' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F '時刻の欄が `occurred_at` と一致しない' >/dev/null \
  && pass "immutable_model.pyは時刻の欄が occurred_at と一致しない分類表を拒否" || fail "immutable_model.pyが時刻の欄の不一致を拒否できない"
(sed 's/reservation_base_events/reservation_header/g' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F '_eventsで終わらない' >/dev/null \
  && pass "immutable_model.pyは_eventsで終わらないイベント表を拒否" || fail "immutable_model.pyが_eventsで終わらないイベント表を拒否できない"
(sed '/bigint version "予約の中の順序"/d' "$fixtures/valid.md" | python3 "$immutable_model" check 2>&1; true) | rg -F '基底イベントに適用後の版 version が無い' >/dev/null \
  && pass "immutable_model.pyは version の無い基底イベントを拒否" || fail "immutable_model.pyが version の無い基底イベントを拒否できない"
perl -pe 's/^(\s+text reason "取消の理由")$/$1\n        date refund_due_on "返金の期限"/' "$fixtures/valid.md" | python3 "$immutable_model" check >/dev/null \
  && pass "immutable_model.pyは詳細イベントの日付の列を拒否しない" || fail "immutable_model.pyが詳細イベントの日付の列を誤検知"
sed -e 's/^## リソース系とイベント系$/## 予約は現在状態、出来事はイベント列で残す/' -e 's/^## 論理データモデル図$/## 予約と二つのイベント表/' -e 's/^## 論理テーブル定義$/## 一つの行にまとめるもの/' "$fixtures/valid.md" | python3 "$immutable_model" check >/dev/null \
  && pass "immutable_model.pyは見出しの文言に依らず目印で読む" || fail "immutable_model.pyが見出しの文言に依存している"
perl -0pe 's/(\| 系列 \| 性質 \| 論理テーブル \| 保存表現 \| 時刻 \| 変化 \| 根拠 \|\n)/$1/; $_ .= "\n| 系列 | 性質 | 論理テーブル | 保存表現 | 時刻 | 変化 | 根拠 |\n|---|---|---|---|---|---|---|\n"' "$fixtures/valid.md" | (python3 "$immutable_model" check 2>&1; true) | rg -F '分類表が2個ある' >/dev/null \
  && pass "immutable_model.pyは分類の表が二つある資料を拒否" || fail "immutable_model.pyが分類の表の重複を拒否できない"
python3 "$immutable_model" check </dev/null >/dev/null 2>&1; [ $? -eq 2 ] \
  && pass "immutable_model.pyの空stdinはexit 2" || fail "immutable_model.pyの空stdin終了code"

printf '\nimmutable_model.py: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
