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
write_doc_package="$CACHE/write-doc/write-doc/0.6.0"
mkdir -p "$write_doc_package/entry" "$write_doc_package/skills/writing-rules" "$write_doc_package/skills/write-doc-cleanup"
mv "$write_doc_package/SKILL.md" "$write_doc_package/playbook.yml" "$write_doc_package/scripts" "$write_doc_package/entry/"
printf -- '---\nname: write-with-rules\ndescription: fixture\n---\n' > "$write_doc_package/skills/writing-rules/SKILL.md"
printf -- '---\nname: remove-intermediate-artifacts\ndescription: fixture\n---\n' > "$write_doc_package/skills/write-doc-cleanup/SKILL.md"
for runtime in codex claude; do
  jq '.skills=["./entry","./skills/writing-rules","./skills/write-doc-cleanup"] | .metadata.harness.entryRoot="./entry"' \
    "$write_doc_package/.$runtime-plugin/plugin.json" > "$TMP_ROOT/write-doc-$runtime.json"
  mv "$TMP_ROOT/write-doc-$runtime.json" "$write_doc_package/.$runtime-plugin/plugin.json"
done
fixture_plugin bdd-discovery-and-formulation user-journey 0.1.0 skill map-user-journey

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation'
entry="$ROOT/plugins/playbooks/bdd/domain-bdd-discovery"
for runtime in codex claude; do
  for directory in $entries; do
    pb="$ROOT/plugins/playbooks/bdd/$directory"
    out="$TMP_ROOT/$runtime-$directory.yml"
    if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" bash "$pb/scripts/resolve.sh" "$REPO" > "$out" 2> "$out.err" \
      && yq -o=json -I=0 '.' "$out" | jq -e --arg runtime "$runtime" \
        'all(.deps[]; .runtime==$runtime) and .deps.grill.version=="9.9.9" and .deps["write-doc"].source_kind=="installed-cache"' >/dev/null; then
      pass "$runtime/$directory name dependency resolution"
    else
      fail "$runtime/$directory name dependency resolution"
    fi
  done
done

# 開発時も別repositoryの公開playbook packageだけを明示mapへ渡す。
dev_map="$TMP_ROOT/dev-roots.json"
jq -n --arg root "$write_doc_package" \
  '{schema:1,dependencies:{"write-doc/write-doc":$root}}' > "$dev_map"
write_doc_root=$(cd "$write_doc_package" && pwd -P)
write_doc_entry=$(cd "$write_doc_package/entry" && pwd -P)
for runtime in codex claude; do
  if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
      bash "$entry/scripts/resolve.sh" "$REPO" 2> "$TMP_ROOT/dev-$runtime.err" \
      | yq -o=json -I=0 '.' | jq -e --arg root "$write_doc_entry" \
        '.deps["write-doc"].source_kind=="dev-map" and .deps["write-doc"].root==$root' >/dev/null; then
    pass "$runtime/dev-mapの公開write-doc packageからcleanup skillを解決"
  else
    fail "$runtime/dev-mapの明示rootでcleanup skillを解決"
  fi
done

mv "$write_doc_package/skills/write-doc-cleanup/SKILL.md" "$TMP_ROOT/cleanup-skill"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$CACHE" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
    bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/dev-no-skill.err"; then
  fail "dev-map rootに必要skillが無い状態を許可"
else
  pass "dev-map rootに必要skillが無い状態を拒否"
fi
mv "$TMP_ROOT/cleanup-skill" "$write_doc_package/skills/write-doc-cleanup/SKILL.md"

# package内部のskillがcacheに存在しても、外部repositoryから内部plugin名では解決できない。
for runtime in codex claude; do
  if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$CACHE" \
      python3 "$entry/scripts/resolve-dependency.py" \
      --plugin-root "$entry" --plugin write-doc-cleanup --marketplace write-doc \
      >/dev/null 2> "$TMP_ROOT/internal-$runtime.err"; then
    fail "$runtime/外部repositoryから内部plugin名を解決"
  else
    pass "$runtime/外部repositoryから内部plugin名を拒否"
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
