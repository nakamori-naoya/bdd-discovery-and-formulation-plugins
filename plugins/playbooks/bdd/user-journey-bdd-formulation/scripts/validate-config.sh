#!/usr/bin/env bash
set -euo pipefail
file="$1"
jq -e '
  . as $root |
  ($root.steps | to_entries | map(select(.value.skill=="grill"))) as $grill |
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
  (any(.requires[]; .plugin=="write-doc-cleanup" and .marketplace=="write-doc")) and
  ($grill|length)==1 and $grill[0].key==0 and
  ($root.steps | to_entries | map(select(.key > 0)) | all(.[]; ((.value.needs // []) | index("grounded_input") != null))) and
  .steps[-1].skill=="remove-intermediate-artifacts" and .steps[-1].provides==["cleanup_report"] and
  ([.steps[].provides[]?] | index("existing_user_journey_bdd_path") != null and index("journey_map") != null and index("validated_journey_bdd") != null and index("update_target") != null and index("updated_user_journey_bdd_path") != null)
' "$file" >/dev/null || { echo "[error] User Journey BDD Formulationの既存正本・同一パス更新・根拠・境界契約は変更できない" >&2; exit 2; }
