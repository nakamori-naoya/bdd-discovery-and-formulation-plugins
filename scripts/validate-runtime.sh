#!/usr/bin/env bash
# Scenario: runtime別cacheから公開playbookだけを解決し、規則違反と不正系はfail closedする
#
# ここで固定するのは「外部pluginの公開面はplaybook 1枚だけ」という規則である。
# fixtureは公開契約（metadata.harness.marketplace / implements）を宣言した形だけを作り、
# 相手の中の作りを消費側から掴む形は、どれも赤にする。
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

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation'

# 公開playbook packageのfixture。契約IDを implements で自己宣言し、
# 入口4点（playbook.yml / scripts/resolve.sh / scripts/prepare.sh / SKILL.md）を持つ。
fixture_playbook_package() {
  market=$1 plugin=$2 version=$3 skill=$4 types=$5
  root="$CACHE/$market/$plugin/$version"
  mkdir -p "$root/.codex-plugin" "$root/.claude-plugin" "$root/entry/scripts"
  printf -- '---\nname: %s\ndescription: fixture\n---\n' "$skill" > "$root/entry/SKILL.md"
  printf 'version: 2\nname: %s\n' "$skill" > "$root/entry/playbook.yml"
  for script in resolve.sh prepare.sh; do
    printf '#!/usr/bin/env bash\nexit 0\n' > "$root/entry/scripts/$script"
    chmod +x "$root/entry/scripts/$script"
  done
  for runtime in codex claude; do
    jq -n --arg n "$plugin" --arg v "$version" --arg m "$market" --arg s "$skill" --argjson t "$types" '
      {name:$n, version:$v, skills:["./entry"],
       metadata:{harness:{installationSurface:"playbook-package", marketplace:$m,
         entryRoot:"./entry", playbooks:{($s):"./entry"}, contractVersion:1,
         implements:[({id:($m+"/"+$n), version:1, kind:"playbook", playbook:$s}
                      + (if $t==null then {} else {types:$t} end))]}}}' \
      > "$root/.$runtime-plugin/plugin.json"
  done
}

# 内部pluginを持つ提供側。内部の名前は公開skillにならないことを確かめるために使う。
add_internal_plugin() {
  root=$1 name=$2 skill=$3
  mkdir -p "$root/inner"
  printf -- '---\nname: %s\ndescription: fixture\n---\n' "$skill" > "$root/inner/SKILL.md"
  for runtime in codex claude; do
    jq --arg n "$name" '.metadata.harness.internalPlugins={($n):"./inner"}' \
      "$root/.$runtime-plugin/plugin.json" > "$TMP_ROOT/manifest.json"
    mv "$TMP_ROOT/manifest.json" "$root/.$runtime-plugin/plugin.json"
  done
}

fixture_playbook_package grill grill 0.2.13 grill null
fixture_playbook_package grill grill 9.9.9 grill null
fixture_playbook_package write-doc write-doc 0.6.0 write-doc \
  '["domain-rule","user-journey-bdd","rdb-logical-data-modeling"]'
write_doc_package="$CACHE/write-doc/write-doc/0.6.0"
add_internal_plugin "$write_doc_package" fixture-inner fixture-inner-skill

PACKAGE="$TMP_ROOT/package"
cp -R "$ROOT/plugins" "$PACKAGE"
CALLERS="$PACKAGE/playbooks/bdd"
for directory in $entries; do
  mkdir -p "$CALLERS/$directory/.harness-plugin-test-cache"
  cp -R "$CACHE/." "$CALLERS/$directory/.harness-plugin-test-cache/"
done
entry="$CALLERS/domain-bdd-discovery"
ENTRY_CACHE="$entry/.harness-plugin-test-cache"

for runtime in codex claude; do
  for directory in $entries; do
    pb="$CALLERS/$directory"
    out="$TMP_ROOT/$runtime-$directory.yml"
    if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$pb/.harness-plugin-test-cache" bash "$pb/scripts/resolve.sh" "$REPO" > "$out" 2> "$out.err" \
      && yq -o=json -I=0 '.' "$out" | jq -e --arg runtime "$runtime" '
        all(.deps[]; .runtime==$runtime) and .deps.grill.version=="9.9.9" and
        .deps["write-doc"].source_kind=="installed-cache" and
        .deps.grill.dependency_scope=="external" and .deps["write-doc"].dependency_scope=="external" and
        .deps.grill.contract=="grill/grill" and .deps["write-doc"].contract=="write-doc/write-doc" and
        (.deps["write-doc"].implements[0].playbook=="write-doc") and
        all(.deps[] | select(.marketplace=="bdd-discovery-and-formulation"); .dependency_scope=="internal")' >/dev/null; then
      pass "$runtime/$directory 公開playbookとして依存を解決"
    else
      fail "$runtime/$directory 公開playbookとして依存を解決"
    fi
  done
done

# 開発時も別repositoryの公開playbook packageだけを明示mapへ渡す。
dev_map="$TMP_ROOT/dev-roots.json"
jq -n --arg root "$write_doc_package" \
  '{schema:1,dependencies:{"write-doc/write-doc":$root}}' > "$dev_map"
write_doc_entry=$(cd "$write_doc_package/entry" && pwd -P)
for runtime in codex claude; do
  if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
      bash "$entry/scripts/resolve.sh" "$REPO" 2> "$TMP_ROOT/dev-$runtime.err" \
      | yq -o=json -I=0 '.' | jq -e --arg root "$write_doc_entry" \
        '.deps["write-doc"].source_kind=="dev-map" and .deps["write-doc"].root==$root' >/dev/null; then
    pass "$runtime/dev-mapの公開playbook packageを解決"
  else
    fail "$runtime/dev-mapの公開playbook packageを解決"
  fi
done

# ---- 規則の負の試験（外部pluginの公開面はplaybook 1枚だけ） -------------------
# 解決済みYAMLのstepsだけを書き換えて --check-steps へ渡す。
# 自分のvalidate-config.shより後段にある規則強制そのものを見るため、resolve.sh全体ではなくここを直接叩く。
resolver="$entry/scripts/resolve-dependency.py"
base_config="$TMP_ROOT/base-config.json"
HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" bash "$entry/scripts/resolve.sh" "$REPO" 2>/dev/null \
  | yq -o=json -I=0 '.' > "$base_config" || { fail "負の試験の土台となる解決に失敗"; }

expect_check_steps_error() {
  label=$1 filter=$2 pattern=$3
  if jq "$filter" "$base_config" | HARNESS_PLUGIN_RUNTIME=codex python3 "$resolver" --check-steps \
      >/dev/null 2> "$TMP_ROOT/mutant.err"; then
    fail "$label を許可"
  elif rg -n -- "$pattern" "$TMP_ROOT/mutant.err" >/dev/null; then
    pass "$label を停止"
  else
    fail "$label のerror contract（$(head -1 "$TMP_ROOT/mutant.err")）"
  fi
}

# 土台そのものは通ること。負の試験が「常に赤」で通っていないことを確かめる。
if jq '.' "$base_config" | HARNESS_PLUGIN_RUNTIME=codex python3 "$resolver" --check-steps >/dev/null 2>&1; then
  pass "規則検査の土台は緑"
else
  fail "規則検査の土台が赤（負の試験が意味を持たない）"
fi

# (1) 外部pluginを skill: で直接呼ぶ形に戻す。
expect_check_steps_error "外部pluginの公開skillをskill:で呼ぶ形" \
  '(.playbook.steps[0]) |= (del(.playbook) | .skill="grill")' \
  '\[error:external-dependency-skill\].*step=settle.*skill=grill'

# (2) 外部pluginの内部skillを名指しする。
expect_check_steps_error "外部pluginの内部skillの名指し" \
  '(.playbook.steps[-1]) |= (del(.script) | .skill="fixture-inner-skill")' \
  'steps が指すスキルが requires のプラグインに無い: fixture-inner-skill'

# (3) 外部pluginのscriptを script: + plugin: で実行する。
expect_check_steps_error "外部pluginのscript実行" \
  '(.playbook.steps[-1]) |= (.script="scripts/write.sh" | .plugin="write-doc")' \
  '\[error:external-dependency-script\].*plugin=write-doc'

# (4) 公開面4点以外のpathを外部rootから組み立てる。
expect_check_steps_error "外部root配下のpath組み立て" \
  '(.playbook.steps[-1].purpose) |= (. + " ${.deps[\"write-doc\"].root}/scripts/write-anything.sh")' \
  '\[error:external-dependency-path\].*plugin=write-doc'

# (4b)(4c) 廃止した参照形。禁止語をこのファイルへ literal で書くと消費側lintが正しく赤にするので、
# 検査したい形は組み立てて渡す。検査の中身は変わらない。
forbidden_tail='.skills.write-doc}'
expect_check_steps_error "廃止した .skills.<名前> 形での入口参照" \
  "(.playbook.steps[] | select(.playbook==\"write-doc\") | .purpose) |= (. + \" \${.deps.write-doc${forbidden_tail}\")" \
  '\[error:external-dependency-path\].*plugin=write-doc'

# ブラケット形はドット形と同じsegment列へ正規化される。禁止形の密輸に使えないことを見る。
expect_check_steps_error "ブラケット形で禁止segmentを渡す" \
  "(.playbook.steps[] | select(.playbook==\"write-doc\") | .purpose) |= (. + \" \${.deps[\\\"write-doc\\\"]${forbidden_tail}\")" \
  '\[error:external-dependency-path\].*plugin=write-doc'

# (4d) 公開面の1形である .entry は、ドット形でもブラケット形でも通ること。
for form in '${.deps.write-doc.entry}' '${.deps["write-doc"].entry}'; do
  if jq --arg ref "$form" '(.playbook.steps[] | select(.playbook=="write-doc") | .purpose) |= (. + " " + $ref)' "$base_config" \
      | HARNESS_PLUGIN_RUNTIME=codex python3 "$resolver" --check-steps >/dev/null 2>&1; then
    pass "公開面の .entry 参照は通る（${form}）"
  else
    fail "公開面の .entry 参照を拒否している（${form}）"
  fi
done

# (5) when付きの非活性stepへ違反を隠す。
expect_check_steps_error "非活性stepへ隠した規則違反" \
  '(.playbook.steps[0]) |= (del(.playbook) | .skill="grill" | .when="false")' \
  '\[error:external-dependency-skill\]'

# (6) 実装していない文書型を渡す。
expect_check_steps_error "契約が実装していない文書型" \
  '(.playbook.steps[] | select(.playbook=="write-doc") | .input.document_type) |= "no-such-type"' \
  '\[error:binding-capability-unsupported\].*value=no-such-type'

# (7) 提供側が implements を宣言していない。
expect_check_steps_error "implements未宣言の提供側" \
  '(.deps["write-doc"].implements) |= []' \
  '\[error:dependency-changed\].*reason=implements'

# (8) 公開skillは提供側の公開面だけ。内部pluginの名前では解決できない。
for runtime in codex claude; do
  if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" \
      python3 "$resolver" --plugin-root "$entry" --plugin fixture-inner --marketplace write-doc \
      >/dev/null 2> "$TMP_ROOT/internal-$runtime.err"; then
    fail "$runtime/外部repositoryから内部plugin名を解決"
  else
    pass "$runtime/外部repositoryから内部plugin名を拒否"
  fi
done

# ---- 既存の不正系 -------------------------------------------------------------
mv "$ENTRY_CACHE/grill" "$TMP_ROOT/grill-cache"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/missing.err"; then
  fail "missing dependencyを許可"
elif rg -n '\[error:dependency-missing\].*plugin=grill.*marketplace=grill.*runtime=codex' "$TMP_ROOT/missing.err" >/dev/null; then
  pass "missing dependencyはidentity付きで停止"
else
  fail "missing dependency error contract"
fi
mv "$TMP_ROOT/grill-cache" "$ENTRY_CACHE/grill"

mv "$ENTRY_CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json" "$TMP_ROOT/grill-manifest"
printf '{"name":"not-grill","version":"9.9.9"}\n' > "$ENTRY_CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/name.err"; then
  fail "manifest名違いを許可"
elif rg -n '\[error:dependency-invalid\].*manifest-identity-mismatch' "$TMP_ROOT/name.err" >/dev/null; then
  pass "manifest名違いを停止"
else
  fail "manifest名違いerror contract"
fi
mv "$TMP_ROOT/grill-manifest" "$ENTRY_CACHE/grill/grill/9.9.9/.codex-plugin/plugin.json"

if HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" HARNESS_PLUGIN_RUNTIME= CODEX_HOME= CLAUDE_PLUGIN_ROOT= bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/runtime.err"; then
  fail "runtime不明を許可"
elif rg -n '\[error:dependency-runtime-unresolved\]' "$TMP_ROOT/runtime.err" >/dev/null; then
  pass "runtime不明を停止"
else
  fail "runtime不明error contract"
fi

mkdir -p "$REPO/.harness-plugins"
yq -o=json -I=0 '.' "$entry/playbook.yml" | jq '.requires[0]=.requires[0].plugin' | yq -P > "$REPO/.harness-plugins/domain-bdd-discovery.config.yml"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/bare.err"; then
  fail "bare dependency nameを許可"
else
  pass "schema v2はbare dependency nameを拒否"
fi

yq -o=json -I=0 '.' "$entry/playbook.yml" | jq '.requires[0].version="0.2.13"' | yq -P > "$REPO/.harness-plugins/domain-bdd-discovery.config.yml"
if HARNESS_PLUGIN_RUNTIME=codex HARNESS_PLUGIN_CACHE_ROOT="$ENTRY_CACHE" bash "$entry/scripts/resolve.sh" "$REPO" >/dev/null 2> "$TMP_ROOT/pin.err"; then
  fail "dependency version pinを許可"
else
  pass "schema v2はdependency version pinを拒否"
fi
rm -f "$REPO/.harness-plugins/domain-bdd-discovery.config.yml"

printf '\nRuntime: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
