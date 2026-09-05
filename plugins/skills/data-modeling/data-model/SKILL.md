---
name: design-data-model
description: 業務イベント、事前状態、判断、結果、次状態を含む業務シナリオから、時間を越えて残すべき状態・約束・権利・義務・判断根拠を見出し、BDDシナリオを含む論理データモデルを作る。手法は事実の記録中心・正規化中心・分析中心などから選べ、利用者のファイルも指せる。記録の形と業務シナリオを双方向で突き合わせ、永続化の必要を説明できない要素を残さない。「論理データモデリングして」「何を記録すべきか整理して」「このモデルに要らないものが無いか見て」と言われたときに使う。
---

# design-data-model（業務の永続化を論理設計する）

**保存の形から入らない。** 業務シナリオを観察し、何を記録しないと業務が時間を越えて続かないかを先に決める。**記録の必要を説明できない要素は、手法が何であれ要らない。**

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
BUNDLE_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
if [ -d "${BUNDLE_ROOT}/skills/data-modeling/data-model" ]; then
  PLUGIN_ROOT="${BUNDLE_ROOT}/skills/data-modeling/data-model"
else
  PLUGIN_ROOT="${BUNDLE_ROOT}"
fi
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 手法を決めて、置き場を読む

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

**`method`は依頼のたびに変わる値で、同梱既定に実値を持たない。** 上のコマンドは`method`未指定のため**exit 2で意図して止まる（事故ではない）**。同梱の候補は[事実の記録](references/methods/fact-recording.md)、[正規化](references/methods/normalized.md)、[次元モデル](references/methods/dimensional.md)である。選ぶ1つだけを読む。

依頼で手法が指定されていればそれを使う。明示が無ければ記録対象・監査要件・分析目的などから文脈で判断できるならそれを使い、文脈からも定まらなければ利用者に聞く（同梱一覧を選択肢として示す）。**先頭の候補だけを試さない。**

```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)" --override=method=<決めた手法>) || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

`${.model_dir}`・`${.method.id}`・`${.method.path}`が揃う。`${.instructions.design.directive}`に従い、成果は`${.model_dir}`へ置く。**決め方（依頼指定／文脈推定／確認済み）を必ず報告する。黙って手法を変えない。**

## 2. 手法によらない部分を先に済ませる

`${.fact_contract}`、`${.domain_events}`、`${.event_sourcing}`、`${.data_models}`、`${.concept_map}`、`${.immutable_data_modeling}`、`${.null_avoidance}` を必ず読む。関係データベースへ写す場合は、`${.relational_data_modeling}`と`${.logical_rdb_template}`も読む。**ドメインモデルから業務上の永続化が必要な事実を見つけ、記録すべき事実のシナリオを手法選択より前に洗い出す。** 業務イベントから成立済みの事実を見つけ、正本と現在状態を分ける。NULL、汎用属性、JSON、削除フラグで業務上の違いを隠さない。schema移行、製品version更新、backup、restore、監視、index、実行計画、性能測定は論理設計で扱わない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。論理資料へBDDを置く前に条件マトリクスを作り、`python3 "${PLUGIN_ROOT}/scripts/scenario_matrix.py" check --file <condition-matrix.json>`を通す。

業務イベントとevent record、記録すべき事実、目的別のモデルを分ける。Event Sourcingは履歴が要るというだけでは採用しない。

```bash
python3 "${PLUGIN_ROOT}/scripts/fact.py" add --config "$CFG_FILE" --topic <題材> \
  --element '<モデル要素>' --fact '<記録する事実>' \
  --why-record '<残さないと業務の何が回らなくなるか>' \
  --actor '<その記録を必要とする人>' --source '<どの事実・どの具体例から来たか>' --status assumed
```

**「〜のため」で終わる説明は書けたことにしない。** 記録が無かったとき、誰が何をできなくなるかまで言う。

## 3. BDDシナリオを含む論理モデルへ写す

`${.method.path}` を読む。先に決めること・成果物・向き不向き・見直しの問いはそこにある。**手法ごとに違うのは配置の仕方であって、記録の必要ではない。** RDBの論理設計では`${.logical_rdb_template}`を複製して使う。

モデルは`${.model_dir}`へ書く。入力された全永続化シナリオを資料末尾の`## BDD`へ置き、`### Scenario <ID>: <場合>`、`Given`、`When`、`Then`の形で業務上の条件と結果をデータ構造から読めるようにする。正常系だけでなく、拒否、取消、訂正、削除、同時進行で守るべき結果も必要に応じて追加する。

論理テーブルは`## 論理テーブル定義`の下へ`### \`table_name\`（業務上の名前）`として置く。列はカラム名、PK・FKなどの制約、型、NOT NULL、値域、業務上の意味を表で書き、業務制約は`#### 業務制約: <名前>`として根拠となるBDDへ結ぶ。ここでテーブル、列、業務上のキー、関係、制約を確定する。RDB製品、DDL、index、パーティション、分離レベルは書かない。

## 4. 双方向で突き合わせる

```bash
python3 "${PLUGIN_ROOT}/scripts/fact.py" check --config "$CFG_FILE" --topic <題材> \
  --model-file <論理モデル> --scenario-file <永続化シナリオ台帳>
```

**片側にしかない要素があれば落ちる。** モデルにあるのに記録の必要が説明されていないテーブルは外すか説明を足す。記録すると決めたのにモデルに無いものは落ちている。入力された永続化シナリオがBDDシナリオとして本文に無い場合も止まる。

## 5. 報告する

使った手法と理由、論理モデルのパス、BDDシナリオ数、記録シナリオ数、未確認の記録と確認相手、手法の「見直しの問い」で引っかかった点を報告する。

設定形式は[README](README.md)を参照する。物理設計・移行手順・性能の話へは進まない。物理設計でテーブルや列を変える必要が見つかった場合も、この工程へ戻してBDDシナリオとの対応から見直す。
