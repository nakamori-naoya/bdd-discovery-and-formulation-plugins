---
name: formulate-domain
description: コアドメインの既存domain-rule資料をQA観点で反証し、境界シナリオ、新しい業務理解、未決の問いを同じ資料へ戻して深化させる。「BDDを定式化して」「境界値も含めてドメイン資料を深掘りして」と言われたときに使う。新規資料は作らない。
---

# ドメインの振る舞いをBDDへ定式化する

**共通理解を反証して深化させる。** 新しい資料を作らず、入力された既存のdomain-ruleだけを更新する。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 工程と焦点を解決する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.playbook.focus}`は`domain`に固定される。既存資料のパスが無い、資料内でコアの範囲が分からない、更新先に別パスを指定された場合は停止する。[このplaybookの焦点](references/focus.md)を読み、支援・汎用を反証対象へ広げない。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各skillで意識することを補う。grill工程には実行指示書のdomain formulation固有の文脈を与え、grill自身にdomainやQAの観点を求めない。

## 2. 定式化へ進める入力かを最初に評価する

[入力に根拠づける規律](references/input-grounding.md)を読み、`${.playbook.steps}`の最初のgrill工程へ利用者の説明と既存資料を渡す。不明点や深掘りが必要な点を利用者へ1問ずつ確認し、確認済みの回答だけを`grounded_input`にする。次に[定式化へ進める共通理解かを見極める](references/formulation-readiness.md)を読み、`grounded_input`をLLMが意味から評価する。語の有無、点数、項目数、scriptで代用しない。対話後もコアの代表的な業務を説明する基準が無ければ、未決と回答責任者を示し、`domain-bdd-discovery`を案内してここで終了する。残りの`${.playbook.steps}`や資料更新は始めない。

進める場合は、代表的な共通理解をどの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。

## 3. コアの既存理解をQA観点で反証する

最初のgrill工程より後の`${.playbook.steps}`を順に実行し、各工程へ`--scope=${.resolution.scope_root}`を渡す。[重要なシナリオを見つけるQA観点](references/important-scenarios.md)を読み、[コアドメインへの適用](references/qa-probes.md)に従う。`grounded_input`にならない業務用語・イベント・概念を後続へ渡さない。既存理解で説明できたもの、確認済みの修正、回答責任者つきの未決、コアの外へ分ける。網羅感のためにシナリオを増やさない。

確認済みの発見だけを既存資料のユビキタス言語、業務ルール、状態、アクター、BDDへ戻す。未確認の疑問は決まりにせず未回答の問いへ置く。QA手法の説明は資料へ書かない。

## 4. 変更するBDDを定式化して検査する

[シナリオの書き方](references/writing.md)と[Givenの選び方](references/given.md)に従う。複数主体や知識差が結果を変える場合だけ[登場人物と情報差](references/actors.md)を読む。

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" check --config "$CFG_FILE" --file <下書き>
python3 "${PLUGIN_ROOT}/scripts/update-guard.py" --existing <入力資料> --output <更新先>
```

違反、未確認の決まり、別パスへの出力があれば更新しない。

## 5. 既存資料を同じパスで更新する

既存資料を読んだうえで、検査済みBDD、確認済みの理解、`update-guard.py`が返した`update_target`を資料化工程へ渡す。型は`${.playbook.document_type}`の`domain-rule`、媒体は`output_format=${.playbook.output_format}`に固定し、入力資料と同じ絶対パスへ差し替える。`output.dir`から別の保存先を作らない。差し替え後もコア以外の記述を勝手に深化させない。

## 6. 報告する

更新した既存資料の絶対パス、追加・修正したBDD、変化した業務理解、未回答の問い、コアの外へ送った事項を報告する。新規資料が無いことも明記する。
