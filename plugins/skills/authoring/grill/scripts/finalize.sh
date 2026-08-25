#!/usr/bin/env bash
# grill 固有の検査と、出す形の組み立て。
#
# **resolve.sh から source される。** 設定の解決手順は共通なのでここには無い。
# 使えるもの: merged / required / root / PLUGIN_ROOT / name / selected / source / explain / resolve_path
# やること: 固有schemaの検査と、out への最終JSONの代入。
jq -e '.version==1 and (.aspects|type=="string") and (.log_dir|type=="string" and length>0) and
  (.instructions.questioning.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、log_dir、questioning directiveのいずれかが不正" >&2; exit 2; }

want=$(jq -r '.aspects // ""' <<<"$merged")
# 同梱の観点は名前で選べる（例: business-rules）。/ も . も含まない語だけを名前として扱う。
bundled_aspect=""
case "$want" in
  ""|*/*|*.*) ;;
  *) [ ! -f "$PLUGIN_ROOT/references/aspects/${want}.md" ] || bundled_aspect="$PLUGIN_ROOT/references/aspects/${want}.md" ;;
esac
if [ -n "$bundled_aspect" ]; then
  aspects="$bundled_aspect"; src="$want"
else
  aspects=$(resolve_path "$want")
  if [ -n "$aspects" ] && [ -f "$aspects" ]; then
    src=repo
  else
    # 指したのに無いのを既定へ倒すと、差し替えたつもりで効いていない。
    [ -z "$aspects" ] || { echo "[error] aspects に指定したファイルが無い: ${aspects}（同梱の観点を使うなら $(cd "$PLUGIN_ROOT/references/aspects" && ls ./*.md | sed 's|^\./||; s|\.md$||' | tr '\n' ' ')）" >&2; exit 2; }
    aspects="$PLUGIN_ROOT/references/aspects/default.md"; src=default
  fi
fi

log_dir=$(resolve_path "$(jq -r '.log_dir // "decisions"' <<<"$merged")")

out=$(jq -cn --arg a "$aspects" --arg s "$src" --arg q "$PLUGIN_ROOT/references/questioning.md" \
  --arg l "$log_dir" --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  '{contract:1, aspects:{path:$a, source:$s}, questioning:$q, log_dir:$l,
    instructions:$instructions,
    repo_root:$root, plugin_root:$pr}')

if [ "$explain" = "1" ]; then
  echo "# 詰める観点: ${src} (${aspects})" >&2
  echo "# 決定ログ: ${log_dir}" >&2
fi
