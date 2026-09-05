---
name: write-persistence-scenarios
description: 既存の業務シナリオと業務イベントから、データの作成・更新・削除に関係する断面を選び、アクター、事前状態、業務イベント、判断、残す事実、次状態、履歴、保持理由を永続化シナリオとして記録する。3操作を検討済みで、未確認事項のない資料をデータモデリング工程へ渡す。「永続化シナリオを作って」「データモデリングの前提を整理して」と言われたときに使う。
---

# write-persistence-scenarios（永続化シナリオを先に書く）

**データの形を考える前に、何が起きたため何を残すのかを書く。** 作成・更新・削除はSQL操作ではなく、業務上の事実が初めて成立する、別の事実によって現在状態が変わる、保持理由が尽きて物理的に消せる、という観点で扱う。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
BUNDLE_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
if [ -d "${BUNDLE_ROOT}/skills/data-modeling/persistence-scenarios" ]; then
  PLUGIN_ROOT="${BUNDLE_ROOT}/skills/data-modeling/persistence-scenarios"
else
  PLUGIN_ROOT="${BUNDLE_ROOT}"
fi
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 設定と判断材料を読む

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
printf '%s\n' "$CFG_FILE"
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.actors_stakeholders}`、`${.domain_events}`、`${.ubiquitous_language}`を必ず読む。成果は`${.scenario_dir}`へ置く。ここでは既存の業務シナリオから永続化に必要な断面だけを選び、目的や経路を再設計せず、エンティティ、テーブル、正本方式、投影を決めない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。永続化シナリオごとに条件マトリクスを作り、`python3 "${PLUGIN_ROOT}/scripts/scenario_matrix.py" check --file <condition-matrix.json>`を通す。単一失敗では検証対象以外の必要条件をすべて成立させる。

## 2. 作成・更新・削除を検討した証拠を残す

利用者の業務シナリオ、業務イベント台帳、業務資料を先に読む。資料に無い判断を補わず、未確認として止める。各操作が必要なら`covered`、業務上存在しないなら理由つきの`not-applicable`を記録する。

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" coverage --config "$CFG_FILE" --topic <題材> --operation <create|update|delete> --status <covered|not-applicable> --reason '<根拠>'
```

## 3. 永続化シナリオを記録する

一つのシナリオには、一つの業務イベントと一つの永続化上の変化だけを置く。API、DTO、SQL、テーブル、ORMなどの実現方法は書かない。

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" add --config "$CFG_FILE" --topic <題材> \
  --title '<場合>' --actor '<アクター>' --prior-state '<事前状態>' --event '<業務イベント>' \
  --condition '<条件|追加条件なし>' --decision '<業務判断>' --result '<業務上の結果>' --next-state '<次状態>' \
  --operation <create|update|delete> --fact '<残す・変える・消せる事実>' \
  --history '<過去の何を残すか|履歴不要>' --retention '<物理削除を許す条件|未決>' --source '<元のシナリオ・イベント>' --status <confirmed|assumed|unknown>
```

更新では上書きか新しい事実の追加か、削除では業務上の取消・失効と物理削除を分ける。現在状態だけでなく、後の判断、取消、訂正、説明に必要な事実を確かめる。

## 4. 資料化してから次へ渡す

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" check --config "$CFG_FILE" --topic <題材>
python3 "${PLUGIN_ROOT}/scripts/scenario.py" render --config "$CFG_FILE" --topic <題材>
```

3操作が未検討、`covered`なのにシナリオが無い、未確認のシナリオがある場合は止まる。通った資料だけをデータモデリングへ渡す。

## 5. 報告する

台帳と資料のパス、操作別件数、追加記録にした変化、物理削除を許す条件、仮置きのシナリオを報告する。データモデル、DDL、API設計へは進まない。

## 実行設定の寿命

prepareが返した絶対pathを実行記録へ保持する。別shellではそのpathを`CFG_FILE`へ明示して読み、shell変数の継承を前提にしない。完了時と失敗停止時のどちらも、最後の設定利用後に`python3 "${PLUGIN_ROOT}/scripts/run-config.py" cleanup --config "$CFG_FILE"`を実行する。他runの設定やdirectoryを削除しない。
