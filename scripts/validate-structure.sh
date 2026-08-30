#!/usr/bin/env bash
# Scenario: BDD marketplaceがBDD責務だけを配布し、外部依存を名前で修飾している
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-structure.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
has_execution_guidance() {
  pb=$1
  [ -s "$pb/references/execution-guidance.md" ] \
    && rg -F '[実行指示書](references/execution-guidance.md)を必ず読む' "$pb/SKILL.md" >/dev/null \
    && rg -n '^### grill$' "$pb/references/execution-guidance.md" >/dev/null
}

for cmd in jq yq python3 bash cmp find sort diff rg; do
  command -v "$cmd" >/dev/null 2>&1 && pass "command $cmd" || fail "command $cmd が無い"
done

# 条件マトリクスの代表的な正常系・境界系・不正系を固定する。
matrix_validator="$ROOT/shared/quality-engineering/scenario_matrix.py"
matrix_good="$TMP_ROOT/matrix-good.json"
cat > "$matrix_good" <<'EOF'
{"scenarios":[
  {"name":"成功","kind":"success","expected":"success","rule":"R","trigger":{"kind":"event","text":"受付が起きる"},"premises":[{"name":"A","text":"Aが成立","state":"satisfied","target":false,"source":"業務規則"}]},
  {"name":"単一失敗","kind":"single_failure","expected":"failure","rule":"R","trigger":{"kind":"action","text":"確認する"},"premises":[{"name":"A","text":"Aが成立","state":"satisfied","target":false,"source":"業務規則"},{"name":"B","text":"Bが不成立","state":"unsatisfied","target":true,"source":"業務規則"}],"note":{"rule":"R","reason":"Bに抵触"}},
  {"name":"境界","kind":"boundary","expected":"success","rule":"R","trigger":{"kind":"action","text":"判定する"},"premises":[{"name":"A","text":"Aが境界","state":"boundary","target":true,"source":"業務規則"}]},
  {"name":"組合せ","kind":"interaction","expected":"success","rule":"R","trigger":{"kind":"event","text":"同時に起きる"},"premises":[{"name":"A","text":"A","state":"satisfied","target":true,"source":"業務規則"},{"name":"B","text":"B","state":"satisfied","target":true,"source":"業務規則"}]}
]}
EOF
if python3 "$matrix_validator" check --file "$matrix_good" >/dev/null; then pass "条件マトリクス代表ケース"; else fail "条件マトリクス代表ケース"; fi
matrix_bad="$TMP_ROOT/matrix-bad.json"
sed 's/"state":"satisfied","target":false/"state":"unsatisfied","target":false/' "$matrix_good" > "$matrix_bad"
if python3 "$matrix_validator" check --file "$matrix_bad" >/dev/null 2>&1; then fail "条件マトリクスの暗黙前提を許可"; else pass "条件マトリクスの暗黙前提を拒否"; fi

if jq -e '.name=="bdd-discovery-and-formulation" and (.plugins|length==11)' "$ROOT/.agents/plugins/marketplace.json" >/dev/null; then
  pass "Codex marketplaceの配布境界"
else
  fail "Codex marketplaceの配布境界"
fi

jq -r '.plugins[].name' "$ROOT/.agents/plugins/marketplace.json" | sort > "$TMP_ROOT/expected"
find "$ROOT/plugins" -path '*/.codex-plugin/plugin.json' -type f -exec jq -r '.name' {} \; | sort > "$TMP_ROOT/actual"
diff -u "$TMP_ROOT/expected" "$TMP_ROOT/actual" >/dev/null && pass "配布pluginは11件だけ" || fail "配布plugin集合"

for market in .agents/plugins/marketplace.json .claude-plugin/marketplace.json; do
  jq -r '.plugins[].name' "$ROOT/$market" | sort > "$TMP_ROOT/market"
  diff -u "$TMP_ROOT/expected" "$TMP_ROOT/market" >/dev/null && pass "$market plugin集合" || fail "$market plugin集合"
done

if jq -e '.name=="bdd-discovery-and-formulation" and all(.plugins[]; .policy.installation=="AVAILABLE" and .policy.authentication=="ON_INSTALL" and (.category|length>0))' "$ROOT/.agents/plugins/marketplace.json" >/dev/null \
  && jq -e '.name=="bdd-discovery-and-formulation"' "$ROOT/.claude-plugin/marketplace.json" >/dev/null; then
  pass "marketplace identityとCodex policy"
else
  fail "marketplace identityとCodex policy"
fi

while IFS='|' read -r name version rel; do
  codex="$ROOT/$rel/.codex-plugin/plugin.json"
  claude="$ROOT/$rel/.claude-plugin/plugin.json"
  if jq -e --arg n "$name" --arg v "$version" '.name==$n and .version==$v' "$codex" "$claude" >/dev/null; then
    pass "$name manifest identity"
  else
    fail "$name manifest identity"
  fi
done < <(jq -r '.plugins[] | [.name,.version,(.source.path | ltrimstr("./"))] | join("|")' "$ROOT/.agents/plugins/marketplace.json")

for directory in domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation e2e-bdd-documentation; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e '.version==2 and (.requires|length>0) and all(.requires[]; (keys|sort)==["marketplace","plugin"])' >/dev/null; then
    pass "$directory name-qualified requirements"
  else
    fail "$directory name-qualified requirements"
  fi
  cmp -s "$ROOT/shared/playbook/resolve.sh" "$pb/scripts/resolve.sh" && pass "$directory resolver同期" || fail "$directory resolver同期"
  cmp -s "$ROOT/shared/playbook/resolve-dependency.py" "$pb/scripts/resolve-dependency.py" && pass "$directory dependency resolver同期" || fail "$directory dependency resolver同期"
  if has_execution_guidance "$pb"; then
    pass "$directory は順序契約と実行指示書を分離"
  else
    fail "$directory の実行指示書契約"
  fi
  cmp -s "$ROOT/shared/quality-engineering/scenario-premises.md" "$pb/references/scenario-premises.md" && pass "$directory 前提規律同期" || fail "$directory 前提規律同期"
  cmp -s "$ROOT/shared/quality-engineering/scenario_matrix.py" "$pb/scripts/scenario_matrix.py" && pass "$directory 条件マトリクスvalidator同期" || fail "$directory 条件マトリクスvalidator同期"
done

# 実行指示書が無い、または入口から必読になっていない構成を拒否する負の試験。
broken="$TMP_ROOT/broken-guidance"
mkdir -p "$broken/references"
printf '%s\n' '# fixture' > "$broken/SKILL.md"
printf '%s\n' '# fixture' '### grill' > "$broken/references/execution-guidance.md"
if has_execution_guidance "$broken"; then
  fail "入口から未参照の実行指示書を許可"
else
  pass "入口から未参照の実行指示書を拒否"
fi

if rg -n -i 'prototype|プロトタイプ' "$ROOT" -g '*.md' -g '*.json' >/dev/null; then
  fail "prototype表現が残存"
else
  pass "prototype表現なし"
fi

if find "$ROOT/plugins" -type d \( -name write-doc -o -name writing-rules -o -name content-types -o -name visual-guidance -o -name doc-render -o -name grill \) | rg . >/dev/null; then
  fail "外部pluginを同梱"
else
  pass "write-docとgrillを同梱しない"
fi

domain_events="$ROOT/plugins/skills/domain/domain-events"
if [ ! -e "$domain_events/references/event-sourcing.md" ] \
  && ! rg -n 'event_sourcing' "$domain_events/SKILL.md" "$domain_events/scripts/finalize.sh" >/dev/null; then
  pass "domain-eventsは後続の保存方式設計を同梱しない"
else
  fail "domain-eventsに後続設計の関心が混入"
fi

legacy_bdd_pattern='use''[- ]?case|jour''ney|ユース''ケース|ジャー''ニー'
if rg -n -i "$legacy_bdd_pattern" "$ROOT/plugins" "$ROOT/shared" >/dev/null; then
  fail "旧BDD焦点の資産または記述が残存"
else
  pass "旧BDD焦点の資産と記述なし"
fi

e2e="$ROOT/plugins/playbooks/bdd/e2e-bdd-documentation"
good_story="$TMP_ROOT/good-e2e.md"
cat > "$good_story" <<'EOF'
# 予約を完了する
- ユーザー: 予約者
- 目的: 希望する条件で予約を成立させる
- 開始地点: 予約者が希望条件を決めている
- 最終地点: 予約が成立している
- 完了条件: 予約者が成立した予約を確認できる
### 場面 1: 希望を伝える
Given 予約者が希望条件を決めている
When 予約者が希望を伝える
Then 希望に合う候補が示される
接続: 示された候補を選べる状態になる
### 場面 2: 予約を成立させる
Given 予約者が候補を選べる
When 予約者が候補を選ぶ
Then 予約が成立し予約者が確認できる
EOF
good_matrix="$TMP_ROOT/good-e2e-matrix.json"
cat > "$good_matrix" <<'EOF'
{"scenarios":[
  {"name":"希望を伝える","kind":"success","expected":"success","rule":"予約成立規則","trigger":{"kind":"action","text":"予約者が希望を伝える"},"premises":[{"name":"開始地点","text":"予約者が希望条件を決めている","state":"satisfied","target":false,"source":"予約資料"}]},
  {"name":"予約を成立させる","kind":"success","expected":"success","rule":"予約成立規則","trigger":{"kind":"action","text":"予約者が候補を選ぶ"},"premises":[{"name":"候補を選べる","text":"予約者が候補を選べる","state":"satisfied","target":false,"source":"予約資料"}]}
]}
EOF
if python3 "$e2e/scripts/scenario.py" check --config "$e2e/playbook.yml" --file "$good_story" --matrix "$good_matrix" >/dev/null; then
  pass "E2Eの長いストーリーを複数場面として受理"
else
  fail "E2Eストーリー正常系"
fi

bad_story="$TMP_ROOT/bad-e2e.md"
sed 's/予約者が希望を伝える/予約者がAPIを呼び出す/' "$good_story" > "$bad_story"
if python3 "$e2e/scripts/scenario.py" check --config "$e2e/playbook.yml" --file "$bad_story" --matrix "$good_matrix" >/dev/null 2>&1; then
  fail "E2E資料にAPI操作を許可"
else
  pass "E2E資料からAPI操作を拒否"
fi

syntax_failed=0
while IFS= read -r script; do bash -n "$script" || syntax_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" -type f -name '*.sh' | sort)
[ "$syntax_failed" -eq 0 ] && pass "shell構文" || fail "shell構文"

python_failed=0
while IFS= read -r script; do PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile "$script" || python_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.py' | sort)
[ "$python_failed" -eq 0 ] && pass "Python構文" || fail "Python構文"

printf '\nStructure: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
