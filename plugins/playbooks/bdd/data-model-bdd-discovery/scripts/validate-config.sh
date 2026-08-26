#!/usr/bin/env bash
set -euo pipefail
file="$1"
jq -e '
  . as $root |
  (.requires | index("intermediate-cleanup") != null) and
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
  ($root.requires | index("grill") != null) and
  ($grill|length)==1 and
  $grill[0].key==0 and
  ($grill[0].value.provides | index("grounded_input") != null) and
  ($root.steps | to_entries | map(select(.key > $grill[0].key)) | all(.[]; ((.value.needs // []) | index("grounded_input") != null)))
' "$file" >/dev/null || {
  echo "[error] BDD工程は入力根拠を固定し、grillで確認したgrounded_inputを全後続工程へ渡すこと" >&2
  exit 2
}
jq -e '
  .focus=="data-model" and
  .document_type=="rdb-logical-data-modeling" and
  .output_format=="markdown" and
  (.modeling.method|type=="string" and length>0) and
  (.out_dir|type=="string" and length>0) and
  (.contract.persistence_operations==["create","update","delete"]) and
  (.contract.scenario_roles|type=="array" and length==10 and length==(unique|length)) and
  ([.steps[].provides[]?] | index("persistence_scenarios") != null and index("logical_data_model") != null and index("logical_document_path") != null)
' "$file" >/dev/null || {
  echo "[error] data-model焦点・RDB論理設計の資料型・Markdown出力・modeling.method・CUD契約・必須成果は変更できない" >&2
  exit 2
}
