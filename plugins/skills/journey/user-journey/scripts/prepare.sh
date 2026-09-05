#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ "${1:-}" != "--root-only" ] || [ "$#" -ne 1 ]; then
  echo "usage: prepare.sh --root-only" >&2
  exit 2
fi
[ -f "$PLUGIN_ROOT/SKILL.md" ] || { echo "[error] root SKILL.mdが無い" >&2; exit 2; }
[ -x "$PLUGIN_ROOT/scripts/journey.py" ] || { echo "[error] journey validatorが無い" >&2; exit 2; }
printf '%s\n' "$PLUGIN_ROOT"
