#!/usr/bin/env bash
# business_knowledge.py（write-business-knowledge が保存した業務知識に一回かける検査）を、正例・反例・境界例で確かめる。
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
accepts() { local name=$1; shift; python3 "$checker" "$@" >/dev/null 2>&1 && pass "$name" || fail "$name"; }
rejects() {
  local name=$1 expected=$2; shift 2
  local output status
  output=$(python3 "$checker" "$@" 2>&1); status=$?
  if [ "$status" -eq 1 ] && rg -F -- "$expected" <<< "$output" >/dev/null; then pass "$name"; else fail "${name}（exit ${status}）"; fi
}
unverified() {
  local name=$1; shift
  local output status
  output=$(python3 "$checker" "$@" 2>&1); status=$?
  if [ "$status" -eq 0 ] && rg -F '"unverified"' <<< "$output" >/dev/null; then pass "$name"; else fail "${name}（exit ${status}）"; fi
}
edit() { perl -0pi -e "$2" "$1"; }

# 正例
fresh; accepts "持ち主の資料の正例" check "$owner"
fresh; accepts "前提で持ち主を指す資料の正例" check "$user"
fresh; accepts "前提のリンク先がある資料の組の正例" check-set "$owner" "$user"

# 境界例
fresh; edit "$owner" 's/^## 前提\n\n### 利用者\n\n[^\n]*\n/## 前提\n\nこの業務は前提を持たない。\n/m; s/利用者、一部屋一日一件/一部屋一日一件/'; accepts "中身の無い節を一文で残した資料を通す" check "$owner"
fresh; accepts "状況を持たない資料のいつでもを通す" check "$user"
fresh; edit "$owner" 's/^\| 予約している \| 利用者 \| 予約した本人ではない利用者が取り消す \|/| 予約している、取り消した | 利用者 | 予約した本人ではない利用者が取り消す |/m'; accepts "状況を「、」で並べてまとめた行を通す" check "$owner"
fresh; edit "$owner" 's/^### 予約している（Active）$/### 予約している/m'; accepts "英名を添えない状況の名前でも表から引ける" check "$owner"
fresh; edit "$user" 's#\.\./予約/business-knowledge\.md#../無い/business-knowledge.md#g'; unverified "前提のリンク先が無ければ未確認として通す" check-set "$user"
fresh; edit "$owner" 's/^## 前提\n\n### 利用者$/## 前提\n\n### 予約/m; s/利用者、一部屋一日一件/予約、一部屋一日一件/'; accepts "前提の同じ名前は二つの資料の照合に数えない" check-set "$owner" "$user"
fresh; accepts "check は前提のリンク先を照合しない" check "$user"

# 反例: 見出しの骨組み
fresh; edit "$owner" 's/^## 計算\n\n### 取り消す日\n\n[^\n]*\n\n//m; s/、取り消す日//g'; rejects "節の欠けを拒否" "の順の八つではない" check "$owner"
fresh; edit "$owner" 's/^## 制約$/## 前提の二/m; s/^## 前提$/## 制約/m; s/^## 前提の二$/## 前提/m'; rejects "節の順の入れ替えを拒否" "の順の八つではない" check "$owner"
fresh; edit "$owner" 's/^## まだ決まっていないこと$/## ユビキタス言語\n\nなし。\n\n## まだ決まっていないこと/m'; rejects "余分な節を拒否" "の順の八つではない" check "$owner"
fresh; edit "$owner" 's/^## BDD$/# BDD の一覧\n\n## BDD/m'; rejects "二つ目の表題を拒否" "\`#\` の見出しが2個ある" check "$owner"
fresh; edit "$owner" 's/^### 取り消す日$/### 本人だけが取り消す/m; s/、取り消す日//g'; rejects "制約と計算をまたぐ同じ名前を拒否" "同じ名前が制約の節にもある" check "$owner"
fresh; edit "$owner" 's/^### 取り消した（Cancelled）$/### 予約している（Done）/m'; rejects "英名を外すと同じになる状況の名前を拒否" "同じ名前が状況の節にもある" check "$owner"

# 反例: 判断の表
fresh; edit "$owner" 's/\| いつ \| 誰が \| 何をすると \| 何が起きる \| どの決まりによるか \|/| いつ | 誰が | 何をすると | 根拠 |/'; rejects "見出し行の違う表を拒否" "ではない表がある" check "$owner"
fresh; edit "$owner" 's/^(\| 予約している \| 利用者 \| 予約した本人が利用日より後に取り消す [^\n]*\n)/$1\n| いつ | 誰が | 何をすると | 何が起きる | どの決まりによるか |\n|---|---|---|---|---|\n| 取り消した | 利用者 | 取り消す | できない。何も変わらない | 本人だけが取り消す |\n\n/m'; rejects "二つ目の判断の表を拒否" "判断の表が二つ目である" check "$owner"
fresh; edit "$owner" 's/^## まだ決まっていないこと\n\nなし。/## まだ決まっていないこと\n\n| いつ | 誰が | 何をすると | 何が起きる | どの決まりによるか |\n|---|---|---|---|---|\n| 取り消した | 利用者 | 取り消す | できない。何も変わらない | 本人だけが取り消す |/m'; rejects "節の外の判断の表を拒否" "節の外にある" check "$owner"
fresh; edit "$owner" 's/\| できない。何も変わらない \| 一部屋一日一件 \|/| 一部屋一日一件 |/'; rejects "列数の違う行を拒否" "列数が判断の表の見出しと一致しない" check "$owner"
fresh; edit "$owner" 's/^\| 予約している \| 利用者 \| 予約した本人ではない/| 予約中 | 利用者 | 予約した本人ではない/m'; rejects "状況の節に無いいつを拒否" "いつの欄の名前が状況の節に無い: 予約中" check "$owner"
fresh; edit "$owner" 's/^\| 予約が無い \|/| — |/m'; rejects "いつの欄の「—」を拒否" "いつの欄の名前が状況の節に無い: —" check "$owner"
fresh; edit "$owner" 's/^\| 予約が無い \|/| いつでも |/m'; rejects "状況を持つ資料のいつでもを拒否" "状況を持つ資料のいつの欄が「いつでも」である" check "$owner"
fresh; edit "$owner" 's/\| できない。何も変わらない \| 本人だけが取り消す \|/| できない。何も変わらない | 本人だけが取り消す、他人の予約 |/'; rejects "どの項目にも無い決まりを拒否" "どの決まりによるかの名前が前提、制約、状況、計算のどれにも無い: 他人の予約" check "$owner"
fresh; edit "$owner" 's/\| できない。何も変わらない \| 取り消しは利用日まで、取り消す日 \|/| できない。何も変わらない | 取り消す日 |/'; rejects "計算だけによるできない行を拒否" "できない行のどの決まりによるかに、制約、前提、状況の名前が無い" check "$owner"
fresh; edit "$owner" 's/\| できない。何も変わらない \| 本人だけが取り消す \|/| できない。何も変わらない | — |/'; rejects "できない行の「—」を拒否" "できない行のどの決まりによるかが「—」である" check "$owner"
fresh; edit "$owner" 's/\| 本人だけが取り消す、取り消しは利用日まで、取り消す日 \|/| — |/'; accepts "できない行でない行の「—」を通す" check "$owner"
fresh; edit "$owner" 's/^### 取り消す日$/### 取り消す日、時刻/m'; rejects "「、」を含む項目の名前を拒否" "項目の名前が「、」を含む" check "$owner"

# 反例: BDD
fresh; edit "$owner" 's/\[BDD-002\]/[BDD-001]/'; rejects "BDD 番号の重複を拒否" "BDD の番号が" check "$owner"
fresh; edit "$owner" 's/\[BDD-002\]/[BDD-2]/'; rejects "3桁未満の BDD 番号を拒否" "3桁以上の数字" check "$owner"
fresh; edit "$owner" 's/^### 取り消す日$/### [BDD-009] 取り消す日/m; s/、取り消す日//g'; rejects "BDD の節の外の BDD を拒否" "BDD の節の外にある" check "$owner"
fresh; edit "$owner" 's/^## BDD\n/## BDD\n\n### 取り消しの例\n/m'; rejects "BDD の節の BDD でない見出しを拒否" "の形ではない" check "$owner"
fresh; edit "$owner" 's/Rule: 本人だけが取り消す/Rule: 取り消す日/'; rejects "計算の名前を指す Rule を拒否" "制約にも前提にも状況にも無い" check "$owner"
fresh; edit "$user" 's/Rule: 予約した本人だけが入る/Rule: 本人ではない/'; rejects "どの項目にも無い Rule を拒否" "制約にも前提にも状況にも無い" check "$user"

# 反例: 資料の組
fresh; edit "$user" 's/^### 予約した本人だけが入る$/### 一部屋一日一件/m; s/予約した本人だけが入る/一部屋一日一件/g'; rejects "二つの資料が定義する同じ制約を拒否" "も制約として定義している" check-set "$owner" "$user"
fresh; edit "$user" 's/^### 入室する日$/### 予約している/m; s/入室する日/予約している/g'; rejects "ほかの資料の状況と同じ名前の計算を拒否" "も状況として定義している" check-set "$owner" "$user"

# 引数
python3 "$checker" check >/dev/null 2>&1; [ $? -eq 2 ] && pass "引数の無い呼び出しは exit 2" || fail "引数の無い呼び出しの終了code"
fresh; python3 "$checker" check "$owner" "$user" >/dev/null 2>&1; [ $? -eq 2 ] && pass "check に二本渡すと exit 2" || fail "check に二本渡したときの終了code"
python3 "$checker" check "$work/無い.md" >/dev/null 2>&1; [ $? -eq 2 ] && pass "読めない資料は exit 2" || fail "読めない資料の終了code"

printf '\nbusiness_knowledge.py: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
