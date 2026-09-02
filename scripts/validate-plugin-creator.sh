#!/usr/bin/env bash
# Scenario: 配布manifestを現在のCodex plugin-creator契約でも検査する
# Given: BDD marketplaceに登録された各pluginの.codex-plugin/plugin.jsonがある
# When: plugin-creatorのvalidatorを各plugin rootへ実行する
# Then: 現行validatorとの互換差分をpluginごとに報告する
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VALIDATOR=${PLUGIN_CREATOR_VALIDATOR:-$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py}

if [ ! -f "$VALIDATOR" ]; then
  echo "FAIL: plugin-creator validatorがこのPCに無い: $VALIDATOR"
  exit 2
fi
if ! python3 -c 'import yaml' >/dev/null 2>&1; then
  echo "FAIL: plugin-creator validatorが必要とするPyYAMLが現在のPython環境に無い"
  echo "      PYTHONPATHを指定できる隔離dependency環境で再実行すること"
  exit 2
fi

passed=0
failed=0
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  if python3 "$VALIDATOR" "$ROOT/$rel"; then
    echo "PASS: $rel"
    passed=$((passed + 1))
  else
    echo "FAIL: $rel"
    failed=$((failed + 1))
  fi
done < <(jq -r '.plugins[].source.path | ltrimstr("./")' "$ROOT/.agents/plugins/marketplace.json")

printf '\nPlugin creator compatibility: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
