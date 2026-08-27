#!/usr/bin/env bash
# Scenario: runtime別cacheから完全修飾依存だけを解決し、不正系はfail closedする
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-runtime.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
REPO="$TMP_ROOT/repo"
CACHE="$TMP_ROOT/cache"
mkdir -p "$REPO"
git -C "$REPO" init -q
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }

fixture_plugin() {
  market=$1 plugin=$2 version=$3 kind=$4 skill=$5
  root="$CACHE/$market/$plugin/$version"
  mkdir -p "$root/.codex-plugin" "$root/.claude-plugin" "$root/scripts"
  printf '{"name":"%s","version":"%s"}\n' "$plugin" "$version" > "$root/.codex-plugin/plugin.json"
  printf '{"name":"%s","version":"%s"}\n' "$plugin" "$version" > "$root/.claude-plugin/plugin.json"
  printf -- '---\nname: %s\ndescription: fixture\n---\n' "$skill" > "$root/SKILL.md"
  if [ "$kind" = playbook ]; then
    printf 'version: 2\nname: %s\n' "$plugin" > "$root/playbook.yml"
    printf '#!/usr/bin/env bash\nexit 0\n' > "$root/scripts/resolve.sh"
    chmod +x "$root/scripts/resolve.sh"
  fi
}

fixture_plugin grill grill 0.2.13 skill grill
fixture_plugin write-doc write-doc 0.6.0 playbook write-doc
fixture_plugin write-doc writing-rules 0.4.15 skill write-with-rules

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation'
for runtime in codex claude; do
  for directory in $entries; do
    pb="$ROOT/plugins/playbooks/bdd/$directory"
    out="$TMP_ROOT/$runtime-$directory.yml"
    if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$pb/scripts/resolve.sh" "$REPO" > "$out" 2> "$out.err" \
      && yq -o=json -I=0 '.' "$out" | jq -e --arg runtime "$runtime" 'all(.deps[]; .runtime==$runtime)' >/dev/null; then
      pass "$runtime/$directory exact dependency resolution"
    else
      fail "$runtime/$directory exact dependency resolution"
    fi
  done
done

entry="$ROOT/plugins/playbooks/bdd/domain-bdd-discovery"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$TMP_ROOT/missing" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/missing.err"; then
  fail "missing dependencyを許可"
elif rg -n '\[error:dependency-missing\].*marketplace=grill.*version=0.2.13' "$TMP_ROOT/missing.err" >/dev/null; then
  pass "missing dependencyはidentity付きで停止"
else
  fail "missing dependency error contract"
fi

mv "$CACHE/grill/grill/0.2.13/.codex-plugin/plugin.json" "$TMP_ROOT/grill-manifest"
printf '{"name":"grill","version":"9.9.9"}\n' > "$CACHE/grill/grill/0.2.13/.codex-plugin/plugin.json"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/version.err"; then
  fail "manifest版違いを許可"
elif rg -n '\[error:dependency-invalid\].*manifest-identity-mismatch' "$TMP_ROOT/version.err" >/dev/null; then
  pass "manifest版違いを停止"
else
  fail "manifest版違いerror contract"
fi
mv "$TMP_ROOT/grill-manifest" "$CACHE/grill/grill/0.2.13/.codex-plugin/plugin.json"

if HARNESS_PLUGIN_CACHE_ROOT="$CACHE" CODEX_HOME= CLAUDE_PLUGIN_ROOT= bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/runtime.err"; then
  fail "runtime不明を許可"
elif rg -n '\[error:dependency-runtime-unresolved\]' "$TMP_ROOT/runtime.err" >/dev/null; then
  pass "runtime不明を停止"
else
  fail "runtime不明error contract"
fi

mkdir -p "$REPO/.harness-plugins"
yq -o=json -I=0 '.' "$entry/playbook.yml" | jq '.requires[0]=.requires[0].plugin' | yq -P > "$REPO/.harness-plugins/domain-bdd-discovery.config.yml"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/bare.err"; then
  fail "bare dependency nameを許可"
else
  pass "schema v2はbare dependency nameを拒否"
fi

printf '\nRuntime: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
