#!/usr/bin/env bash
# Scenario: prototypeの全受入検査を一度に実行する
# Given: 最新commitから15 pluginと必要sharedだけをコピーしている
# When: 構造、runtime、Codex manifest互換を順に検査する
# Then: 一つでも不具合があれば最終終了codeを非0にする
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
status=0

for script in validate-structure.sh validate-runtime.sh; do
  printf '\n=== %s ===\n' "$script"
  if ! bash "$ROOT/scripts/$script"; then status=1; fi
done

exit "$status"
