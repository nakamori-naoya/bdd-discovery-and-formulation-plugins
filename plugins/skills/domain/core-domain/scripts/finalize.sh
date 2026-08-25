#!/usr/bin/env bash
# core-domain 固有の検査と、出す形の組み立て。
#
# **resolve.sh から source される。** 設定の解決手順は共通なのでここには無い。
# 使えるもの: merged / required / root / PLUGIN_ROOT / name / selected / source / explain / resolve_path
# やること: 固有schemaの検査と、out への最終JSONの代入。
jq -e '.version==1 and (.scope_dir|type=="string" and length>0) and
  (.instructions.marking.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、scope_dir、marking directiveのいずれかが不正" >&2; exit 2; }
scope_dir=$(jq -r '.scope_dir' <<<"$merged"); scope_dir="${scope_dir/#\~/$HOME}"
case "$scope_dir" in /*) ;; *) scope_dir="${root}/${scope_dir}" ;; esac
out=$(jq -cn --arg s "$scope_dir" --arg b "$PLUGIN_ROOT/references/boundary.md" \
  --arg d "$PLUGIN_ROOT/references/domain.md" --arg sd "$PLUGIN_ROOT/references/subdomains.md" \
  --arg bc "$PLUGIN_ROOT/references/bounded-contexts.md" --arg cm "$PLUGIN_ROOT/references/concept-map.md" \
  --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  '{contract:1, scope_dir:$s, boundary:$b, domain:$d, subdomains:$sd,
    bounded_contexts:$bc, concept_map:$cm, instructions:$instructions, repo_root:$root, plugin_root:$pr}')
