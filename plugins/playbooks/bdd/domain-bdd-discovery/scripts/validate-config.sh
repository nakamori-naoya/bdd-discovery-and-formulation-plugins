#!/usr/bin/env bash
# domain-bdd-discovery 固有の設定検査。共通のschema検査は resolve.sh が済ませている。
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
  ($grill|length)==1 and
  $grill[0].key==0 and
  ($grill[0].value.provides | index("grounded_input") != null) and
  ($root.steps | to_entries | map(select(.key > $grill[0].key)) | all(.[]; ((.value.needs // []) | index("grounded_input") != null)))
' "$file" >/dev/null || {
  echo "[error] BDD工程は入力根拠を固定し、grillで確認したgrounded_inputを全後続工程へ渡すこと" >&2
  exit 2
}
jq -e '(.contract|type=="object") and
  (.focus=="domain") and
  (.document_type=="domain-rule") and
  (.output_format=="markdown") and
  (.map_dir|type=="string" and length>0) and
  (.contract.material_roles|type=="array" and length>0 and all(.[]; type=="string" and length>0) and (length==(unique|length))) and
  (.contract.confidence|type=="array" and length>0 and all(.[]; type=="string" and length>0)) and
  (.contract.behavior_slice|type=="array" and length==12 and length==(unique|length)) and
  ([.steps[].provides[]?] | index("behavior_map") != null and index("representative_bdd") != null and index("domain_rule_path") != null) and
  (.out_dir|type=="string" and length>0)' "$file" >/dev/null \
  || { echo "[error] domain-rule、Markdown出力、振る舞い断面契約、必須成果、out_dirのいずれかが不正" >&2; exit 2; }
# 業務の正本は、作りを全部やめても残る範囲だけを持つ。
# 実装の関心を落とす工程を、要件を立てたまま外せないようにする。
if jq -e '.requirements | has("exclude_implementation")' "$file" >/dev/null; then
  jq -e '.requirements.exclude_implementation | type == "boolean"' "$file" >/dev/null \
    || { echo "[error] requirements.exclude_implementation は true / false で指定すること" >&2; exit 2; }
  if jq -e '.requirements.exclude_implementation == true' "$file" >/dev/null; then
    jq -e '[.steps[] | .provides[]?] | index("implementation_excluded") != null' "$file" >/dev/null \
      || { echo "[error] requirements.exclude_implementation が true だが、implementation_excluded を provides する工程が無い" >&2; exit 2; }
  fi
fi
