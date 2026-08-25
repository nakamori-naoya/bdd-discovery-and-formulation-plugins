#!/usr/bin/env bash
# rdb-design 固有の検査と、解決結果の組み立て。
jq -e '.version==1 and (.design_dir|type=="string" and length>0) and
  (.database.product|type=="string" and length>0) and (.database.version|type=="string" and length>0) and
  (.instructions.design.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、design_dir、database.product、database.version、design directiveのいずれかが不正" >&2; exit 2; }
design_dir=$(jq -r '.design_dir' <<<"$merged"); design_dir="${design_dir/#\~/$HOME}"
case "$design_dir" in /*) ;; *) design_dir="${root}/${design_dir}" ;; esac
out=$(jq -cn --arg d "$design_dir" --arg product "$(jq -r '.database.product' <<<"$merged")" \
  --arg version "$(jq -r '.database.version' <<<"$merged")" \
  --arg rd "$PLUGIN_ROOT/references/relational-data-modeling-principles.md" \
  --arg na "$PLUGIN_ROOT/references/null-avoidance.md" \
  --arg rl "$PLUGIN_ROOT/references/relational-data-lifecycle.md" \
  --arg ti "$PLUGIN_ROOT/references/transaction-isolation.md" \
  --arg dc "$PLUGIN_ROOT/references/design-contract.md" \
  --arg pt "$PLUGIN_ROOT/assets/physical-design.md" \
  --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  --arg cfgsrc "$source" --argjson psrc "$sources" \
  '{contract:1, design_dir:$d, database:{product:$product,version:$version},
    relational_data_modeling:$rd, null_avoidance:$na, relational_data_lifecycle:$rl,
    transaction_isolation:$ti,
    design_contract:$dc, physical_rdb_template:$pt,
    instructions:$instructions, repo_root:$root, plugin_root:$pr,
    resolution:{config_source:$cfgsrc}, _sources:$psrc}')
