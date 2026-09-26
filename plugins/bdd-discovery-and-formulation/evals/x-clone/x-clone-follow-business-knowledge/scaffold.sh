#!/usr/bin/env bash
# X のクローンの共通の準備を使う。
set -euo pipefail
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scaffold.sh"
