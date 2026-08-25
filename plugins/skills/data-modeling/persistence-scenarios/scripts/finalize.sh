#!/usr/bin/env bash
# persistence-scenarios 固有の検査と、解決結果の組み立て。
jq -e '.version==1 and (.scenario_dir|type=="string" and length>0) and
  (.instructions.discovery.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、scenario_dir、discovery directiveのいずれかが不正" >&2; exit 2; }
scenario_dir=$(jq -r '.scenario_dir' <<<"$merged"); scenario_dir="${scenario_dir/#\~/$HOME}"
case "$scenario_dir" in /*) ;; *) scenario_dir="${root}/${scenario_dir}" ;; esac
out=$(jq -cn --arg d "$scenario_dir" \
  --arg as "$PLUGIN_ROOT/references/actors-and-stakeholders.md" \
  --arg uc "$PLUGIN_ROOT/references/use-cases.md" \
  --arg de "$PLUGIN_ROOT/references/domain-events.md" \
  --arg ul "$PLUGIN_ROOT/references/ubiquitous-language.md" \
  --arg im "$PLUGIN_ROOT/references/immutable-data-modeling.md" \
  --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  --arg cfgsrc "$source" --argjson psrc "$sources" \
  '{contract:1, scenario_dir:$d, actors_stakeholders:$as, use_cases:$uc,
    domain_events:$de, ubiquitous_language:$ul, immutable_data_modeling:$im,
    instructions:$instructions, repo_root:$root, plugin_root:$pr,
    resolution:{config_source:$cfgsrc}, _sources:$psrc}')
