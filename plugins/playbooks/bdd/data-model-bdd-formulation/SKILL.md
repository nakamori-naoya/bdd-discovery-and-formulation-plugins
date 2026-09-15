---
name: formulate-data-model
description: 既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新する。その論理構造を変えず、設定されたRDB製品・バージョンのRead、型、index、分離レベル、配置へ写す。「データモデルを定式化して」「論理設計を深掘りして物理設計して」と言われたときに使う。
---

# データモデルを定式化する

**既存の論理資料を反証して深化させる。** 新しい論理資料を作らず、入力された`rdb-logical-data-modeling`を同じパスで更新してから物理設計へ進む。

## 1. 実行契約と対象RDBを受け取る

このSKILLを実行する同じagentが、同じdirectoryの`playbook.yml`と本文から参照する資料を全文読み、利用者の入力と明示された資料を保持した一つの文脈で最後まで判断する。`playbook.yml`の`steps`、`needs`、`provides`は仕事の順序と前後関係を示す正本であり、宣言順に辿る。`agent_work: invoking_agent`はこのagentが同じ文脈で担う意味ある認知工程、`script:`は明示した実在入力から閉じた結果を得る決定論的tool、`playbook:`は外部公開Skillの直接呼び出しである。外部runtimeによる値注入や、値運搬だけの中間fileを前提にしない。必要な入力、判断、成果、公開Skill結果が無ければ推測せず停止する。

`${.instructions.execution.directive}`と[工程間の契約](references/contract.md)を読み、対象RDBと成果の境界を確定する。まだ`${.playbook.steps}`は実行しない。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各工程で意識することを補う。`grill`工程には実行指示書のdata model formulation固有の文脈を`context`と`questions`として渡し、相手に永続化やQAの観点を求めない。

[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む。`playbook:`の工程（`grill`、`write-doc`）は、そこに書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。

**資料保存は版2の直接呼び出しである。** `write-doc`には型付き`material`と明示した保存先を直接渡す。返された`status: completed`と保存済みMarkdownの絶対パスを確認し、`path`を`updated_logical_document_path`へ対応させる。更新時は`path == update_target`も確認する。失敗や結果欠落なら後続工程と素材削除へ進まない。入力・出力YAMLや相手の設定解決は使わない。

`grill:grill`が直接返した`decisions`と`open_questions`を利用者入力・明示資料と突き合わせ、同じagentが根拠づけられた入力を確定する。`grounded_input`はこの確認済み集合の論理名であり、別の認知担当から受け取る中間成果ではない。

後片付けは、最終資料の保存成功を確認した同じagentが`${.playbook.agent_work.temporary_files}`に従い、system temporary directory内に自分が作った検査用fileだけへ明示pathで適用する。保存失敗時は削除しない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。変更するBDDごとに条件マトリクスを作り、対応する検査工程の成功結果を確認する。

## 2. 定式化へ進める入力かを最初に評価する

[入力に根拠づける規律](references/input-grounding.md)を読み、`${.playbook.steps}`の最初の`grill`工程へ利用者の説明と既存論理資料を`context`・`questions`・`grounding`として渡す。不明点や深掘りが必要な点を利用者へ1問ずつ確認し、返った`decisions`と`open_questions`を`ground`工程が`grounded_input`へ束ねる。次に[定式化へ進める共通理解かを見極める](references/formulation-readiness.md)を読み、`grounded_input`をLLMが意味から評価する。語の有無、点数、項目数、scriptで代用しない。対話後も代表的な永続化の振る舞いを説明する基準が無ければ、未決と回答責任者を示し、`data-model-bdd-discovery`を案内してここで終了する。残りのQA反証、資料更新、物理設計は始めない。

進める場合は、代表的な共通理解をどの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。

## 3. 既存の論理資料を永続化の観点で反証する

`${.instructions.execution.directive}`に従って最初の`grill`工程より後も、同じagentが利用者の回答、根拠、既存資料、前工程の判断を保持して順に進む。[重要なシナリオを見つけるQA観点](references/important-scenarios.md)と[正規化中心の論理モデリング規律](references/normalized-method.md)を全文読む。`grounded_input`にならない業務用語・イベント・概念を後続へ渡さない。論理モデル責務では正規化中心の規律、RDB設計責務では`${.playbook.database.product}`と`${.playbook.database.version}`を適用する。

`rdb-logical-data-modeling`型の既存論理資料の絶対パスと、物理資料の新規保存先である`physical_output_directory`と`physical_name`を最初の工程へ渡す。前者は既存の書き込み可能な絶対directory、後者はパス要素を含まない`.md`名でなければならない。資料が無い、論理資料の更新先が別パス、物理資料の保存先が無いまたは同名fileがある、BDDと論理テーブルの対応が読めない場合は止まる。

作成・更新・削除に関係するBDDだけを、`${.playbook.contract.probe_dimensions}`で反証する。境界、精度と単位、状態遷移、順序、重複、同時実行、権限内の悪用、時間、規則変更の遡及、失敗時保証によって残す事実や履歴が変わるかを見る。Readやindexを論理設計へ混ぜない。

確認済みの発見は既存資料のBDD、事実、論理テーブル、列、業務制約へ戻す。未決は推測で埋めない。既存資料の同じ絶対パスであることを検査し、その絶対pathを`update_target`、同じ文脈で完成させた改訂Markdown本文を`{kind: text, content: <完成本文>}`の1要素配列にして`material`、`rdb-logical-data-modeling`を`document_type`として`write-doc`工程へ渡して差し替える。**新規作成の指定（`output_directory`と`name`）は渡さない。** 保存先を相手に作り直させない。

更新先検査工程が、入力論理資料と同じ絶対pathを`update_target`として返したことを確認する。`document_type: rdb-logical-data-modeling`はwrite-doc公開契約のtemplate選択値であり、consumerからprovider内部templateのpathへ到達しない。

## 4. 論理構造を変えずに物理設計する

[RDB物理設計へ写す判断規律](references/physical-design-judgment.md)を全文読み、`update-logical-document`が保存成功した`updated_logical_document_path`だけを`design-physical`工程へ渡して同じagentが適用する。論理資料の保存成功前に物理設計を始めない。対象は`${.playbook.database.product}` `${.playbook.database.version}`であり、その版の公式資料または実機で確認できない機能は使わない。

物理設計では、業務で典型的かつ重要なRead、絞り込み、並び順、結合、必要な鮮度、想定件数を記録してからindexを決める。BDD形式にはせず、論理資料へ再掲しない。論理テーブル定義も複製せず、入力論理資料を一つ明記したうえで物理制約、型、index、分離レベル、配置、容量・性能・運用を書く。

論理設計で見つけた同時実行上の必要保証を、対象RDBの分離レベル、制約、ロック、競合時の再試行へ写す。物理設計で構造変更が必要なら、物理側で補わず論理設計へ戻す。

同じagentが完成させた物理設計本文を`{kind: text, content: <完成本文>}`として`document-physical`から`write-doc`へ渡す。`document_type`はwrite-doc公開契約のtemplate選択値`rdb-physical-design`、保存先は確認済み入力をそのまま`output_directory: ${physical_output_directory}`と`name: ${physical_name}`に対応させる。consumerからprovider内部templateのpathへ到達しない。返された`status: completed`と`path`が指定した新規保存先に完全一致することを確認し、その`path`を`physical_rdb_design_path`に対応させるまで完了にしない。

## 5. 報告する

- 対象RDBと版、使った論理モデリング手法
- 同じパスで更新したBDD付き論理設計、RDB物理設計、機能根拠台帳のパス
- QA反証で変化した永続化の理解、追加・修正したBDD、未回答の問い
- 物理設計で採用した典型Readとindex、その順序の理由
- 論理構造を物理資料へ重複させず、変更もしていないこと
- NULLを許した箇所、選択した分離レベル、競合時の扱い

同梱工程のexit 2、または検査失敗なら後続へ進まない。`grill`は直接返された結果objectの`status: completed`と型付き`decisions`・`open_questions`、`write-doc`は直接返された結果objectの`status: completed`で成功を判断する。設定形式は[README](README.md)を参照する。
