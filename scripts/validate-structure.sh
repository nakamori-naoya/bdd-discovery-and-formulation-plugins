#!/usr/bin/env bash
# Scenario: BDD marketplaceがBDD責務だけを配布し、外部依存を名前で修飾している
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-structure.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
legacy_plugin="intermediate""-cleanup"
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

# step数とExamplesの行列数は内容の十分性を表さない。構造が正しい大きな例を受理し、
# Given/When/Thenと条件マトリクスの対応という表現契約は引き続き拒否できることを確かめる。
domain_formulation="$ROOT/plugins/playbooks/bdd/domain-bdd-formulation"
large_scenario="$TMP_ROOT/large-scenario.feature"
cat > "$large_scenario" <<'EOF'
Feature: 多数の結果と代表例を持つ業務規則
Scenario Outline: 必要な結果をすべて観測する
  Given <a> <b> <c> <d> <e> <f> <g> が前提である
  When 判定する
  Then 結果1を観測する
  And 結果2を観測する
  And 結果3を観測する
  And 結果4を観測する
  And 結果5を観測する
  And 結果6を観測する
  Examples:
    | a | b | c | d | e | f | g |
    | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
    | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
    | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
    | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
    | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
    | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
    | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
    | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
    | 9 | 9 | 9 | 9 | 9 | 9 | 9 |
    | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
    | 11 | 11 | 11 | 11 | 11 | 11 | 11 |
EOF
large_matrix="$TMP_ROOT/large-scenario-matrix.json"
cat > "$large_matrix" <<'EOF'
{"scenarios":[{"name":"必要な結果をすべて観測する","kind":"success","expected":"success","rule":"R","trigger":{"kind":"action","text":"判定する"},"premises":[{"name":"全条件","text":"<a> <b> <c> <d> <e> <f> <g> が前提である","state":"satisfied","target":false,"source":"業務規則"}]}]}
EOF
if python3 "$domain_formulation/scripts/scenario.py" check --config "$domain_formulation/playbook.yml" --file "$large_scenario" --matrix "$large_matrix" >/dev/null; then
  pass "step数とExamples行列数を品質gateにしない"
else
  fail "量だけで正しいBDD構造を拒否"
fi
broken_scenario="$TMP_ROOT/broken-large-scenario.feature"
sed 's/^  Then 結果1を観測する$/  When 結果1を観測する/' "$large_scenario" > "$broken_scenario"
if python3 "$domain_formulation/scripts/scenario.py" check --config "$domain_formulation/playbook.yml" --file "$broken_scenario" --matrix "$large_matrix" >/dev/null 2>&1; then
  fail "複数Whenを許可"
else
  pass "一つのWhenという表現契約を拒否側で検証"
fi

core_domain="$ROOT/plugins/skills/domain/core-domain"
scope_config="$TMP_ROOT/core-domain.yml"
scope_directory="$TMP_ROOT/core-scope"
scope_material="$TMP_ROOT/core-scope.md"
mkdir -p "$scope_directory"
cat > "$scope_config" <<EOF
scope_dir: $scope_directory
EOF
cat > "$scope_material" <<'EOF'
## コア
API商品という業務上の固有名を扱う
## 支援
なし
## 汎用
なし
## スコープ外
なし
EOF
if python3 "$core_domain/scripts/check.py" write --config "$scope_config" --topic semantic-boundary --body-file "$scope_material" >/dev/null; then
  pass "語の存在だけでコア境界を機械判定しない"
else
  fail "語の存在だけでコア境界の意味を判定"
fi

if jq -e '.name=="bdd-discovery-and-formulation" and (.plugins|length==1) and .plugins[0].name=="bdd-discovery-and-formulation" and .plugins[0].source.path=="./plugins"' "$ROOT/.agents/plugins/marketplace.json" >/dev/null; then
  pass "Codex marketplaceの配布境界"
else
  fail "Codex marketplaceの配布境界"
fi

if ! rg -n -i -- "$legacy_plugin" "$ROOT/.agents/plugins/marketplace.json" "$ROOT/.claude-plugin/marketplace.json" "$ROOT/plugins" "$ROOT/AGENTS.md" "$ROOT/README.md" >/dev/null \
  && [ ! -e "$ROOT/plugins/skills/authoring/$legacy_plugin" ]; then
  pass "旧cleanup配布物を同時に配らない"
else
  fail "旧cleanup配布物が残存"
fi

jq -r '.plugins[].name' "$ROOT/.agents/plugins/marketplace.json" | sort > "$TMP_ROOT/expected"
jq -r '.name' "$ROOT/plugins/.codex-plugin/plugin.json" | sort > "$TMP_ROOT/actual"
diff -u "$TMP_ROOT/expected" "$TMP_ROOT/actual" >/dev/null && pass "公開インストール対象はplaybook packageだけ" || fail "配布plugin集合"

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

for directory in domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e '.version==2 and (.requires|length>0) and all(.requires[]; (keys|sort)==["marketplace","plugin"])' >/dev/null; then
    pass "$directory name-qualified requirements"
  else
    fail "$directory name-qualified requirements"
  fi
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e 'all(.requires[]; .marketplace=="bdd-discovery-and-formulation" or .plugin==.marketplace)' >/dev/null; then
    pass "$directory 外部repositoryには公開playbook packageだけで依存"
  else
    fail "$directory が外部repositoryの内部機能へ依存"
  fi
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e --arg legacy "$legacy_plugin" '([.requires[] | select(.marketplace=="write-doc")] == [{"plugin":"write-doc","marketplace":"write-doc"}]) and (all(.requires[]; .plugin!=$legacy))' >/dev/null; then
    pass "$directory 外部の資料作成依存はwrite-doc playbookだけ"
  else
    fail "$directory が外部repositoryの内部機能へ依存"
  fi
  cmp -s "$ROOT/shared/playbook/resolve.sh" "$pb/scripts/resolve.sh" && pass "$directory resolver同期" || fail "$directory resolver同期"
  cmp -s "$ROOT/shared/playbook/resolve-dependency.py" "$pb/scripts/resolve-dependency.py" && pass "$directory dependency resolver同期" || fail "$directory dependency resolver同期"
  cmp -s "$ROOT/shared/playbook/state.py" "$pb/scripts/state.py" && pass "$directory 実行状態同期" || fail "$directory 実行状態同期"
  if has_execution_guidance "$pb"; then
    pass "$directory は順序契約と実行指示書を分離"
  else
    fail "$directory の実行指示書契約"
  fi
  cmp -s "$ROOT/shared/quality-engineering/scenario-premises.md" "$pb/references/scenario-premises.md" && pass "$directory 前提規律同期" || fail "$directory 前提規律同期"
  cmp -s "$ROOT/shared/quality-engineering/scenario_matrix.py" "$pb/scripts/scenario_matrix.py" && pass "$directory 条件マトリクスvalidator同期" || fail "$directory 条件マトリクスvalidator同期"
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e '
      .agent_work.owner=="invoking_agent" and
      .agent_work.delivery.provider=="write-doc" and
      .agent_work.delivery.input_mapping=={"material_kind":"text","material_content":"final_markdown"} and
      all(.steps[]; (.script // "") as $s |
        ($s != "scripts/ground.py" and $s != "scripts/compose.sh" and $s != "scripts/map.py" and $s != "scripts/material.sh" and $s != "scripts/cleanup.py"))' >/dev/null; then
    pass "$directory は認知判断を同一agentが保持しtext materialへ直接接続"
  else
    fail "$directory が旧認知relayを公開工程に残している"
  fi
  # 外部pluginは playbook: でしか指さない。skill: / script:+plugin: での参照はここでも止める。
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e --arg own bdd-discovery-and-formulation '
      . as $root |
      ([$root.requires[] | select(.marketplace != $own) | .plugin]) as $external |
      (all($root.steps[]; (.skill // "") as $s | ($external | index($s)) == null)) and
      (all($root.steps[]; (.plugin // "") as $p | ($external | index($p)) == null)) and
      (all($root.steps[]; (.playbook // null) as $b | $b == null or ($external | index($b)) != null)) and
      ([$root.steps[] | select(.playbook != null)] | length > 0)' >/dev/null; then
    pass "$directory 外部依存は playbook: 工程だけ"
  else
    fail "$directory が外部依存を skill: / script: で指している"
  fi
done

# Formulationのwrite-doc呼出しは更新先と新規保存先を混ぜない。
# 現行YAMLを正常例にし、更新target欠落、論理path名の取り違え、
# output_directory/nameとの混在をそれぞれ一箇所だけ変えた負例で固定する。
while IFS='|' read -r directory document_step expected_output_path; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  current="$TMP_ROOT/$directory-current.json"
  yq -o=json -I=0 '.' "$pb/playbook.yml" > "$current"
  if bash "$pb/scripts/validate-config.sh" "$current" >/dev/null; then
    pass "$directory 更新専用write-doc契約"
  else
    fail "$directory 更新専用write-doc正常系"
  fi

  missing_update="$TMP_ROOT/$directory-missing-update-target.json"
  jq --arg id "$document_step" '(.steps[] | select(.id==$id) | .needs) -= ["update_target"]' "$current" > "$missing_update"
  if bash "$pb/scripts/validate-config.sh" "$missing_update" >/dev/null 2>&1; then
    fail "$directory がupdate_target欠落を許可"
  else
    pass "$directory はupdate_target欠落を拒否"
  fi

  wrong_mapping="$TMP_ROOT/$directory-wrong-output-path.json"
  jq '.agent_work.delivery.output_path_from="different_existing_path"' "$current" > "$wrong_mapping"
  if bash "$pb/scripts/validate-config.sh" "$wrong_mapping" >/dev/null 2>&1; then
    fail "$directory が既存path論理名の不一致を許可"
  else
    pass "$directory は既存path論理名の不一致を拒否"
  fi

  mixed_mode="$TMP_ROOT/$directory-mixed-destination-mode.json"
  jq --arg id "$document_step" '(.steps[] | select(.id==$id) | .needs) += ["output_directory","name"]' "$current" > "$mixed_mode"
  if bash "$pb/scripts/validate-config.sh" "$mixed_mode" >/dev/null 2>&1; then
    fail "$directory が同じwrite-doc呼出しの新規/更新混在を許可"
  else
    pass "$directory は同じwrite-doc呼出しの新規/更新混在を拒否"
  fi
done <<'EOF'
data-model-bdd-formulation|update-logical-document|existing_logical_document_path
domain-bdd-formulation|document|existing_domain_rule_path
user-journey-bdd-formulation|document|existing_user_journey_bdd_path
EOF

# Data Model Formulationの物理設計は新規作成側なので、逆向きの混在も拒否する。
data_formulation="$ROOT/plugins/playbooks/bdd/data-model-bdd-formulation"
data_current="$TMP_ROOT/data-model-bdd-formulation-current.json"
data_mixed_create="$TMP_ROOT/data-model-bdd-formulation-mixed-create.json"
yq -o=json -I=0 '.' "$data_formulation/playbook.yml" > "$data_current"
jq '(.steps[] | select(.id=="document-physical") | .needs) += ["update_target"]' "$data_current" > "$data_mixed_create"
if bash "$data_formulation/scripts/validate-config.sh" "$data_mixed_create" >/dev/null 2>&1; then
  fail "data-model-bdd-formulation が物理設計の新規/更新混在を許可"
else
  pass "data-model-bdd-formulation は物理設計の新規/更新混在を拒否"
fi

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

# 外部依存の実体を同梱していないこと。名前は playbook.yml の requires から引く。
# 相手の内部の作りを列挙して検査すると、その内部名がこちらの検査へ焼き付いてしまう。
own_marketplace=$(jq -r '.metadata.harness.marketplace' "$ROOT/plugins/.claude-plugin/plugin.json")
external_plugins=$(for pb in "$ROOT"/plugins/playbooks/*/*/playbook.yml; do
    yq -o=json -I=0 '.' "$pb" | jq -r --arg own "$own_marketplace" '.requires[] | select(.marketplace != $own) | .plugin'
  done | sort -u)
bundled=""
for name in $external_plugins; do
  if find "$ROOT/plugins" -type d -name "$name" | rg . >/dev/null; then bundled="${bundled} ${name}"; fi
done
if [ -z "$bundled" ]; then
  pass "外部依存の実体を同梱しない"
else
  fail "外部pluginを同梱:${bundled}"
fi

# 同梱manifestが名乗る所属marketplaceは、自分のものだけであること。
foreign=$(find "$ROOT/plugins" -name 'plugin.json' -path '*-plugin/*' -exec \
  jq -r --arg own "$own_marketplace" '.metadata.harness.marketplace // empty | select(. != $own)' {} + | sort -u)
if [ -z "$foreign" ]; then
  pass "同梱manifestは自分のmarketplaceだけを名乗る"
else
  fail "別marketplaceを名乗るmanifestが同梱されている: $foreign"
fi

# 消費側が持つ規則の要約（入れ子の段取りの呼び方）が、全入口から必読になっていること。
nested_failed=0
for directory in domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  cmp -s "$ROOT/shared/consumer-contract/nested-playbook.md" "$pb/references/nested-playbook.md" || nested_failed=1
  rg -F '[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む' "$pb/SKILL.md" >/dev/null || nested_failed=1
done
[ "$nested_failed" -eq 0 ] && pass "入れ子の段取りの呼び方を全入口から必読にする" || fail "入れ子の段取りの呼び方の参照契約"

domain_events="$ROOT/plugins/skills/domain/domain-events"
if [ ! -e "$domain_events/references/event-sourcing.md" ] \
  && ! rg -n 'event_sourcing' "$domain_events/SKILL.md" "$domain_events/scripts/finalize.sh" >/dev/null; then
  pass "domain-eventsは後続の保存方式設計を同梱しない"
else
  fail "domain-eventsに後続設計の関心が混入"
fi

legacy_journey_plugin_pattern='e2e-bdd-documentation|e2e-bdd-scenarios|document-e2e-scenarios|bdd/e2e'
if rg -n -i "$legacy_journey_plugin_pattern" "$ROOT/plugins" "$ROOT/shared" "$ROOT/README.md" "$ROOT/AGENTS.md" >/dev/null; then
  fail "テスト実行と誤読される旧Journey plugin名が残存"
else
  pass "旧Journey plugin名なし"
fi

journey="$ROOT/plugins/skills/journey/user-journey"
good_map="$TMP_ROOT/good-journey-map.md"
cat > "$good_map" <<'EOF'
# 出張手配を完了する
- ユーザー: 出張者
- 目的: 出張に必要な手配を完了する
- 開始地点: 出張条件が決まっている
- 最終地点: 承認済みの予約情報を受け取っている
- 完了条件: 出張者が移動と宿泊の成立を確認できる
- 中心の問い: 複数の役割をまたいでも出張者の目的達成がつながるか
- Journeyとして扱う理由: 二つの意味ある場面が状態を受け渡し観測可能な完了へ進む
- Journeyに含めない問い: 個別の承認規則と保存構造
## 場面
### 場面 1: 希望を決める
- 直前の状態: 出張条件が決まっている
- 行う役割: 出張者
- 働きかけ: 希望条件を伝える
- 観測できる応答: 条件に合う候補が示される
- 次の状態: 候補を選べる
- 接続: 選んだ候補を承認へ渡せる
### 場面 2: 手配を成立させる
- 直前の状態: 候補を選べる
- 行う役割: 出張者
- 働きかけ: 希望する候補を選ぶ
- 観測できる応答: 承認済みの予約情報が示される
- 次の状態: 移動と宿泊が成立している
- 接続: 完了条件を満たす
## 分岐
なし
## 未決
なし
EOF
if python3 "$journey/scripts/journey.py" check --file "$good_map" >/dev/null; then
  pass "User Journey典型例を受理"
else
  fail "User Journey典型例"
fi
journey_repo="$TMP_ROOT/journey-repo"
mkdir -p "$journey_repo"
if bash "$journey/scripts/prepare.sh" --root-only >/dev/null \
  && python3 "$journey/scripts/journey.py" write --repo "$journey_repo" --slug business-trip --file "$good_map" >/dev/null \
  && [ -s "$journey_repo/bdd/discovery/user-journey/business-trip.md" ]; then
  pass "User Journey mapを配布単位だけで初回保存"
else
  fail "User Journey map初回保存"
fi
if python3 "$journey/scripts/journey.py" write --repo "$journey_repo" --slug business-trip --file "$good_map" >/dev/null 2>&1; then
  fail "既存Journey mapの黙示上書きを許可"
else
  pass "既存Journey mapの黙示上書きを拒否"
fi
bad_map="$TMP_ROOT/bad-ui-map.md"
sed 's/希望条件を伝える/APIを呼び出す/' "$good_map" > "$bad_map"
if python3 "$journey/scripts/journey.py" check --file "$bad_map" >/dev/null 2>&1; then
  pass "User Journeyの語彙責務を機械判定しない"
else
  fail "語の存在だけでUser Journeyの意味を判定"
fi
boundary_map="$TMP_ROOT/one-scene-map.md"
awk '/^### 場面 2:/{exit} {print}' "$good_map" > "$boundary_map"
printf '%s\n' '## 分岐' 'なし' '## 未決' 'なし' >> "$boundary_map"
if python3 "$journey/scripts/journey.py" check --file "$boundary_map" >/dev/null 2>&1; then
  fail "意味ある場面が一つだけの対象をJourneyへ拡大"
else
  pass "単一場面はJourney境界で拒否"
fi
if rg -n '^## (ユースケースではない|UX Journey mapではない|ドメインではない|データモデルではない|UIフローとテスト仕様ではない)$' "$journey/references/boundary.md" | wc -l | tr -d ' ' | rg '^5$' >/dev/null \
  && rg -n '^## (典型例|条件を一つ変えた境界例)$' "$journey/references/user-journey.md" | wc -l | tr -d ' ' | rg '^2$' >/dev/null; then
  pass "Journeyの何か・何ではないか・境界例を隣接referenceに固定"
else
  fail "Journey意味境界reference"
fi

journey_discovery="$ROOT/plugins/playbooks/bdd/user-journey-bdd-discovery"
good_story="$TMP_ROOT/good-user-journey-bdd.md"
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
good_matrix="$TMP_ROOT/good-user-journey-matrix.json"
cat > "$good_matrix" <<'EOF'
{"scenarios":[
  {"name":"希望を伝える","kind":"success","expected":"success","rule":"予約成立規則","trigger":{"kind":"action","text":"予約者が希望を伝える"},"premises":[{"name":"開始地点","text":"予約者が希望条件を決めている","state":"satisfied","target":false,"source":"予約資料"}]},
  {"name":"予約を成立させる","kind":"success","expected":"success","rule":"予約成立規則","trigger":{"kind":"action","text":"予約者が候補を選ぶ"},"premises":[{"name":"候補を選べる","text":"予約者が候補を選べる","state":"satisfied","target":false,"source":"予約資料"}]}
]}
EOF
if python3 "$journey_discovery/scripts/scenario.py" check --config "$journey_discovery/playbook.yml" --file "$good_story" --matrix "$good_matrix" >/dev/null; then
  pass "ユーザー目的達成BDDを複数場面として受理"
else
  fail "ユーザー目的達成BDD正常系"
fi

bad_story="$TMP_ROOT/bad-user-journey-bdd.md"
sed 's/予約者が希望を伝える/予約者がAPIを呼び出す/' "$good_story" > "$bad_story"
semantic_matrix="$TMP_ROOT/semantic-user-journey-matrix.json"
sed 's/予約者が希望を伝える/予約者がAPIを呼び出す/' "$good_matrix" > "$semantic_matrix"
if python3 "$journey_discovery/scripts/scenario.py" check --config "$journey_discovery/playbook.yml" --file "$bad_story" --matrix "$semantic_matrix" >/dev/null 2>&1; then
  pass "ユーザー目的達成BDDの語彙責務を機械判定しない"
else
  fail "語の存在だけでユーザー目的達成BDDの意味を判定"
fi

journey_formulation="$ROOT/plugins/playbooks/bdd/user-journey-bdd-formulation"
existing="$TMP_ROOT/existing-user-journey.md"
same="$TMP_ROOT/existing-user-journey.md"
different="$TMP_ROOT/new-user-journey.md"
cp "$good_story" "$existing"
if python3 "$journey_formulation/scripts/update-guard.py" --existing "$existing" --output "$same" >/dev/null; then
  pass "Journey Formulationは同一パス更新を受理"
else
  fail "Journey Formulation同一パス更新"
fi
if python3 "$journey_formulation/scripts/update-guard.py" --existing "$existing" --output "$different" >/dev/null 2>&1; then
  fail "Journey Formulationが新規資料を許可"
else
  pass "Journey Formulationは新規資料を拒否"
fi

syntax_failed=0
while IFS= read -r script; do bash -n "$script" || syntax_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.sh' | sort)
[ "$syntax_failed" -eq 0 ] && pass "shell構文" || fail "shell構文"

# $VAR の直後に非ASCII（全角括弧・かな・漢字）が続くと、localeによっては
# 全角文字まで変数名として読まれ、set -u の下で unbound variable になって途中終了する。
# 日本語の文中で変数を使うときは必ず ${VAR} と囲む。
if find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.sh' -print0 \
    | xargs -0 python3 -c '
import re, sys
pattern = re.compile(r"\$(?!\{)[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]")
found = 0
for path in sys.argv[1:]:
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            for match in pattern.finditer(line):
                print(f"{path}:{number}: {match.group(0)}")
                found = 1
sys.exit(found)
'; then
  pass "非ASCIIに接する裸の変数参照なし"
else
  fail "非ASCIIに接する裸の変数参照（\${VAR} で囲む）"
fi

python_failed=0
while IFS= read -r script; do PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile "$script" || python_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.py' | sort)
[ "$python_failed" -eq 0 ] && pass "Python構文" || fail "Python構文"

printf '\nStructure: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
