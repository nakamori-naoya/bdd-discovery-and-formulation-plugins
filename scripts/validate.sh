#!/usr/bin/env bash
# Scenario: BDD marketplaceの全受入検査を一度に実行する
# Given: BDD責務の10 pluginと完全修飾した外部依存契約がある
# When: 構造、runtime、Codex manifest互換を順に検査する
# Then: 一つでも不具合があれば最終終了codeを非0にする
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
status=0

for script in validate-distribution.py validate-structure.sh validate-runtime.sh; do
  printf '\n=== %s ===\n' "$script"
  if [[ "$script" == *.py ]]; then
    if ! python3 "$ROOT/scripts/$script" "$ROOT"; then status=1; fi
  elif ! bash "$ROOT/scripts/$script"; then
    status=1
  fi
done

python3 "$ROOT/scripts/validate-distribution.py" --self-test "$ROOT" || status=1

exit "$status"
