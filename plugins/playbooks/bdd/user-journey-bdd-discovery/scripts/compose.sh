#!/usr/bin/env bash
# 書き上げた本文・BDD草案・条件マトリクスが揃っていることを機械で確かめ、1つの素材へ束ねる。
#
#   compose.sh --config <解決済みYAML> --topic <題材slug> \
#              --scenarios <BDD草案> --matrix <条件マトリクス> \
#              --output-path <保存先の絶対path> [--body <改訂本文>] [--new] [--force]
#
# **束ねるだけで、書かない。** 文章の規律はこの配布物の references が持つ。
# ここは「どれか1つでも欠けたまま保存工程へ渡していないか」を止める。
#
# 標準出力へJSONを1行返す。exit 0 = 束ねた / 2 = 束ねられない。
set -uo pipefail

cfg=""; topic=""; scenarios=""; matrix=""; body=""; output_path=""; want_new=0; force=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) cfg="${2:-}"; shift 2 ;;
    --topic) topic="${2:-}"; shift 2 ;;
    --scenarios) scenarios="${2:-}"; shift 2 ;;
    --matrix) matrix="${2:-}"; shift 2 ;;
    --body) body="${2:-}"; shift 2 ;;
    --output-path) output_path="${2:-}"; shift 2 ;;
    --new) want_new=1; shift ;;
    --force) force=1; shift ;;
    *) echo "[error] 未知の引数: $1" >&2; exit 2 ;;
  esac
done

command -v yq >/dev/null 2>&1 || { echo "[error] yq が要る" >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "[error] jq が要る" >&2; exit 2; }
[ -n "$cfg" ] && [ -f "$cfg" ] || { echo "[error] --config に解決済みYAMLが要る" >&2; exit 2; }
case "$topic" in
  "" ) echo "[error] --topic が要る" >&2; exit 2 ;;
  *[!A-Za-z0-9._-]*|*..*) echo "[error] --topic が不正（英数と . _ - のみ）: ${topic}" >&2; exit 2 ;;
esac
case "$output_path" in
  /*) ;;
  *) echo "[error] --output-path は絶対pathで渡す: ${output_path}" >&2; exit 2 ;;
esac

repo_root=$(yq -er '.repo_root' "$cfg") || exit 2
case "$output_path" in
  "$repo_root"/*) ;;
  *) echo "[error] --output-path がrepositoryの外を指している: ${output_path}" >&2; exit 2 ;;
esac
if [ "$want_new" = "1" ] && [ -e "$output_path" ]; then
  echo "[error] 新規に作る段取りだが、保存先がすでにある: ${output_path}" >&2
  echo "        既存資料を上書きしない。深化させるなら formulation の段取りを使う。" >&2
  exit 2
fi

missing=""
for pair in "BDD草案:$scenarios" "条件マトリクス:$matrix"; do
  label="${pair%%:*}"; path="${pair#*:}"
  { [ -n "$path" ] && [ -f "$path" ] && [ ! -L "$path" ] && [ -s "$path" ]; } || missing="${missing} ${label}"
done
if [ -n "$body" ]; then
  { [ -f "$body" ] && [ ! -L "$body" ] && [ -s "$body" ]; } || missing="${missing} 本文"
fi
if [ -n "$missing" ]; then
  echo "[error] 素材が欠けている:${missing}" >&2
  echo "        欠けたまま保存すると、無かったのか確かめていないのかが読めなくなる。" >&2
  exit 2
fi

out_dir=$(dirname "$output_path")
mkdir -p "$out_dir" || { echo "[error] 置き場を作れない: ${out_dir}" >&2; exit 2; }
material="${out_dir}/${topic}.material.md"
if [ -e "$material" ] && [ "$force" != "1" ]; then
  echo "[error] すでにある: ${material}（上書きするなら --force）" >&2
  exit 2
fi

section() { printf '%s\n\n%s\n\n' '---' "## $1"; }
{
  printf '# 素材 — %s\n\n' "$topic"
  printf '%s\n\n' '**確からしさを落とさない。** 確認できていないものを、確認済みと同じ顔で本文へ入れない。'
  if [ -n "$body" ]; then
    section "本文"; cat "$body"; printf '\n'
  fi
  section "BDD草案"; cat "$scenarios"; printf '\n'
  section "条件マトリクス"
  printf '```json\n'; cat "$matrix"; printf '\n```\n'
} > "$material" || { echo "[error] 素材を書けない: ${material}" >&2; exit 2; }

scenarios_abs=$(cd "$(dirname "$scenarios")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$scenarios")")
matrix_abs=$(cd "$(dirname "$matrix")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$matrix")")

jq -n --arg material "$material" --arg scenarios "$scenarios_abs" --arg matrix "$matrix_abs" \
  --arg output "$output_path" \
  '{material:$material, scenario_draft:$scenarios, condition_matrix:$matrix,
    requested_output_path:$output}'
