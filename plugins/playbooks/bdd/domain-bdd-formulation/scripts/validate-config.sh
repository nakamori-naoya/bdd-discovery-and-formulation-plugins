#!/usr/bin/env bash
set -euo pipefail
file="$1"
# Deterministic validation declaration:
# source=the public playbook JSON; input=the sole write-doc update step;
# normalization=none; predicate=the delivery mapping names the existing domain
# rule and the step has exactly update_target, never create-mode destinations;
# diagnostic=the single structural-contract error below; positive=current
# playbook; negative=missing update_target, wrong mapping, or mixed needs;
# boundary=document meaning remains invoking-agent review.
jq -e '
  .inputs==["user_input","referenced_artifacts","existing_domain_rule_path"] and
  .agent_work.owner=="invoking_agent" and
  .agent_work.delivery.provider=="write-doc" and .agent_work.delivery.input_mapping=={"material_kind":"text","material_content":"final_markdown"} and .agent_work.delivery.output_path_from=="existing_domain_rule_path" and
  .agent_work.temporary_files.location=="system_temporary_directory" and .agent_work.temporary_files.delete_only_after=="document_saved" and
  [.steps[].id]==["challenge","ground","revise","validate","guard-update","document"] and
  [.steps[] | (.agent_work // .script // .playbook)]==["grill","invoking_agent","invoking_agent","scripts/scenario.py","scripts/update-guard.py","write-doc"] and
  all(.steps[] | select(has("agent_work")); .agent_work=="invoking_agent") and
  ([.steps[] | select(has("skill") or has("plugin"))]|length)==0 and
  ([.steps[] | select(has("playbook")) | .playbook]==["grill","write-doc"]) and
  .steps[-1].needs==["final_markdown","validation_report","update_target"] and .steps[-1].input=={"document_type":"${.document_type}"} and .steps[-1].provides==["updated_domain_rule_path"]
' "$file" >/dev/null || { echo "[error] domain-bdd-formulationはYAML宣言順、同一agentの認知工程、決定論的検査、text資料化の構造契約を満たすこと" >&2; exit 2; }
