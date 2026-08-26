#!/usr/bin/env bash
# Scenario: BDD marketplaceがBDD責務だけを配布し、外部依存を完全修飾している
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-structure.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }

for cmd in jq yq python3 bash cmp find sort diff rg; do
  command -v "$cmd" >/dev/null 2>&1 && pass "command $cmd" || fail "command $cmd が無い"
done

if jq -e '.name=="bdd-discovery-and-formulation" and (.plugins|length==10)' "$ROOT/.agents/plugins/marketplace.json" >/dev/null; then
  pass "Codex marketplaceの配布境界"
else
  fail "Codex marketplaceの配布境界"
fi

jq -r '.plugins[].name' "$ROOT/.agents/plugins/marketplace.json" | sort > "$TMP_ROOT/expected"
find "$ROOT/plugins" -path '*/.codex-plugin/plugin.json' -type f -exec jq -r '.name' {} \; | sort > "$TMP_ROOT/actual"
diff -u "$TMP_ROOT/expected" "$TMP_ROOT/actual" >/dev/null && pass "配布pluginは10件だけ" || fail "配布plugin集合"

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

for directory in domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e '.version==2 and (.requires|length>0) and all(.requires[]; (keys|sort)==["marketplace","plugin","version"])' >/dev/null; then
    pass "$directory qualified requirements"
  else
    fail "$directory qualified requirements"
  fi
  cmp -s "$ROOT/shared/playbook/resolve.sh" "$pb/scripts/resolve.sh" && pass "$directory resolver同期" || fail "$directory resolver同期"
  cmp -s "$ROOT/shared/playbook/resolve-dependency.py" "$pb/scripts/resolve-dependency.py" && pass "$directory dependency resolver同期" || fail "$directory dependency resolver同期"
done

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

syntax_failed=0
while IFS= read -r script; do bash -n "$script" || syntax_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" -type f -name '*.sh' | sort)
[ "$syntax_failed" -eq 0 ] && pass "shell構文" || fail "shell構文"

python_failed=0
while IFS= read -r script; do PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile "$script" || python_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.py' | sort)
[ "$python_failed" -eq 0 ] && pass "Python構文" || fail "Python構文"

printf '\nStructure: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
