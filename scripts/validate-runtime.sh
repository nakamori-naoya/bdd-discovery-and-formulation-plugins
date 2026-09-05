#!/usr/bin/env bash
# Scenario: runtime別cacheから名前一致の依存を解決し、不正系はfail closedする
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
fixture_plugin grill grill 9.9.9 skill grill
fixture_plugin write-doc write-doc 0.6.0 playbook write-doc
fixture_plugin write-doc writing-rules 0.4.15 skill write-with-rules
fixture_plugin write-doc write-doc-cleanup 0.1.0 skill remove-intermediate-artifacts
fixture_plugin bdd-discovery-and-formulation user-journey 0.1.0 skill map-user-journey

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation'
entry="$ROOT/plugins/playbooks/bdd/domain-bdd-discovery"
for runtime in codex claude; do
  for directory in $entries; do
    pb="$ROOT/plugins/playbooks/bdd/$directory"
    out="$TMP_ROOT/$runtime-$directory.yml"
    if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$pb/scripts/resolve.sh" "$REPO" > "$out" 2> "$out.err" \
      && yq -o=json -I=0 '.' "$out" | jq -e --arg runtime "$runtime" \
        'all(.deps[]; .runtime==$runtime) and .deps.grill.version=="9.9.9" and .deps["write-doc-cleanup"].source_kind=="installed-cache"' >/dev/null; then
      pass "$runtime/$directory name dependency resolution"
    else
      fail "$runtime/$directory name dependency resolution"
    fi
  done
done

# 開発時は兄弟repositoryの内部構造を仮定せず、利用者が渡す marketplace/plugin root
# の明示mapだけを標準resolverへ渡す。両runtimeで必要skillまで解決できることを確かめる。
dev_map="$TMP_ROOT/dev-roots.json"
jq -n --arg root "$CACHE/write-doc/write-doc-cleanup/0.1.0" \
  '{schema:1,dependencies:{"write-doc/write-doc-cleanup":$root}}' > "$dev_map"
cleanup_root=$(cd "$CACHE/write-doc/write-doc-cleanup/0.1.0" && pwd -P)
for runtime in codex claude; do
  if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
      bash "$entry/scripts/resolve.sh" "$REPO" 2> "$TMP_ROOT/dev-$runtime.err" \
      | yq -o=json -I=0 '.' | jq -e --arg root "$cleanup_root" \
        '.deps["write-doc-cleanup"].source_kind=="dev-map" and .deps["write-doc-cleanup"].root==$root' >/dev/null; then
    pass "$runtime/dev-mapの明示rootでcleanup skillを解決"
  else
    fail "$runtime/dev-mapの明示rootでcleanup skillを解決"
  fi
done

mv "$CACHE/write-doc/write-doc-cleanup/0.1.0/SKILL.md" "$TMP_ROOT/cleanup-skill"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
    bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/dev-no-skill.err"; then
  fail "dev-map rootに必要skillが無い状態を許可"
else
  pass "dev-map rootに必要skillが無い状態を拒否"
fi
mv "$TMP_ROOT/cleanup-skill" "$CACHE/write-doc/write-doc-cleanup/0.1.0/SKILL.md"

# repository marketplaceからの解決も、cacheや兄弟repository名に頼らず両runtimeで行う。
repo_market="$TMP_ROOT/repository-market"
mkdir -p "$repo_market/consumer/.codex-plugin" "$repo_market/consumer/.claude-plugin" "$repo_market/cleanup/.codex-plugin" "$repo_market/cleanup/.claude-plugin" "$repo_market/.agents/plugins" "$repo_market/.claude-plugin"
printf '{"name":"consumer","version":"1.0.0"}\n' > "$repo_market/consumer/.codex-plugin/plugin.json"
printf '{"name":"consumer","version":"1.0.0"}\n' > "$repo_market/consumer/.claude-plugin/plugin.json"
printf '{"name":"write-doc-cleanup","version":"1.0.0"}\n' > "$repo_market/cleanup/.codex-plugin/plugin.json"
printf '{"name":"write-doc-cleanup","version":"1.0.0"}\n' > "$repo_market/cleanup/.claude-plugin/plugin.json"
printf '%s\n' '---' 'name: remove-intermediate-artifacts' 'description: fixture' '---' > "$repo_market/cleanup/SKILL.md"
printf '{"name":"write-doc","plugins":[{"name":"write-doc-cleanup","source":{"source":"local","path":"./cleanup"}}]}\n' > "$repo_market/.agents/plugins/marketplace.json"
printf '{"name":"write-doc","plugins":[{"name":"write-doc-cleanup","source":"./cleanup"}]}\n' > "$repo_market/.claude-plugin/marketplace.json"
for runtime in codex claude; do
  repository_cleanup_root=$(cd "$repo_market/cleanup" && pwd -P)
  if HARNESS_PLUGIN_RUNTIME="$runtime" python3 "$ROOT/shared/playbook/resolve-dependency.py" \
      --plugin-root "$repo_market/consumer" --plugin write-doc-cleanup --marketplace write-doc \
      | jq -e --arg runtime "$runtime" --arg root "$repository_cleanup_root" \
        '.runtime==$runtime and .source_kind=="repository" and .root==$root' >/dev/null; then
    pass "$runtime/repository marketplaceでcleanupを解決"
  else
    fail "$runtime/repository marketplaceでcleanupを解決"
  fi
done

if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$TMP_ROOT/missing" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/missing.err"; then
  fail "missing dependencyを許可"
elif rg -n '\[error:dependency-missing\].*plugin=grill.*marketplace=grill.*runtime=codex' "$TMP_ROOT/missing.err" >/dev/null; then
  pass "missing dependencyはidentity付きで停止"
else
  fail "missing dependency error contract"
fi

mv "$CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json" "$TMP_ROOT/grill-manifest"
printf '{"name":"not-grill","version":"9.9.9"}\n' > "$CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/name.err"; then
  fail "manifest名違いを許可"
elif rg -n '\[error:dependency-invalid\].*manifest-identity-mismatch' "$TMP_ROOT/name.err" >/dev/null; then
  pass "manifest名違いを停止"
else
  fail "manifest名違いerror contract"
fi
mv "$TMP_ROOT/grill-manifest" "$CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json"

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

yq -o=json -I=0 '.' "$entry/playbook.yml" | jq '.requires[0].version="0.2.13"' | yq -P > "$REPO/.harness-plugins/domain-bdd-discovery.config.yml"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/pin.err"; then
  fail "dependency version pinを許可"
else
  pass "schema v2はdependency version pinを拒否"
fi

printf '\nRuntime: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
