#!/usr/bin/env bash
# data-model-bdd-formulation 固有の設定と工程契約を検査する。
set -euo pipefail
file="$1"
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
  (.output_format=="markdown") and
  (.contract.persistence_operations==["create","update","delete"]) and
  (.contract.probe_dimensions == ["同値分割","境界値","精度と単位","条件組合せ","状態遷移","イベント順序","重複と再実行","同時実行","アクターと権限","悪用と不正","時間","規則変更と遡及","失敗時保証","不変条件"]) and
  (.contract.logical_schema_markers==["table","column","business_constraint"]) and
  (.contract.confidence|type=="array" and length>0 and all(.[]; type=="string" and length>0)) and
  (.requirements.existing_logical_document_required==true) and
  (.requirements.update_logical_in_place==true) and
  (.requirements.create_new_logical_document==false) and
  (.requirements.bdd_scenarios_in_logical_only==true) and
  (.requirements.logical_schema_immutable_in_physical==true) and
  (.requirements.read_scenarios_in_physical_only==true) and
  (.requirements.rdb_only==true) and (.requirements.verified_features_only==true) and
  (.database.product|type=="string" and length>0) and
  (.database.version|type=="string" and length>0) and
  (.modeling.method|type=="string" and length>0) and
  (.out_dir|type=="string" and length>0)
' "$file" >/dev/null || {
  echo "[error] Markdown出力、既存論理資料の深化、必須要件、database、modeling.method、out_dirのいずれかが不正" >&2
  exit 2
}

jq -e '
  def providers($name): [.steps | to_entries[] | select(.value.provides | index($name)!=null) | .key];
  def consumers($name): [.steps | to_entries[] | select((.value.needs // []) | index($name)!=null) | .key];
  (providers("existing_logical_document_path")|length)==1 and
  (providers("probe_findings")|length)==1 and
  (providers("revised_persistence_scenarios")|length)==1 and
  (providers("persistence_coverage")|length)==1 and
  (providers("revised_logical_data_model")|length)==1 and
  (providers("logical_update_target")|length)==1 and
  (providers("updated_logical_document_path")|length)==1 and
  (providers("read_scenarios")|length)==1 and
  (providers("physical_rdb_design")|length)==1 and
  (providers("isolation_level_decisions")|length)==1 and
  (providers("feature_evidence")|length)==1 and
  (providers("existing_logical_document_path")[0] < providers("revised_logical_data_model")[0]) and
  (providers("revised_logical_data_model")[0] < providers("updated_logical_document_path")[0]) and
  (providers("updated_logical_document_path")[0] < providers("physical_rdb_design")[0]) and
  (consumers("logical_update_target")|length)==1 and
  (consumers("updated_logical_document_path")|length)==1
' "$file" >/dev/null || {
  echo "[error] 既存論理資料の反証 → 同一パス更新 → Readを含む物理設計という入出力契約が不正" >&2
  exit 2
}
