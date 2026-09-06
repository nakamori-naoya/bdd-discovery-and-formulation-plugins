#!/usr/bin/env bash
# Scenario: BDD marketplaceの全受入検査を一度に実行する
# Given: BDD責務の12 pluginと完全修飾した外部依存契約がある
# When: 構造、runtime、Codex manifest互換を順に検査する
# Then: 一つでも不具合があれば最終終了codeを非0にする
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# 継承した解決環境を捨てる。呼び出し元のdev-mapやtest-cacheが残っていると、
# 負の試験が「別のところから解決できてしまう」形で黙って破れる。
# 必要な検査は自分で設定して実行する。
unset HARNESS_PLUGIN_DEV_ROOTS HARNESS_PLUGIN_CACHE_ROOT
export -n HARNESS_PLUGIN_DEV_ROOTS HARNESS_PLUGIN_CACHE_ROOT 2>/dev/null || true

python3 "$ROOT/scripts/test-hardening.py" || exit 1
status=0

# runtimeの複製が正本と一致していること。意図しない差分をここで止める。
printf '\n=== sync-runtime.py --check ===\n'
if [ -d "$ROOT/../product-planning-plugins/shared/runtime-source" ]; then
  python3 "$ROOT/scripts/sync-runtime.py" --repo "$ROOT" \
    --source "$ROOT/../product-planning-plugins/shared/runtime-source" --check || status=1
else
  printf 'FAIL: runtime正本 (../product-planning-plugins/shared/runtime-source) が無い\n'
  status=1
fi

for script in validate-distribution.py validate-structure.sh validate-runtime.sh validate-real-distribution.sh; do
  printf '\n=== %s ===\n' "$script"
  if [[ "$script" == *.py ]]; then
    if ! python3 "$ROOT/scripts/$script" "$ROOT"; then status=1; fi
  elif ! bash "$ROOT/scripts/$script"; then
    status=1
  fi
done

python3 "$ROOT/scripts/validate-distribution.py" --self-test "$ROOT" || status=1

exit "$status"
