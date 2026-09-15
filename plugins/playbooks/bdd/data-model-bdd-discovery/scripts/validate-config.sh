#!/usr/bin/env bash
set -euo pipefail
# 正本: 公開playbook.ymlとwrite-doc/write-doc v2の新規保存契約。
# 入力: 解決後のplaybook JSON。正規化: jqで配列・文字列の完全一致を見る。
# 合格述語: output_directory/nameが公開入力にあり、document工程が両方をneedし、旧output_target/out_dirを持たない。
# 診断: 本scriptの契約違反。正例: 両入力がdocumentへ到達。反例: output_targetだけ。境界例: 一方だけは不合格。
# 意味評価: 実pathの書込可否、名前の妥当性、本文品質は同じagentが読む。
file="$1"
jq -e '
  .inputs==["user_input","referenced_artifacts","output_directory","name"] and
  (has("out_dir")|not) and
  .agent_work.owner=="invoking_agent" and
  .agent_work.delivery=={"provider":"write-doc","input_mapping":{"material_kind":"text","material_content":"final_markdown"}} and
  .agent_work.temporary_files.location=="system_temporary_directory" and .agent_work.temporary_files.delete_only_after=="document_saved" and
  [.steps[].id]==["settle","ground","explore","scenarios","validate-scenarios","logical-model","document"] and
  [.steps[] | (.agent_work // .script // .playbook)]==["grill","invoking_agent","invoking_agent","invoking_agent","scripts/scenario_matrix.py","invoking_agent","write-doc"] and
  all(.steps[] | select(has("agent_work")); .agent_work=="invoking_agent") and
  ([.steps[] | select(has("skill") or has("plugin"))]|length)==0 and
  ([.steps[] | select(has("playbook")) | .playbook]==["grill","write-doc"]) and
  .steps[-1].needs==["logical_bdd_scenarios","logical_data_model","final_markdown","validation_report","output_directory","name"] and (.steps[-1].provides|index("logical_document_path")!=null)
' "$file" >/dev/null || { echo "[error] data-model-bdd-discoveryはYAML宣言順、同一agentの認知工程、決定論的検査、text資料化の構造契約を満たすこと" >&2; exit 2; }
