#!/usr/bin/env bash
# immutable_model.py（model-command-data が保存したコマンドデータモデルに一回かける検査）を、正例・反例・境界例で確かめる。
# fixture は scripts/fixtures/command-data-model/ にあり、反例は一時ディレクトリへ写した fixture を一か所だけ変えて作る。
# 反例の合格述語は「検査が違反として exit 1 を返し、診断に決まった文言が出る」だけにする。exit 2（入力を読めない）を拒否と誤認しない。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
checker="$ROOT/plugins/bdd-discovery-and-formulation/skills/model-command-data/scripts/immutable_model.py"
fixtures="$ROOT/scripts/fixtures/command-data-model"
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
for cmd in python3 perl rg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "[error] command $cmd が無い" >&2; exit 2; }
done
export PYTHONDONTWRITEBYTECODE=1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# fresh: fixture を一時ディレクトリへ写し直す。
fresh() { rm -rf "$work/m"; mkdir -p "$work/m"; cp "$fixtures"/*.md "$work/m/"; }
# accepts <名前> <資料...>: exit 0 なら合格。
accepts() { local name=$1; shift; python3 "$checker" check "$@" >/dev/null 2>&1 && pass "$name" || fail "$name"; }
# rejects <名前> <診断の文言> <資料...>: exit 1 で、診断に文言が出れば合格。
rejects() {
  local name=$1 expected=$2; shift 2
  local output status
  output=$(python3 "$checker" check "$@" 2>&1); status=$?
  if [ "$status" -eq 1 ] && rg -F -- "$expected" <<< "$output" >/dev/null; then pass "$name"; else fail "$name（exit $status）"; fi
}
# edit <perl の置換>: 一時ディレクトリの valid.md を書き換える。
edit() { perl -0pi -e "$1" "$work/m/valid.md"; }

fresh; accepts "構造の正例" "$work/m/valid.md"
fresh; accepts "持ち主を参照する資料との組の正例" "$work/m/valid.md" "$work/m/reader.md"
fresh; accepts "条件付きNULL・状態・削除フラグを含むだけでは拒まない" "$work/m/conditional-null.md"
fresh; edit 's/\| 保存表現 \|/| 保存の形 |/'; rejects "列名が契約と違う分類表を拒否" "分類表が0個ある" "$work/m/valid.md"
fresh; edit 's/\| 現在状態 \|/| イベント列 |/'; rejects "リソース系でイベント列を選んだ分類を拒否" "リソース系の論理テーブルに対し、分類表の「保存表現」列でイベント列を選択している" "$work/m/valid.md"
fresh; rejects "性質が派生のテーブルを拒否" "許可値ではない: 派生" "$work/m/derived.md"
fresh; rejects "未分類のテーブルを拒否" "図のテーブルが分類表にも参照の表にも無い" "$work/m/unclassified.md"
fresh; edit 's/timestamptz occurred_at "要求した時点"/timestamptz requested_at "要求した時点"/'; rejects "occurred_at の無い技術イベントを拒否" "occurred_at の列が無い" "$work/m/valid.md"
fresh; edit 's/(\s+text reason "取消の理由")/$1\n        timestamptz occurred_at "取り消した時点"/'; rejects "occurred_at を持つ詳細イベントを拒否" "詳細イベントが occurred_at の列を持つ" "$work/m/valid.md"
fresh; edit 's/(\s+text reason "取消の理由")/$1\n        timestamptz cancelled_at "取り消した時点"/'; accepts "名前が _at で終わるだけの詳細イベントの列は拒まない" "$work/m/valid.md"
fresh; edit 's/(\s+timestamptz occurred_at "起きた時点")/$1\n        timestamptz recorded_at "記録した時点"/'; accepts "名前が _at で終わるだけの基底イベントの列は拒まない" "$work/m/valid.md"
fresh; edit 's/timestamptz occurred_at "起きた時点"/date occurred_at "起きた時点"/'; rejects "timestamptz でない occurred_at を拒否" "occurred_at の型が timestamptz ではない" "$work/m/valid.md"
fresh; edit 's/reservation_base_events/reservation_header/g'; rejects "_events で終わらないイベント表を拒否" "_eventsで終わらない" "$work/m/valid.md"
fresh; edit 's/\n\s+bigint version "予約の中の順序"//'; rejects "version の無い基底イベントを拒否" "基底イベントに適用後の版 version が無い" "$work/m/valid.md"
fresh; edit 's/\n\s+bigint current_version "反映済みの最後の版"//'; rejects "current_version の無いリソースを拒否" "current_version の列が無い" "$work/m/valid.md"
fresh; edit 's/\n\s+text status "いまの状態"//'; rejects "status の無いリソースを拒否" "status の列が無い" "$work/m/valid.md"
fresh; edit 's/\n\s+reservations \|\|--\|\{ reservation_base_events : "起きたこと"//'; rejects "リソースと結ばれていない基底イベントを拒否" "リソース系・業務のテーブルと結ばれていない" "$work/m/valid.md"
fresh; edit 's/\n\| イベント系 \| 技術 \| `cancel_notice_succeeded_events`[^\n]*//; s/\n\s+cancel_notice_succeeded_events \{[^}]*\}//; s/\n### `cancel_notice_succeeded_events`[^\n]*\n\n[^\n]*\n//'; rejects "成功の表の無い要求を拒否" "cancel_notice_succeeded_events が技術イベントとして分類されていない" "$work/m/valid.md"
fresh; edit 's/\n\s+bigint version "要求の中の回収の順序"//'; rejects "version の無い回収を拒否" "回収の表に要求の中での回収の版 version が無い" "$work/m/valid.md"
fresh; edit 's/(\s+text reason "取消の理由")/$1\n        date refund_due_on "返金の期限"/'; accepts "詳細イベントの日付の列は拒まない" "$work/m/valid.md"
fresh; edit 's/^## リソース系とイベント系$/## 予約は現在状態、出来事はイベント列で残す/m; s/^## データモデル図$/## 予約と二つのイベント表/m'; accepts "見出しの文言に依らず目印で読む" "$work/m/valid.md"
fresh; printf '\n| 系列 | 性質 | 論理テーブル | 保存表現 | 根拠 |\n|---|---|---|---|---|\n' >> "$work/m/valid.md"; rejects "分類の表が二つある資料を拒否" "分類表が2個ある" "$work/m/valid.md"
fresh; perl -0pi -e 's/`reservation_id`、`status`/`reservation_id`、`guest_name`/; s/text status "いまの状態"\n    \}\n    entries/text guest_name "予約した人"\n    }\n    entries/' "$work/m/reader.md"; rejects "持ち主の図に無い読む列を拒否" "読む列が持ち主の図に無い" "$work/m/reader.md"
fresh; perl -0pi -e 's/\| `reservation_id`、`status` \|/| `reservation_id` |/' "$work/m/reader.md"; rejects "読む列と図の列が違う参照を拒否" "参照したテーブルの図の列が読む列と一致しない" "$work/m/reader.md"
fresh; perl -0pi -e 's/\(valid\.md\)/(missing.md)/' "$work/m/reader.md"
output=$(python3 "$checker" check "$work/m/reader.md" 2>&1); status=$?
[ "$status" -eq 0 ] && rg -F '"unverified"' <<< "$output" >/dev/null && pass "まだ無い持ち主は未確認として報告し、合否に数えない" || fail "まだ無い持ち主の扱い（exit $status）"
fresh; perl -0pi -e 's/reservation_base_events/room_base_events/g' "$work/m/derived.md"; accepts "残りの引数の資料の違反では判定する資料を落とさない" "$work/m/valid.md" "$work/m/derived.md"
fresh; edit 's/(\| リソース系 \| 業務 \| `reservations` [^\n]*\n)/$1| リソース系 | 技術 | `external_accounts` | 現在状態 | 認証の識別子を失うと利用を続けられない（品質要求） |\n/; s/(erDiagram\n)/$1    external_accounts {\n        text external_subject PK "外部の認証の識別子"\n        uuid user_id "利用者"\n    }\n/; s/(### `reservations`)/### `external_accounts`（外部の認証とのひも付け）\n\nひも付け。\n\n$1/'; accepts "技術のリソースは status と current_version を求めない" "$work/m/valid.md"
fresh; perl -0pi -e 's/(\| リソース系 \| 業務 \| `entries`[^\n]*\n)/$1| リソース系 | 業務 | `reservations` | 現在状態 | 入室の業務知識 |\n/; s/\n\| `reservations` \| `reservation_id`、`status` \|[^\n]*//; s/^(### `entries`)/### `reservations`（予約）\n\n予約。\n\n$1/m' "$work/m/reader.md"
rejects "残りの引数の資料も同じテーブルを分類していれば判定する資料で拒否" "同じテーブルをほかの資料も分類している" "$work/m/valid.md" "$work/m/reader.md"
fresh; edit 's/\| BDD-001 \| 対象外 \|/| BDD-001 | 対象外（拒否） |/'; rejects "許されない対応の欄を拒否" "この資料のBDDの欄が許された形ではない" "$work/m/valid.md"
fresh; edit 's/\| BDD-001 \| 対象外 \|/| BDD-001 | BDD-009 |/'; rejects "この資料に無い BDD を指す対応を拒否" "この資料に BDD-009 が無い" "$work/m/valid.md"
fresh; edit 's/\| 業務知識のBDD \| この資料のBDD \|/| 業務知識 | この資料 |/'; rejects "対応の表の無い資料を拒否" "対応の表が0個ある" "$work/m/valid.md"
python3 "$checker" check >/dev/null 2>&1; [ $? -eq 2 ] && pass "引数の無い呼び出しは exit 2" || fail "引数の無い呼び出しの終了code"
python3 "$checker" check "$work/none.md" >/dev/null 2>&1; [ $? -eq 2 ] && pass "読めない資料は exit 2" || fail "読めない資料の終了code"

printf '\nimmutable_model.py: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
