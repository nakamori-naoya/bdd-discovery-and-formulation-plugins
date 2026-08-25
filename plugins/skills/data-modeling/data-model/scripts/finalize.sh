#!/usr/bin/env bash
# data-model 固有の検査と、出す形の組み立て。
#
# **resolve.sh から source される。** 設定の解決手順は共通なのでここには無い。
# 使えるもの: merged / required / root / PLUGIN_ROOT / name / selected / source / sources / explain / resolve_path
# やること: 固有schemaの検査と、out への最終JSONの代入。
# method はもう defaults.yml の実値ではなく prompt_parameters の宣言でしか持たない。
# --override=method=<value> が無い限り .method は無く、ここで明示的に止まる。
jq -e '.version==1 and (.model_dir|type=="string" and length>0) and (.method|type=="string" and length>0) and
  (.instructions.design.directive|type=="string" and length>0)' >/dev/null <<<"$merged" \
  || { echo "[error] version、model_dir、design directiveのいずれかが不正。またはmethodが未指定（--override=method=<手法>を渡すこと）" >&2; exit 2; }
model_dir=$(jq -r '.model_dir' <<<"$merged"); model_dir="${model_dir/#\~/$HOME}"
case "$model_dir" in /*) ;; *) model_dir="${root}/${model_dir}" ;; esac
# 手法は同梱のIDか、利用者のファイル。/ も . も含まない語をIDとして扱う。
want=$(jq -r '.method' <<<"$merged")
bundled_method=""
case "$want" in
  */*|*.*) ;;
  *) [ ! -f "$PLUGIN_ROOT/references/methods/${want}.md" ] || bundled_method="$PLUGIN_ROOT/references/methods/${want}.md" ;;
esac
if [ -n "$bundled_method" ]; then
  method_path="$bundled_method"; method_source=bundled
else
  method_path="${want/#\~/$HOME}"
  case "$method_path" in /*) ;; *) method_path="${root}/${method_path}" ;; esac
  [ -f "$method_path" ] || {
    echo "[error] method に指定した手法が無い: ${want}" >&2
    echo "        同梱の手法: $(cd "$PLUGIN_ROOT/references/methods" && ls ./*.md | sed 's|^\./||; s|\.md$||' | tr '\n' ' ')" >&2
    echo "        指したのに無いものを既定へ倒すと、差し替えたつもりで効かない。" >&2
    exit 2
  }
  method_source=file
fi
out=$(jq -cn --arg m "$model_dir" --arg mp "$method_path" --arg ms "$method_source" --arg mi "$want" \
  --arg f "$PLUGIN_ROOT/references/fact-recording-contract.md" \
  --arg de "$PLUGIN_ROOT/references/domain-events.md" --arg es "$PLUGIN_ROOT/references/event-sourcing.md" \
  --arg dm "$PLUGIN_ROOT/references/data-models.md" \
  --arg cm "$PLUGIN_ROOT/references/concept-map.md" \
  --arg im "$PLUGIN_ROOT/references/immutable-data-modeling.md" \
  --arg rd "$PLUGIN_ROOT/references/relational-data-modeling-principles.md" \
  --arg na "$PLUGIN_ROOT/references/null-avoidance.md" \
  --arg rl "$PLUGIN_ROOT/references/relational-data-lifecycle.md" \
  --arg lt "$PLUGIN_ROOT/assets/logical-design.md" \
  --arg root "$root" --arg pr "$PLUGIN_ROOT" --argjson instructions "$(jq -c '.instructions' <<<"$merged")" \
  --arg cfgsrc "$source" --argjson psrc "$sources" \
  '{contract:1, model_dir:$m, method:{id:$mi, path:$mp, source:$ms},
    fact_contract:$f, domain_events:$de, event_sourcing:$es,
    data_models:$dm, concept_map:$cm, immutable_data_modeling:$im,
    relational_data_modeling:$rd, null_avoidance:$na, relational_data_lifecycle:$rl,
    logical_rdb_template:$lt,
    instructions:$instructions, repo_root:$root, plugin_root:$pr,
    resolution:{config_source:$cfgsrc}, _sources:$psrc}')
