---
name: formulate-data-model
description: 既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新する。その論理構造を変えず、設定されたRDB製品・バージョンのRead、型、index、分離レベル、配置へ写す。「データモデルを定式化して」「論理設計を深掘りして物理設計して」と言われたときに使う。
---

# データモデルを定式化する

**既存の論理資料を反証して深化させる。** 新しい論理資料を作らず、入力された`rdb-logical-data-modeling`を同じパスで更新してから物理設計へ進む。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 工程と対象RDBを解決する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.instructions.execution.directive}`と[工程間の契約](references/contract.md)を読み、対象RDBと成果の境界を確定する。まだ`${.playbook.steps}`は実行しない。

## 2. 定式化へ進める入力かを最初に評価する

[入力に根拠づける規律](references/input-grounding.md)を読み、`${.playbook.steps}`の最初のgrill工程へ利用者の説明と既存論理資料を渡す。不明点や深掘りが必要な点を利用者へ1問ずつ確認し、確認済みの回答だけを`grounded_input`にする。次に[定式化へ進める共通理解かを見極める](references/formulation-readiness.md)を読み、`grounded_input`をLLMが意味から評価する。語の有無、点数、項目数、scriptで代用しない。対話後も代表的な永続化の振る舞いを説明する基準が無ければ、未決と回答責任者を示し、`data-model-bdd-discovery`を案内してここで終了する。残りのQA反証、資料更新、物理設計は始めない。

進める場合は、代表的な共通理解をどの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。

## 3. 既存の論理資料を永続化の観点で反証する

`${.instructions.execution.directive}`に従って最初のgrill工程より後の`${.playbook.steps}`を順に実行し、各工程へ`--scope=${.resolution.scope_root}`を渡す。[重要なシナリオを見つけるQA観点](references/important-scenarios.md)を読む。`grounded_input`にならない業務用語・イベント・概念を後続へ渡さない。論理モデル工程には`--override=method=${.playbook.modeling.method}`、RDB設計工程には`--override=database.product=${.playbook.database.product}`と`--override=database.version=${.playbook.database.version}`を渡す。

`rdb-logical-data-modeling`型の既存論理資料の絶対パスを最初の工程へ渡す。資料が無い、出力先が別パス、BDDと論理テーブルの対応が読めない場合は止まる。

作成・更新・削除に関係するBDDだけを、`${.playbook.contract.probe_dimensions}`で反証する。境界、精度と単位、状態遷移、順序、重複、同時実行、権限内の悪用、時間、規則変更の遡及、失敗時保証によって残す事実や履歴が変わるかを見る。Readやindexを論理設計へ混ぜない。

確認済みの発見は既存資料のBDD、事実、論理テーブル、列、業務制約へ戻す。未決は推測で埋めない。既存資料の同じ絶対パスであることを次で検査し、返された`logical_update_target`と`output_format=${.playbook.output_format}`を`write-doc`へ渡して差し替える。`output.dir`から別の保存先を作らない。

```bash
python3 "${PLUGIN_ROOT}/scripts/update-guard.py" --existing <入力論理資料> --output <更新先>
```

## 4. 論理構造を変えずに物理設計する

更新済み論理資料だけを物理設計へ渡す。対象は`${.playbook.database.product}` `${.playbook.database.version}`であり、その版の公式資料または実機で確認できない機能は使わない。

物理設計では、業務で典型的かつ重要なRead、絞り込み、並び順、結合、必要な鮮度、想定件数を記録してからindexを決める。BDD形式にはせず、論理資料へ再掲しない。論理テーブル定義も複製せず、入力論理資料を一つ明記したうえで物理制約、型、index、分離レベル、配置、容量・性能・運用を書く。

論理設計で見つけた同時実行上の必要保証を、対象RDBの分離レベル、制約、ロック、競合時の再試行へ写す。物理設計で構造変更が必要なら、物理側で補わず論理設計へ戻す。

## 5. 報告する

- 対象RDBと版、使った論理モデリング手法
- 同じパスで更新したBDD付き論理設計、RDB物理設計、機能根拠台帳のパス
- QA反証で変化した永続化の理解、追加・修正したBDD、未回答の問い
- 物理設計で採用した典型Readとindex、その順序の理由
- 論理構造を物理資料へ重複させず、変更もしていないこと
- NULLを許した箇所、選択した分離レベル、競合時の扱い

どの工程もexit 2または検査失敗なら後続へ進まない。設定形式は[README](README.md)を参照する。
