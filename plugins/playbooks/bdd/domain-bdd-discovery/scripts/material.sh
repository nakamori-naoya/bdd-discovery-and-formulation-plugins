#!/usr/bin/env bash
# 洗い出した事実・線引き・決定を、1つの素材へ束ねる。
#
#   material.sh --config <解決済みYAML> --topic <題材> \
#               --events <台帳> --scope <線引き> --decisions <決定ログ> \
#               --behavior-map <振る舞いマップ> --representative-bdd <代表BDD> [--force]
#
# **束ねるだけで、選ばない。** どの素材をどの役へ当てるかは書く工程の判断である。
# ここは「どれか1つでも欠けたまま書き始めていないか」を機械で止める。
set -uo pipefail

cfg=""; topic=""; events=""; scope=""; decisions=""; behavior_map=""; representative_bdd=""; force=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) cfg="${2:-}"; shift 2 ;;
    --topic) topic="${2:-}"; shift 2 ;;
    --events) events="${2:-}"; shift 2 ;;
    --scope) scope="${2:-}"; shift 2 ;;
    --decisions) decisions="${2:-}"; shift 2 ;;
    --behavior-map) behavior_map="${2:-}"; shift 2 ;;
    --representative-bdd) representative_bdd="${2:-}"; shift 2 ;;
    --force) force=1; shift ;;
    *) echo "[error] 未知の引数: $1" >&2; exit 2 ;;
  esac
done

[ -n "$cfg" ] && [ -f "$cfg" ] || { echo "[error] --config に解決済みYAMLが要る" >&2; exit 2; }
command -v yq >/dev/null 2>&1 || { echo "[error] yq が要る" >&2; exit 2; }
case "$topic" in
  "" ) echo "[error] --topic が要る" >&2; exit 2 ;;
  *[!A-Za-z0-9._-]*|*..*) echo "[error] --topic が不正（英数と . _ - のみ）: ${topic}" >&2; exit 2 ;;
esac

# 欠けたまま束ねると、無かったのか聞かなかったのかが後から読めない。
missing=""
for pair in "洗い出し:$events" "線引き:$scope" "決定:$decisions" "振る舞い:$behavior_map" "代表BDD:$representative_bdd"; do
  label="${pair%%:*}"; path="${pair#*:}"
  { [ -n "$path" ] && [ -s "$path" ]; } || missing="${missing} ${label}"
done
if [ -n "$missing" ]; then
  echo "[error] 素材が欠けている:${missing}" >&2
  echo "        欠けたまま書くと、無かったのか確かめていないのかが読めなくなる。" >&2
  exit 2
fi

root=$(yq -er '.repo_root' "$cfg") || exit 2
out_dir=$(yq -er '.playbook.out_dir' "$cfg") || exit 2
case "$out_dir" in /*) ;; *) out_dir="${root}/${out_dir}" ;; esac
roles=$(yq -er '.playbook.contract.material_roles | join(" / ")' "$cfg") || exit 2
confidence=$(yq -er '.playbook.contract.confidence | join(" / ")' "$cfg") || exit 2
directive=$(yq -er '.instructions.material.directive' "$cfg") || exit 2

dest="${out_dir}/${topic}.material.md"
if [ -e "$dest" ] && [ "$force" != "1" ]; then
  echo "[error] すでにある: ${dest}（上書きするなら --force）" >&2
  exit 2
fi
mkdir -p "$out_dir" || { echo "[error] 置き場を作れない: ${out_dir}" >&2; exit 2; }

# 書式の先頭が - で始まると printf の option として食われる。%s で渡す。
section() { printf '%s\n\n%s\n\n' '---' "## $1"; }
{
  printf '# 素材 — %s\n\n%s\n\n' "$topic" "$directive"
  printf '%s\n' "- 役: ${roles}" "- 確からしさ: ${confidence}" ""
  printf '%s\n\n' '**確からしさを落とさない。** 確認できていないものを、確認済みと同じ顔で本文へ入れない。'
  section "洗い出した事実"; cat "$events"
  printf '\n'; section "線引き"; cat "$scope"
  printf '\n'; section "決めたこと・未決"; cat "$decisions"
  printf '\n'; section "コアドメインの振る舞い断面"; cat "$behavior_map"
  printf '\n'; section "代表BDD"; cat "$representative_bdd"
  printf '\n'
} > "$dest" || { echo "[error] 素材を書けない: ${dest}" >&2; exit 2; }

printf '%s\n' "$dest"
