#!/usr/bin/env bash
# User Journey BDD Discoveryの変更不能な契約を検査する。
set -euo pipefail
file="$1"

jq -e '
  . as $root |
  (any(.requires[]; .plugin=="write-doc-cleanup" and .marketplace=="write-doc")) and
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
  echo "[error] User Journey BDD工程は入力根拠を固定し、grillのgrounded_inputを全後続工程へ渡すこと" >&2
  exit 2
}

jq -e '
  .focus=="user-journey" and
  .document_type=="user-journey-bdd" and
  .output_format=="markdown" and
  (.out_dir|type=="string" and length>0) and
  .requirements.one_user_purpose_per_document==true and
  .requirements.multiple_meaningful_scenes==true and
  .requirements.observable_completion==true and
  .requirements.allow_multiple_interactions==true and
  .requirements.exclude_test_execution==true and
  .requirements.create_first_canonical_document==true and
  .requirements.existing_document_must_not_be_overwritten==true and
  .contract.journey_frame==["user","purpose","starting_point","final_point","completion_condition"] and
  .contract.journey_boundary==["central_question","inclusion_reason","excluded_questions"] and
  .contract.journey_scene==["sequence","prior_state","acting_role","action","observable_response","next_state","handoff"] and
  .contract.excluded_concerns==["use_case_responsibility","ux_experience_map","domain_rule_discovery","data_model_design","interface_operation_details","test_execution"] and
  (any(.requires[]; .plugin=="user-journey" and .marketplace=="bdd-discovery-and-formulation")) and
  ([.steps[].provides[]?] | index("journey_map") != null and index("scenario_draft") != null and index("validated_journey_bdd") != null and index("user_journey_bdd_path") != null)
' "$file" >/dev/null || {
  echo "[error] Journeyの目的・両端・複数場面・責務境界・初回正本の契約は変更できない" >&2
  exit 2
}
