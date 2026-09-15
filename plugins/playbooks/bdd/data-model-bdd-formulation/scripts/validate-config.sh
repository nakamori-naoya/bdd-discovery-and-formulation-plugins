#!/usr/bin/env bash
set -euo pipefail
file="$1"
# Deterministic validation declaration:
# source=the public playbook JSON; input=the logical-update and physical-create
# write-doc steps; normalization=none; predicate=each call has exactly one
# destination mode and delivery points at the declared existing logical path;
# diagnostic=the single structural-contract error below; positive=current
# playbook; negative=missing update_target, wrong output_path_from, or mixed
# create/update needs; boundary=document meaning remains invoking-agent review.
jq -e '
  .inputs==["user_input","referenced_artifacts","existing_logical_document_path","physical_output_directory","physical_name"] and
  (has("out_dir")|not) and
  .agent_work.owner=="invoking_agent" and
  .agent_work.delivery.provider=="write-doc" and .agent_work.delivery.input_mapping=={"material_kind":"text","material_content":"final_markdown"} and .agent_work.delivery.output_path_from=="existing_logical_document_path" and
  .agent_work.temporary_files.location=="system_temporary_directory" and .agent_work.temporary_files.delete_only_after=="document_saved" and
  [.steps[].id]==["challenge-persistence","ground","deepen-scenarios","validate-scenarios","revise-logical-model","guard-logical-update","update-logical-document","design-physical","document-physical"] and
  [.steps[] | (.agent_work // .script // .playbook)]==["grill","invoking_agent","invoking_agent","scripts/scenario_matrix.py","invoking_agent","scripts/update-guard.py","write-doc","invoking_agent","write-doc"] and
  all(.steps[] | select(has("agent_work")); .agent_work=="invoking_agent") and
  ([.steps[] | select(has("skill") or has("plugin"))]|length)==0 and
  ([.steps[] | select(has("playbook")) | .playbook]==["grill","write-doc","write-doc"]) and
  .steps[6].needs==["final_markdown","validation_report","update_target"] and .steps[6].input=={"document_type":"rdb-logical-data-modeling"} and .steps[6].provides==["updated_logical_document_path"] and
  (.steps[7].needs|index("updated_logical_document_path")!=null) and (.steps[7].needs|index("physical_output_directory")!=null) and (.steps[7].needs|index("physical_name")!=null) and
  .steps[-1].needs==["updated_logical_document_path","physical_output_directory","physical_name","physical_rdb_design","physical_final_markdown","isolation_level_decisions","feature_evidence"] and .steps[-1].input=={"document_type":"rdb-physical-design"} and .steps[-1].provides==["physical_rdb_design_path"]
' "$file" >/dev/null || { echo "[error] data-model-bdd-formulationはYAML宣言順、同一agentの認知工程、決定論的検査、text資料化の構造契約を満たすこと" >&2; exit 2; }
