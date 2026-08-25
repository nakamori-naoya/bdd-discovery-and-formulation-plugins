#!/usr/bin/env bash
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
  .focus=="domain" and
  .output_format=="markdown" and
  (.max_steps|type=="number" and .>=3 and .<=12) and
  (.allow_background|type=="boolean") and
  (.examples_limits.rows|type=="number" and .>=1) and
  (.examples_limits.columns|type=="number" and .>=1) and
  (.contract.probe_dimensions == ["同値分割","境界値","精度と単位","条件組合せ","状態遷移","イベント順序","重複と再実行","同時実行","アクターと権限","悪用と不正","時間","規則変更と遡及","失敗時保証","不変条件"]) and
  (.requirements.core_domain_only==true) and
  (.requirements.existing_document_required==true) and
  (.requirements.update_in_place==true) and
  (.requirements.create_new_document==false) and
  ([.steps[].provides[]?] | index("existing_domain_rule_path") != null and index("probe_findings") != null and index("validated_scenarios") != null and index("update_target") != null and index("updated_domain_rule_path") != null)
' "$file" >/dev/null || {
  echo "[error] domain formulationはMarkdown出力・コア限定・既存資料の同一パス更新・QA反証・必須成果を変更できない" >&2
  exit 2
}
jq -e '.document_type=="domain-rule"' "$file" >/dev/null \
  || { echo "[error] domainの資料型はdomain-ruleに固定する" >&2; exit 2; }
