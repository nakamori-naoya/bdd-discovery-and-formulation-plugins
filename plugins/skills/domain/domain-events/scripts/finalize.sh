#!/usr/bin/env bash
# domain-events 固有の検査と、出す形の組み立て。
#
# **resolve.sh から source される。** 設定の解決手順は共通なのでここには無い。
# 使えるもの: merged / required / root / PLUGIN_ROOT / name / selected / source / explain / resolve_path
# やること: 固有schemaの検査と、out への最終JSONの代入。
jq -e '.version==1 and (.event_dir|type=="string" and length>0) and
  (.instructions.exploration.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、event_dir、exploration directiveのいずれかが不正" >&2; exit 2; }
event_dir=$(jq -r '.event_dir' <<<"$merged"); event_dir="${event_dir/#\~/$HOME}"
case "$event_dir" in /*) ;; *) event_dir="${root}/${event_dir}" ;; esac
out=$(jq -cn --arg e "$event_dir" --arg g "$PLUGIN_ROOT/references/grain.md" \
  --arg as "$PLUGIN_ROOT/references/actors-and-stakeholders.md" \
  --arg uc "$PLUGIN_ROOT/references/use-cases.md" --arg de "$PLUGIN_ROOT/references/domain-events.md" \
  --arg es "$PLUGIN_ROOT/references/event-sourcing.md" --arg cm "$PLUGIN_ROOT/references/concept-map.md" \
  --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  '{contract:1, event_dir:$e, grain:$g, actors_stakeholders:$as, use_cases:$uc,
    domain_events:$de, event_sourcing:$es, concept_map:$cm,
    instructions:$instructions, repo_root:$root, plugin_root:$pr}')
