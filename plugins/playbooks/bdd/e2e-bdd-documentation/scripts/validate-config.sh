#!/usr/bin/env bash
set -euo pipefail
file="$1"

jq -e '
  . as $root |
  (any(.requires[]; .plugin=="intermediate-cleanup")) and
  (.contract.cleanup.delete_after_document | type=="array" and length>0) and
  (.contract.cleanup.preserve | type=="array" and length>0) and
  ((.contract.cleanup.delete_after_document + .contract.cleanup.preserve) - .steps[-1].needs | length==0) and
  (.steps[-1].id=="cleanup" and .steps[-1].skill=="remove-intermediate-artifacts" and .steps[-1].provides==["cleanup_report"]) and
  ([.steps | to_entries[] | select(.value.playbook=="write-doc") | .key] | length>0 and max < (($root.steps|length)-1))
' "$file" >/dev/null || { echo "[error] write-doc後の中間生成物の後片付け契約は外せない" >&2; exit 2; }

jq -e '
  . as $root |
  ($root.steps | to_entries | map(select(.value.skill=="grill"))) as $grill |
  $root.requirements.input_grounded==true and
  $root.requirements.clarify_with_grill==true and
  $root.contract.grounding_sources==["user_input","referenced_artifacts","grill_decisions"] and
  (any($root.requires[]; .plugin=="grill")) and
  ($grill|length)==1 and $grill[0].key==0 and
  ($grill[0].value.provides | index("grounded_input") != null) and
  ($root.steps | to_entries | map(select(.key > $grill[0].key)) | all(.[]; ((.value.needs // []) | index("grounded_input") != null)))
' "$file" >/dev/null || {
  echo "[error] E2E BDD工程は入力根拠を固定し、grillのgrounded_inputを全後続工程へ渡すこと" >&2
  exit 2
}

jq -e '
  .focus=="e2e-story" and
  .document_type=="e2e-bdd-scenarios" and
  .output_format=="markdown" and
  (.out_dir|type=="string" and length>0) and
  .requirements.one_user_purpose_per_document==true and
  .requirements.interactive_story==true and
  .requirements.allow_multiple_interactions==true and
  .requirements.exclude_test_execution==true and
  .contract.story_frame==["user","purpose","starting_point","final_point","completion_condition"] and
  .contract.interaction_scene==["sequence","prior_state","acting_role","action","observable_response","next_state"] and
  .contract.excluded_concerns==["domain_rule_discovery","data_model_design","interface_operation_details","test_execution"] and
  ([.steps[].provides[]?] | index("story_draft") != null and index("validated_story") != null and index("e2e_document_path") != null)
' "$file" >/dev/null || {
  echo "[error] E2Eストーリーの目的・両端・複数場面・責務境界・必須成果は変更できない" >&2
  exit 2
}
