#!/usr/bin/env bash
# Scenario: 4入口が依存を解決し、入力根拠の制約を実行時に強制する
# Given: BDD依存閉包の16 pluginを同一marketplace rootへ隔離配置している
# When: resolver、全skill工程のprepare、意図的に壊した設定を実行する
# Then: 正常系は成功し、不正な設定・欠落依存・呼べない工程は必ず失敗する
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/knowledge-hub-bdd-runtime.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
FIXTURE="$TMP_ROOT/repo"
mkdir -p "$FIXTURE"
git -C "$FIXTURE" init -q

passed=0
failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }

for cmd in jq yq git rsync rg sed; do
  if command -v "$cmd" >/dev/null 2>&1; then pass "command $cmd"; else fail "command $cmd が無い"; fi
done

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation'

for directory in $entries; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  out="$TMP_ROOT/$directory.yml"
  err="$TMP_ROOT/$directory.err"
  if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$pb/scripts/resolve.sh" "$FIXTURE" >"$out" 2>"$err" \
    && [ -s "$out" ] && [ ! -s "$err" ]; then
    pass "$directory resolver成功・stderr空"
  else
    fail "$directory resolver"
  fi

  prepare_out="$TMP_ROOT/$directory.prepare.out"
  prepare_err="$TMP_ROOT/$directory.prepare.err"
  if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$pb/scripts/prepare.sh" "$FIXTURE" >"$prepare_out" 2>"$prepare_err"; then
    cfg=$(sed -n '$p' "$prepare_out")
    [ -f "$cfg" ] && rm -f "$cfg"
    if rg -n '^\[error\]' "$prepare_err" >/dev/null; then
      fail "$directory prepare成功時にerror出力"
    else
      pass "$directory prepare成功（resolverのexplain出力を許容）"
    fi
  else
    fail "$directory prepare"
  fi
done

write_doc="$ROOT/plugins/playbooks/authoring/write-doc"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$write_doc/scripts/resolve.sh" "$FIXTURE" >"$TMP_ROOT/write-doc.yml" 2>"$TMP_ROOT/write-doc.err" \
  && [ -s "$TMP_ROOT/write-doc.yml" ] && [ ! -s "$TMP_ROOT/write-doc.err" ]; then
  pass "write-doc resolver成功・stderr空"
else
  fail "write-doc resolver"
fi

negative_case() {
  label="$1" pb="$2" filter="$3"
  case_file="$TMP_ROOT/negative.json"
  yq -o=json -I=0 '.' "$pb/playbook.yml" | jq "$filter" > "$case_file"
  if bash "$pb/scripts/validate-config.sh" "$case_file" >/dev/null 2>&1; then
    fail "$label を拒否しなかった"
  else
    pass "$label を拒否"
  fi
}

data_discovery="$ROOT/plugins/playbooks/bdd/data-model-bdd-discovery"
negative_case "data-model-bdd-discovery modeling.method欠落" "$data_discovery" 'del(.modeling.method)'
negative_case "data-model-bdd-discovery modeling.method空" "$data_discovery" '.modeling.method=""'
data_formulation="$ROOT/plugins/playbooks/bdd/data-model-bdd-formulation"
negative_case "data-model-bdd-formulation modeling.method欠落" "$data_formulation" 'del(.modeling.method)'
negative_case "data-model-bdd-formulation modeling.method空" "$data_formulation" '.modeling.method=""'

for directory in $entries; do
  pb="$ROOT/plugins/playbooks/bdd/$directory"
  negative_case "$directory grounding_sources変更" "$pb" '.contract.grounding_sources=["user_input"]'
  negative_case "$directory 先頭grill欠落" "$pb" 'del(.steps[0])'
  negative_case "$directory 後続grounded_input欠落" "$pb" '.steps[1].needs = [.steps[1].needs[] | select(. != "grounded_input")]'
  negative_case "$directory input_grounded=false" "$pb" '.requirements.input_grounded=false'
  negative_case "$directory clarify_with_grill=false" "$pb" '.requirements.clarify_with_grill=false'
  negative_case "$directory grillが第2工程" "$pb" '.steps = [.steps[1], .steps[0]] + .steps[2:]'
  negative_case "$directory grillのgrounded_input提供欠落" "$pb" '.steps[0].provides = [.steps[0].provides[] | select(. != "grounded_input")]'
  negative_case "$directory 最終cleanup欠落" "$pb" 'del(.steps[-1])'
  negative_case "$directory cleanupが最終工程でない" "$pb" '.steps = (.steps[0:-2] + [.steps[-1], .steps[-2]])'
done

copy_case() {
  destination="$1"
  mkdir -p "$destination"
  rsync -a --exclude VALIDATION.md "$ROOT/" "$destination/"
}

case_root="$TMP_ROOT/missing-dependency"
copy_case "$case_root"
rm -f "$case_root/plugins/skills/authoring/grill/.claude-plugin/plugin.json"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$case_root/plugins/playbooks/bdd/domain-bdd-discovery/scripts/resolve.sh" "$FIXTURE" >/dev/null 2>&1; then
  fail "依存manifest欠落を拒否しなかった"
else
  pass "依存manifest欠落を拒否"
fi

case_root="$TMP_ROOT/missing-skill"
copy_case "$case_root"
rm -f "$case_root/plugins/skills/authoring/grill/SKILL.md"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$case_root/plugins/playbooks/bdd/domain-bdd-discovery/scripts/resolve.sh" "$FIXTURE" >/dev/null 2>&1; then
  fail "依存skill欠落を拒否しなかった"
else
  pass "依存skill欠落を拒否"
fi

case_root="$TMP_ROOT/missing-cleanup-dependency"
copy_case "$case_root"
rm -f "$case_root/plugins/skills/authoring/intermediate-cleanup/.claude-plugin/plugin.json"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$case_root/plugins/playbooks/bdd/domain-bdd-discovery/scripts/resolve.sh" "$FIXTURE" >/dev/null 2>&1; then
  fail "cleanup依存manifest欠落を拒否しなかった"
else
  pass "cleanup依存manifest欠落を拒否"
fi

case_root="$TMP_ROOT/missing-script"
copy_case "$case_root"
rm -f "$case_root/plugins/playbooks/bdd/domain-bdd-discovery/scripts/map.py"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$case_root/plugins/playbooks/bdd/domain-bdd-discovery/scripts/resolve.sh" "$FIXTURE" >/dev/null 2>&1; then
  fail "入口script欠落を拒否しなかった"
else
  pass "入口script欠落を拒否"
fi

case_root="$TMP_ROOT/missing-nested-script"
copy_case "$case_root"
rm -f "$case_root/plugins/skills/authoring/doc-render/scripts/write-doc.sh"
if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$case_root/plugins/playbooks/authoring/write-doc/scripts/resolve.sh" "$FIXTURE" >/dev/null 2>&1; then
  fail "入れ子保存script欠落を拒否しなかった"
else
  pass "入れ子保存script欠落を拒否"
fi

cleanup_script="$ROOT/plugins/skills/authoring/intermediate-cleanup/scripts/cleanup.py"
cleanup_repo="$TMP_ROOT/cleanup-repo"
mkdir -p "$cleanup_repo/work/nested" "$cleanup_repo/final"
git -C "$cleanup_repo" init -q
printf 'draft\n' > "$cleanup_repo/work/nested/draft.md"
printf 'final\n' > "$cleanup_repo/final/result.md"
if python3 "$cleanup_script" check --repo-root "$cleanup_repo" --delete "$cleanup_repo/work/nested/draft.md" --keep "$cleanup_repo/final/result.md" >/dev/null \
  && python3 "$cleanup_script" delete --repo-root "$cleanup_repo" --delete "$cleanup_repo/work/nested/draft.md" --keep "$cleanup_repo/final/result.md" >/dev/null \
  && [ ! -e "$cleanup_repo/work/nested/draft.md" ] && [ ! -d "$cleanup_repo/work" ] && [ -f "$cleanup_repo/final/result.md" ]; then
  pass "cleanupは明示した未追跡中間ファイルだけを削除"
else
  fail "cleanup正常系"
fi

printf 'tracked\n' > "$cleanup_repo/tracked.md"
git -C "$cleanup_repo" add tracked.md
if python3 "$cleanup_script" check --repo-root "$cleanup_repo" --delete "$cleanup_repo/tracked.md" --keep "$cleanup_repo/final/result.md" >/dev/null 2>&1; then
  fail "cleanupがGit追跡中ファイルを許可"
else
  pass "cleanupはGit追跡中ファイルを拒否"
fi

printf 'outside\n' > "$TMP_ROOT/outside.md"
if python3 "$cleanup_script" check --repo-root "$cleanup_repo" --delete "$TMP_ROOT/outside.md" --keep "$cleanup_repo/final/result.md" >/dev/null 2>&1; then
  fail "cleanupがrepository外ファイルを許可"
else
  pass "cleanupはrepository外ファイルを拒否"
fi

find_skill_root() {
  resolved="$1" wanted="$2"
  while IFS= read -r dep_root; do
    for skill_file in "$dep_root/SKILL.md" "$dep_root"/skills/*/SKILL.md; do
      [ -f "$skill_file" ] || continue
      skill_name=$(sed -n 's/^name: //p' "$skill_file" | head -1)
      [ "$skill_name" = "$wanted" ] || continue
      dirname "$skill_file" | sed 's|/skills/[^/]*$||'
      return 0
    done
  done < <(yq -r '.deps[]' "$resolved")
  return 1
}

prepare_skill() {
  entry="$1" resolved="$2" skill="$3"
  safe_entry=$(printf '%s' "$entry" | tr '/' '-')
  plugin_root=$(find_skill_root "$resolved" "$skill") || { fail "$entry/$skill のplugin root解決"; return; }
  scope=$(yq -r '.resolution.scope_root' "$resolved")
  if [ ! -x "$plugin_root/scripts/resolve.sh" ]; then
    if bash "$plugin_root/scripts/prepare.sh" --root-only >/dev/null 2>"$TMP_ROOT/prepare-$safe_entry-$skill.err"; then
      pass "$entry/$skill prepare --root-only"
    else
      fail "$entry/$skill prepare --root-only"
    fi
    return
  fi
  args=("$FIXTURE" "--scope=$scope")
  if [ "$skill" = "design-data-model" ]; then
    method=$(yq -r '.playbook.modeling.method // ""' "$resolved")
    [ -z "$method" ] || args+=("--override=method=$method")
  elif [ "$skill" = "design-rdb-persistence" ]; then
    product=$(yq -r '.playbook.database.product // ""' "$resolved")
    version=$(yq -r '.playbook.database.version // ""' "$resolved")
    [ -z "$product" ] || args+=("--override=database.product=$product")
    [ -z "$version" ] || args+=("--override=database.version=$version")
  fi
  out="$TMP_ROOT/prepare-$safe_entry-$skill.out"
  err="$TMP_ROOT/prepare-$safe_entry-$skill.err"
  if bash "$plugin_root/scripts/prepare.sh" "${args[@]}" >"$out" 2>"$err"; then
    cfg=$(sed -n '$p' "$out")
    [ -f "$cfg" ] && rm -f "$cfg"
    pass "$entry/$skill prepare"
  else
    detail=$(tr '\n' ' ' < "$err")
    fail "$entry/$skill prepare: $detail"
  fi
}

for directory in $entries; do
  resolved="$TMP_ROOT/$directory.yml"
  [ -s "$resolved" ] || continue
  while IFS= read -r skill; do
    prepare_skill "$directory" "$resolved" "$skill"
  done < <(yq -r '.playbook.steps[] | select(.skill != null) | .skill' "$resolved")
done

while IFS= read -r skill; do
  prepare_skill "write-doc" "$TMP_ROOT/write-doc.yml" "$skill"
done < <(yq -r '.playbook.steps[] | select(.skill != null) | .skill' "$TMP_ROOT/write-doc.yml")

for directory in $entries; do
  parent="$TMP_ROOT/$directory.yml"
  yq -e '.playbook.steps[] | select(.playbook=="write-doc")' "$parent" >/dev/null || continue
  scope=$(yq -r '.resolution.scope_root' "$parent")
  nested="$TMP_ROOT/$directory.write-doc.yml"
  err="$TMP_ROOT/$directory.write-doc.err"
  if CLAUDE_MARKETPLACE=knowledge-hub-bdd-prototype bash "$write_doc/scripts/resolve.sh" "$FIXTURE" "--scope=$scope" >"$nested" 2>"$err" \
    && [ "$(yq -r '.resolution.scope_root' "$nested")" = "$scope" ] && [ ! -s "$err" ]; then
    pass "$directory -> write-doc scope伝播"
  else
    fail "$directory -> write-doc scope伝播"
    continue
  fi
  while IFS= read -r skill; do
    prepare_skill "$directory/write-doc" "$nested" "$skill"
  done < <(yq -r '.playbook.steps[] | select(.skill != null) | .skill' "$nested")
done

printf '\nRuntime: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
