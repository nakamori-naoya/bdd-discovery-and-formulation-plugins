#!/usr/bin/env bash
# Scenario: fixtureではなく実際に配布されている依存先packageに対して解決し、lintを通す
#
# fixtureだけで緑になる状態を許さない。fixtureは自分が書いた形しか持たないので、
# 相手が実際に何を公開しているかは、相手の配布物そのものに対してしか確かめられない。
#
# 依存先の実体は次の順で探す。
#   1. HARNESS_PLUGIN_REAL_ROOTS（契約ID→package rootのJSON。既に用意してあるとき）
#   2. 兄弟checkout <repo>/../<provider>-plugins/plugins
# どちらでも見つからなければ、この検査は落とす。見つからないことを緑にしない。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SIBLINGS=$(cd "$ROOT/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-real-distribution.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -q
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }

entries='domain-bdd-discovery domain-bdd-formulation data-model-bdd-discovery data-model-bdd-formulation user-journey-bdd-discovery user-journey-bdd-formulation'

dev_map="${HARNESS_PLUGIN_REAL_ROOTS:-}"
if [ -z "$dev_map" ]; then
  grill_root="$SIBLINGS/grill-plugins/plugins"
  write_doc_root="$SIBLINGS/write-doc-plugins/plugins"
  missing=""
  [ -d "$grill_root" ] || missing="${missing} grill/grill(${grill_root})"
  [ -d "$write_doc_root" ] || missing="${missing} write-doc/write-doc(${write_doc_root})"
  if [ -n "$missing" ]; then
    fail "実配布物が見つからない:${missing}"
    printf '  兄弟checkoutを置くか、契約ID→package rootのJSONを HARNESS_PLUGIN_REAL_ROOTS で渡す。\n'
    printf '\nReal distribution: %d passed, %d failed\n' "$passed" "$failed"
    exit 1
  fi
  dev_map="$TMP_ROOT/real-roots.json"
  jq -n --arg grill "$(cd "$grill_root" && pwd -P)" --arg doc "$(cd "$write_doc_root" && pwd -P)" \
    '{schema:1,dependencies:{"grill/grill":$grill,"write-doc/write-doc":$doc}}' > "$dev_map"
fi
printf '# 実配布物:\n'
jq -r '.dependencies | to_entries[] | "  " + .key + " -> " + .value' "$dev_map"

for runtime in codex claude; do
  for directory in $entries; do
    pb="$ROOT/plugins/playbooks/bdd/$directory"
    out="$TMP_ROOT/$runtime-$directory.yml"
    if HARNESS_PLUGIN_RUNTIME="$runtime" HARNESS_PLUGIN_DEV_ROOTS="$dev_map" \
        bash "$pb/scripts/resolve.sh" "$REPO" > "$out" 2> "$out.err" \
      && yq -o=json -I=0 '.' "$out" | jq -e '
        (.deps.grill.dependency_scope=="external") and
        (.deps["write-doc"].dependency_scope=="external") and
        (.deps.grill.source_kind=="dev-map") and
        (.deps["write-doc"].source_kind=="dev-map") and
        ([.deps.grill.implements[] | select(.id=="grill/grill" and .version==1 and .kind=="playbook")] | length==1) and
        ([.deps["write-doc"].implements[] | select(.id=="write-doc/write-doc" and .version==1 and .kind=="playbook")] | length==1)' >/dev/null; then
      pass "$runtime/$directory 実配布物に対する解決"
    else
      fail "$runtime/$directory 実配布物に対する解決（$(head -1 "$out.err")）"
      continue
    fi
    # 入口は .entry の1形だけで指せること。実在するSKILL.mdであり、
    # entry_skill がその frontmatter の name であることを、配布物そのもので確かめる。
    entry_ok=1
    for logical in grill write-doc; do
      entry_path=$(yq -er ".deps[\"$logical\"].entry" "$out" 2>/dev/null) || { entry_ok=0; break; }
      entry_skill=$(yq -er ".deps[\"$logical\"].entry_skill" "$out" 2>/dev/null) || { entry_ok=0; break; }
      dep_root=$(yq -er ".deps[\"$logical\"].root" "$out" 2>/dev/null) || { entry_ok=0; break; }
      [ "$entry_path" = "$dep_root/SKILL.md" ] || { entry_ok=0; break; }
      [ -f "$entry_path" ] && [ ! -L "$entry_path" ] || { entry_ok=0; break; }
      declared=$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1 && /^name: /{sub(/^name: /,""); gsub(/^["'"'"']|["'"'"']$/,""); print; exit}' "$entry_path")
      [ -n "$declared" ] && [ "$declared" = "$entry_skill" ] || { entry_ok=0; break; }
    done
    [ "$entry_ok" -eq 1 ] && pass "$runtime/$directory 入口SKILL.mdは .entry の1形で解決" \
      || fail "$runtime/$directory 入口SKILL.mdの .entry / entry_skill が実配布物と一致しない"
  done
done

# 消費側lintは、依存先の内部名を相手のmanifestから生成する。
# 実配布物が解決できなければ内部名を作れないので、この検査もここへ置く。
for runtime in codex claude; do
  if HARNESS_PLUGIN_DEV_ROOTS="$dev_map" python3 "$ROOT/scripts/lint-consumer-contract.py" \
      --repo "$ROOT" --runtime "$runtime" > "$TMP_ROOT/lint-$runtime.txt" 2>&1; then
    pass "$runtime/消費側lint"
  else
    fail "$runtime/消費側lint"
    sed -n '1,40p' "$TMP_ROOT/lint-$runtime.txt"
    tail -1 "$TMP_ROOT/lint-$runtime.txt"
  fi
done

printf '\nReal distribution: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
