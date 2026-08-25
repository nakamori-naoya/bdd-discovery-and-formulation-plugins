#!/usr/bin/env bash
# Scenario: 15 pluginだけを配布できる構造になっている
# Given: vendor-lockと2つのmarketplaceにコピー対象が固定されている
# When: manifest、shared正本、構文、除外境界を検査する
# Then: 対象の欠落・余分なplugin・byte差分・構文不正を一つも見逃さない
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/knowledge-hub-bdd-structure.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT

passed=0
failed=0

pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }

for cmd in jq yq python3 bash cmp find sort diff rg xargs; do
  if command -v "$cmd" >/dev/null 2>&1; then pass "command $cmd"; else fail "command $cmd が無い"; fi
done

if jq -e '.schema == 1 and (.plugins | length == 15)' "$ROOT/vendor-lock.json" >/dev/null; then
  pass "vendor-lock schemaと15件"
else
  fail "vendor-lock schemaまたは件数"
fi

jq -r '.plugins[].name' "$ROOT/vendor-lock.json" | sort > "$TMP_ROOT/expected-names"
find "$ROOT/plugins" -path '*/.codex-plugin/plugin.json' -type f -exec jq -r '.name' {} \; | sort > "$TMP_ROOT/actual-names"
if diff -u "$TMP_ROOT/expected-names" "$TMP_ROOT/actual-names" >/dev/null; then
  pass "plugin directoryはlock記載の15件だけ"
else
  diff -u "$TMP_ROOT/expected-names" "$TMP_ROOT/actual-names" || true
  fail "plugin directoryの集合"
fi

for market in .agents/plugins/marketplace.json .claude-plugin/marketplace.json; do
  if jq -e '.plugins | length == 15' "$ROOT/$market" >/dev/null; then
    pass "$market は15件"
  else
    fail "$market の件数"
  fi
  jq -r '.plugins[].name' "$ROOT/$market" | sort > "$TMP_ROOT/market-names"
  if diff -u "$TMP_ROOT/expected-names" "$TMP_ROOT/market-names" >/dev/null; then
    pass "$market のplugin集合"
  else
    fail "$market のplugin集合"
  fi
done

if jq -e '.plugins | all(.[]; .policy.installation == "AVAILABLE" and .policy.authentication == "ON_INSTALL" and (.category | type == "string" and length > 0))' "$ROOT/.agents/plugins/marketplace.json" >/dev/null; then
  pass "Codex marketplace policy"
else
  fail "Codex marketplace policy"
fi

while IFS='|' read -r name version rel; do
  [ -n "$name" ] || continue
  plugin="$ROOT/$rel"
  if [ -d "$plugin" ]; then pass "$name root"; else fail "$name root欠落: $rel"; continue; fi

  for kind in codex claude; do
    manifest="$plugin/.$kind-plugin/plugin.json"
    if [ ! -f "$manifest" ]; then fail "$name $kind manifest欠落"; continue; fi
    got_name=$(jq -r '.name // ""' "$manifest")
    got_version=$(jq -r '.version // ""' "$manifest")
    if [ "$got_name" = "$name" ] && [ "$got_version" = "$version" ]; then
      pass "$name $kind manifest"
    else
      fail "$name $kind manifest name/version"
    fi
  done

  codex_source=$(jq -r --arg n "$name" '.plugins[] | select(.name==$n) | .source.path // ""' "$ROOT/.agents/plugins/marketplace.json")
  claude_source=$(jq -r --arg n "$name" '.plugins[] | select(.name==$n) | .source // ""' "$ROOT/.claude-plugin/marketplace.json")
  codex_version=$(jq -r --arg n "$name" '.plugins[] | select(.name==$n) | .version // ""' "$ROOT/.agents/plugins/marketplace.json")
  claude_version=$(jq -r --arg n "$name" '.plugins[] | select(.name==$n) | .version // ""' "$ROOT/.claude-plugin/marketplace.json")
  expected_source="./$rel"
  if [ "$codex_source" = "$expected_source" ] && [ "$claude_source" = "$expected_source" ] \
    && [ "$codex_version" = "$version" ] && [ "$claude_version" = "$version" ]; then
    pass "$name marketplace source/version"
  else
    fail "$name marketplace source/version"
  fi
done < <(jq -r '.plugins[] | [.name,.version,.path] | join("|")' "$ROOT/vendor-lock.json")

content_manifest_description=$(jq -r '.description' "$ROOT/plugins/skills/authoring/content-types/.claude-plugin/plugin.json")
content_marketplace_description=$(jq -r '.plugins[] | select(.name=="content-types") | .description' "$ROOT/.claude-plugin/marketplace.json")
if [ "$content_manifest_description" = "$content_marketplace_description" ] && ! rg -n '25種' "$ROOT/.claude-plugin/marketplace.json" >/dev/null; then
  pass "content-types Claude marketplace description"
else
  fail "content-types Claude marketplace description"
fi

if (cd "$ROOT" && python3 scripts/sync-skill-entry.py --check); then
  pass "SKILL起動blockはshared正本と一致"
else
  fail "SKILL起動block"
fi

while IFS= read -r plugin; do
  [ -n "$plugin" ] || continue
  if cmp -s "$ROOT/shared/prepare.sh" "$plugin/scripts/prepare.sh"; then
    pass "prepare byte一致: ${plugin#"$ROOT/"}"
  else
    fail "prepare byte差分: ${plugin#"$ROOT/"}"
  fi
done < <(find "$ROOT/plugins" -path '*/scripts/prepare.sh' -type f -exec dirname {} \; | xargs -n 1 dirname | sort)

while IFS= read -r resolver; do
  [ -n "$resolver" ] || continue
  plugin=$(dirname "$(dirname "$resolver")")
  if [ -f "$plugin/playbook.yml" ]; then source="$ROOT/shared/playbook/resolve.sh"; else source="$ROOT/shared/skill/resolve.sh"; fi
  if cmp -s "$source" "$resolver"; then
    pass "resolver byte一致: ${resolver#"$ROOT/"}"
  else
    fail "resolver byte差分: ${resolver#"$ROOT/"}"
  fi
done < <(find "$ROOT/plugins" -path '*/scripts/resolve.sh' -type f | sort)

if cmp -s "$ROOT/shared/playbook/state.py" "$ROOT/plugins/playbooks/authoring/write-doc/scripts/state.py"; then
  pass "write-doc state.py byte一致"
else
  fail "write-doc state.py byte差分"
fi

while IFS='|' read -r source copy; do
  [ -n "$source" ] || continue
  if cmp -s "$ROOT/$source" "$ROOT/$copy"; then
    pass "shared byte一致: $copy"
  else
    fail "shared byte差分: $source -> $copy"
  fi
done <<'MAPPINGS'
shared/domain-modeling/domain.md|plugins/skills/domain/core-domain/references/domain.md
shared/domain-modeling/subdomains.md|plugins/skills/domain/core-domain/references/subdomains.md
shared/domain-modeling/bounded-contexts.md|plugins/skills/domain/core-domain/references/bounded-contexts.md
shared/domain-modeling/concept-map.md|plugins/skills/domain/core-domain/references/concept-map.md
shared/domain-modeling/domain-rules.md|plugins/playbooks/bdd/domain-bdd-discovery/references/domain-rules.md
shared/domain-modeling/actors-and-stakeholders.md|plugins/playbooks/bdd/domain-bdd-discovery/references/actors-and-stakeholders.md
shared/domain-modeling/ubiquitous-language.md|plugins/playbooks/bdd/domain-bdd-discovery/references/ubiquitous-language.md
shared/domain-modeling/actors-and-stakeholders.md|plugins/skills/domain/domain-events/references/actors-and-stakeholders.md
shared/domain-modeling/use-cases.md|plugins/skills/domain/domain-events/references/use-cases.md
shared/domain-modeling/domain-events.md|plugins/skills/domain/domain-events/references/domain-events.md
shared/data-modeling/event-sourcing.md|plugins/skills/domain/domain-events/references/event-sourcing.md
shared/domain-modeling/concept-map.md|plugins/skills/domain/domain-events/references/concept-map.md
shared/domain-modeling/domain-events.md|plugins/skills/data-modeling/data-model/references/domain-events.md
shared/data-modeling/event-sourcing.md|plugins/skills/data-modeling/data-model/references/event-sourcing.md
shared/data-modeling/data-models.md|plugins/skills/data-modeling/data-model/references/data-models.md
shared/domain-modeling/concept-map.md|plugins/skills/data-modeling/data-model/references/concept-map.md
shared/data-modeling/immutable-data-modeling.md|plugins/skills/data-modeling/data-model/references/immutable-data-modeling.md
shared/data-modeling/relational-data-modeling-principles.md|plugins/skills/data-modeling/data-model/references/relational-data-modeling-principles.md
shared/data-modeling/null-avoidance.md|plugins/skills/data-modeling/data-model/references/null-avoidance.md
shared/data-modeling/relational-data-lifecycle.md|plugins/skills/data-modeling/data-model/references/relational-data-lifecycle.md
shared/domain-modeling/actors-and-stakeholders.md|plugins/skills/data-modeling/persistence-scenarios/references/actors-and-stakeholders.md
shared/domain-modeling/use-cases.md|plugins/skills/data-modeling/persistence-scenarios/references/use-cases.md
shared/domain-modeling/domain-events.md|plugins/skills/data-modeling/persistence-scenarios/references/domain-events.md
shared/domain-modeling/ubiquitous-language.md|plugins/skills/data-modeling/persistence-scenarios/references/ubiquitous-language.md
shared/data-modeling/immutable-data-modeling.md|plugins/skills/data-modeling/persistence-scenarios/references/immutable-data-modeling.md
shared/data-modeling/relational-data-modeling-principles.md|plugins/skills/data-modeling/rdb-design/references/relational-data-modeling-principles.md
shared/data-modeling/null-avoidance.md|plugins/skills/data-modeling/rdb-design/references/null-avoidance.md
shared/data-modeling/relational-data-lifecycle.md|plugins/skills/data-modeling/rdb-design/references/relational-data-lifecycle.md
shared/data-modeling/transaction-isolation.md|plugins/skills/data-modeling/rdb-design/references/transaction-isolation.md
shared/quality-engineering/important-scenarios.md|plugins/playbooks/bdd/domain-bdd-formulation/references/important-scenarios.md
shared/quality-engineering/important-scenarios.md|plugins/playbooks/bdd/data-model-bdd-formulation/references/important-scenarios.md
shared/quality-engineering/formulation-readiness.md|plugins/playbooks/bdd/domain-bdd-formulation/references/formulation-readiness.md
shared/quality-engineering/formulation-readiness.md|plugins/playbooks/bdd/data-model-bdd-formulation/references/formulation-readiness.md
shared/quality-engineering/input-grounding.md|plugins/playbooks/bdd/domain-bdd-discovery/references/input-grounding.md
shared/quality-engineering/input-grounding.md|plugins/playbooks/bdd/data-model-bdd-discovery/references/input-grounding.md
shared/quality-engineering/input-grounding.md|plugins/playbooks/bdd/domain-bdd-formulation/references/input-grounding.md
shared/quality-engineering/input-grounding.md|plugins/playbooks/bdd/data-model-bdd-formulation/references/input-grounding.md
MAPPINGS

if find "$ROOT/plugins" -type d \( -name '*slack*' -o -name '*meeting*' -o -name '*session*' -o -name '*cadence*' -o -name '*agent-run*' -o -name '*pull-request*' -o -name '*journey*' -o -name '*use-case*' \) | grep -q .; then
  fail "除外対象plugin directoryが混入"
else
  pass "除外対象plugin directoryなし"
fi

syntax_failed=0
while IFS= read -r script; do
  bash -n "$script" || syntax_failed=1
done < <(find "$ROOT/plugins" "$ROOT/scripts" -type f -name '*.sh' | sort)
if [ "$syntax_failed" -eq 0 ]; then pass "shell構文"; else fail "shell構文"; fi

python_failed=0
while IFS= read -r script; do
  PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile "$script" || python_failed=1
done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.py' | sort)
if [ "$python_failed" -eq 0 ]; then pass "Python構文"; else fail "Python構文"; fi

if find "$ROOT" -type d -name '__pycache__' | grep -q .; then fail "配布対象内に__pycache__が残った"; else pass "生成物なし"; fi

fixture="$ROOT/fixtures/electronic-ticket-entry-exit-exercise.md"
if [ -f "$fixture" ] && ! rg -n '探索に使う代表的な場面|参加者が確認すべき問い|推奨回答|場面[A-Z]:' "$fixture" >/dev/null; then
  pass "電子チケットお題に探索ヒント見出しなし"
else
  fail "電子チケットお題の存在またはヒント混入"
fi

content_types="$ROOT/plugins/skills/authoring/content-types"
jq -r '.pairs | keys[]' < <(yq -o=json "$content_types/assets/template-examples.yml") | sort > "$TMP_ROOT/content-type-pairs"
printf '%s\n' domain-rule rdb-logical-data-modeling | sort > "$TMP_ROOT/expected-content-types"
find "$content_types/assets/templates" -type f -name '*.md' -exec basename {} .md \; | sort > "$TMP_ROOT/content-type-templates"
find "$content_types/assets/examples" -type f -name '*.example.md' -exec basename {} .example.md \; | sort > "$TMP_ROOT/content-type-examples"
find "$content_types/references/detail" -type f -name '*.md' -exec basename {} .md \; | sort > "$TMP_ROOT/content-type-details"
printf '%s\n' domain data-modeling | sort > "$TMP_ROOT/expected-content-details"
if diff -u "$TMP_ROOT/expected-content-types" "$TMP_ROOT/content-type-pairs" >/dev/null \
  && diff -u "$TMP_ROOT/expected-content-types" "$TMP_ROOT/content-type-templates" >/dev/null \
  && diff -u "$TMP_ROOT/expected-content-types" "$TMP_ROOT/content-type-examples" >/dev/null \
  && diff -u "$TMP_ROOT/expected-content-details" "$TMP_ROOT/content-type-details" >/dev/null; then
  pass "content-typesはBDD用2型だけ"
else
  fail "content-typesの公開型・template・example境界"
fi
if rg -n -i 'slack' "$content_types" >/dev/null; then fail "content-typesへSlack資産が混入"; else pass "content-typesにSlack資産なし"; fi

printf '\nStructure: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
