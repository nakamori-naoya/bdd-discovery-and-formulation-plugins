#!/usr/bin/env bash
# BDD package の受入検査を一度に実行する。
# package の配置と manifest は兄弟 checkout ../harness-tools/ の保守 tool が検査し、
# このrepositoryに固有の検査は immutable_model.py の正例・反例・境界例だけである。
# harness-tools が無ければ検査せずに止まる（fixture で代用しない）。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TOOLS="$ROOT/../harness-tools/tools"
[ -d "$TOOLS" ] || { echo "[error] 兄弟 checkout harness-tools が無い: $TOOLS" >&2; exit 2; }
export PYTHONDONTWRITEBYTECODE=1
status=0

printf '\n=== validate-plugin-repository.py ===\n'
python3 "$TOOLS/validate-plugin-repository.py" "$ROOT" || status=1
python3 "$TOOLS/validate-plugin-repository.py" --self-test || status=1
printf '\n=== test-hardening.py ===\n'
python3 "$TOOLS/test-hardening.py" --repository "$ROOT" || status=1

printf '\n=== test-immutable-model.sh ===\n'
bash "$ROOT/scripts/test-immutable-model.sh" || status=1

exit "$status"
