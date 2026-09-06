#!/usr/bin/env bash
set -euo pipefail
file="$1"
jq -e '
  . as $root |
  ($root.steps | to_entries | map(select(.value.playbook=="grill"))) as $grill |
  ($root.steps | to_entries | map(select(.value.script=="scripts/ground.py"))) as $ground |
  .focus=="user-journey" and .document_type=="user-journey-bdd" and .output_format=="markdown" and
  .requirements.input_grounded==true and .requirements.clarify_with_grill==true and
  .requirements.one_user_purpose_per_document==true and .requirements.multiple_meaningful_scenes==true and
  .requirements.observable_completion==true and .requirements.exclude_test_execution==true and
  .requirements.existing_document_required==true and .requirements.update_in_place==true and
  .requirements.create_new_document==false and
  .contract.grounding_sources==["user_input","referenced_artifacts","grill_decisions"] and
  .contract.journey_frame==["user","purpose","starting_point","final_point","completion_condition"] and
  .contract.journey_boundary==["central_question","inclusion_reason","excluded_questions"] and
  .contract.journey_scene==["sequence","prior_state","acting_role","action","observable_response","next_state","handoff"] and
  (any(.requires[]; .plugin=="user-journey" and .marketplace=="bdd-discovery-and-formulation")) and
  ([.requires[] | select(.marketplace=="write-doc")] == [{"plugin":"write-doc","marketplace":"write-doc"}]) and
  (all($root.steps[]; .skill!="grill")) and
  ($grill|length)==1 and $grill[0].key==0 and
  ($grill[0].value.provides == ["decisions","open_questions"]) and
  ($ground|length)==1 and $ground[0].key==1 and
  ($ground[0].value.needs == ["decisions","open_questions"]) and
  ($ground[0].value.provides | index("grounded_input") != null) and
  ($root.steps | to_entries | map(select(.key > $ground[0].key)) | all(.[]; ((.value.needs // []) | index("grounded_input") != null))) and
  ([.steps[] | select(.playbook=="write-doc")] | length==1 and all(.[]; (.input.document_type|type=="string" and length>0))) and
  (.steps[-1].id=="cleanup" and .steps[-1].script=="scripts/cleanup.py" and .steps[-1].provides==["cleanup_report"]) and
  ((.contract.cleanup.delete_after_document + .contract.cleanup.preserve) - .steps[-1].needs | length==0) and
  ([.steps[].provides[]?] | index("existing_user_journey_bdd_path") != null and index("journey_map") != null and index("validated_journey_bdd") != null and index("update_target") != null and index("updated_user_journey_bdd_path") != null)
' "$file" >/dev/null || { echo "[error] User Journey BDD Formulationの既存正本・同一パス更新・根拠・境界契約は変更できない" >&2; exit 2; }
