#!/usr/bin/env bash
# Scenario: BDD packageの全受入検査を一度に実行する
# Given: 7公開入口と5内部skillを持つ1 packageと、grill / write-docへの外部依存宣言と、兄弟checkout ../harness-tools/ の保守toolがある
# When: 構造、root契約、保守toolの回帰検査、消費側lintを順に検査する
# Then: 一つでも不具合があれば最終終了codeを非0にする。harness-tools または依存先の実配布物が無ければ検査せずに止まる（fixtureで代用しない）
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TOOLS="$ROOT/../harness-tools/tools"
[ -d "$TOOLS" ] || { echo "[error] 兄弟 checkout harness-tools が無い: $TOOLS" >&2; exit 2; }

# 継承した解決環境を捨てる。呼び出し元のdev-mapやtest-cacheが残っていると、
# 負の試験が「別のところから解決できてしまう」形で黙って破れる。
unset HARNESS_PLUGIN_DEV_ROOTS HARNESS_PLUGIN_CACHE_ROOT
export -n HARNESS_PLUGIN_DEV_ROOTS HARNESS_PLUGIN_CACHE_ROOT 2>/dev/null || true
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-validate.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
status=0

printf '\n=== validate-structure.sh ===\n'
bash "$ROOT/scripts/validate-structure.sh" || status=1

# 共有保守tool（正本は ../harness-tools/tools。複製を持たない）
printf '\n=== validate-plugin-repository.py ===\n'
python3 "$TOOLS/validate-plugin-repository.py" "$ROOT" || status=1
python3 "$TOOLS/validate-plugin-repository.py" --self-test || status=1
printf '\n=== test-hardening.py ===\n'
python3 "$TOOLS/test-hardening.py" --repository "$ROOT" || status=1

# 消費側lint: 依存先の実配布物（兄弟checkout）から検出語を作る。fixtureだけで緑にしない。
printf '\n=== lint-consumer-contract.py ===\n'
grill_root="$ROOT/../grill-plugins/plugins/grill"
write_doc_root="$ROOT/../write-doc-plugins/plugins/write-doc"
if [ -d "$grill_root" ] && [ -d "$write_doc_root" ]; then
  dev_map="$TMP_ROOT/real-roots.json"
  jq -n --arg grill "$(cd "$grill_root" && pwd -P)" --arg doc "$(cd "$write_doc_root" && pwd -P)" \
    '{schema:1,dependencies:{"grill/grill":$grill,"write-doc/write-doc":$doc}}' > "$dev_map"
  for runtime in codex claude; do
    HARNESS_PLUGIN_DEV_ROOTS="$dev_map" python3 "$TOOLS/lint-consumer-contract.py" \
      --repo "$ROOT" --runtime "$runtime" || status=1
  done
else
  printf 'FAIL: 依存先の実配布物（../grill-plugins/plugins/grill, ../write-doc-plugins/plugins/write-doc）が無い\n'
  status=1
fi

exit "$status"
