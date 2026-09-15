---
name: discover-data-model
description: 業務シナリオと業務イベントから、データの作成・更新・削除に関係する振る舞いを発見し、検査済みBDDとRDB論理データモデルを一つの資料にする。「データモデルのBDDを発見して」「業務イベントから永続化を考えて」と言われたときに使う。
---

# データモデリングのBDDを発見する

**テーブルから始めない。** 何が起きたため、どの事実を、誰の後の判断や説明のために残すのかを確定してから論理構造へ写す。

## 1. 実行契約を受け取る

このSKILLを実行する同じagentが、同じdirectoryの`playbook.yml`と本文から参照する資料を全文読み、利用者の入力と明示された資料を保持した一つの文脈で最後まで判断する。`playbook.yml`の`steps`、`needs`、`provides`は仕事の順序と前後関係を示す正本であり、宣言順に辿る。`agent_work: invoking_agent`はこのagentが同じ文脈で担う意味ある認知工程、`script:`は明示した実在入力から閉じた結果を得る決定論的tool、`playbook:`は外部公開Skillの直接呼び出しである。外部runtimeによる値注入や、値運搬だけの中間fileを前提にしない。必要な入力、判断、成果、公開Skill結果が無ければ推測せず停止する。

`${.playbook.focus}`は`data-model`、`${.playbook.document_type}`は`rdb-logical-data-modeling`に固定される。[このplaybookの焦点](references/focus.md)を読み、Readと物理設計を混ぜない。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各工程で意識することを補う。`grill`工程には実行指示書のdata model固有の文脈を`context`と`questions`として渡し、相手に永続化の観点を求めない。

[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む。`playbook:`の工程（`grill`、`write-doc`）は、そこに書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。

**資料保存は版2の直接呼び出しである。** `write-doc`には型付き`material`と明示した保存先を直接渡す。返された`status: completed`と保存済みMarkdownの絶対パスを確認し、`path`を`logical_document_path`へ対応させる。`path`が指定した`output_directory`と`name`による新規保存先に一致することも確認する。失敗や結果欠落なら後続工程と素材削除へ進まない。入力・出力YAMLや相手の設定解決は使わない。

`grill:grill`が直接返した`decisions`と`open_questions`を利用者入力・明示資料と突き合わせ、同じagentが根拠づけられた入力を確定する。`grounded_input`はこの確認済み集合の論理名であり、別の認知担当から受け取る中間成果ではない。

後片付けは、最終資料の保存成功を確認した同じagentが`${.playbook.agent_work.temporary_files}`に従い、system temporary directory内に自分が作った検査用fileだけへ明示pathで適用する。保存失敗時は削除しない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。永続化シナリオを資料へ写す前に条件マトリクスを作り、対応する検査工程の成功結果を確認する。

## 2. 永続化の振る舞いを先に発見する

[入力に根拠づける規律](references/input-grounding.md)、[永続化から論理モデルへ写す判断規律](references/modeling-judgment.md)、[正規化中心の論理モデリング規律](references/normalized-method.md)を全文読む。利用者の発言、明示された資料、`grill`工程で確認した決定にない業務用語・イベント・概念を作らない。`${.playbook.steps}`の認知責務を同じagentが順に実行し、`explore`と`scenarios`では判断規律の「永続化シナリオ」、`logical-model`では「論理モデル」と正規化中心の規律を適用する。アクター、事前状態、業務イベント、条件、判断、結果、次状態から、初めて成立する事実、追加する履歴、保持理由、物理削除を許す条件を確かめる。

`${.playbook.contract.persistence_operations}`の作成・更新・削除を、シナリオありまたは理由つき対象外として全て検討する。不明点や深掘りが必要な点は`grill`工程で利用者へ1問ずつ確認し、`ground`工程が束ねた`grounded_input`にならない仮説を後続へ渡さない。未確認事項が残る、対象操作のシナリオが無い、業務上の取消と物理削除が混ざる場合は論理モデルへ進まない。

ここでは業務担当者が認識している代表的な永続化の共通理解を作る。境界値、同値分割、順序逆転、重複、同時実行、読み取り特性を体系的に反証しない。それらによる深化は、完成した論理資料を入力にするdata-model-formulationが担う。

## 3. 論理モデルへ写す

検査済みシナリオだけを論理モデル工程へ渡す。各シナリオを独立したGiven・When・Thenにし、BeforeとAfterの双方へ全論理テーブルを同じ順序で置く。0件は「レコードなし」、変化しないものは「変更なし」と明記する。

物理名、物理型、索引、分離レベル、パーティション、SQL、API、DTO、ORMは書かない。現在の姿を持つリソース系と、成立済みの業務イベントを残すイベント系を区別する。

## 4. RDB論理設計資料として保存する

開始時に公開入力の`output_directory`が既存の書き込み可能な絶対directory、`name`がパス要素を含まない`.md`名であることを確かめる。不明・相対path・同名fileが既存する場合は推測や上書きをせず停止する。論理モデルとBDDを同じ文脈で1つのMarkdown本文へまとめ、`{kind: text, content: <完成本文>}`の1要素配列にして`material`、`${.playbook.document_type}`を`document_type`、確認済みの2入力をそのまま`output_directory`と`name`に渡す。BDDは本文の末尾に置く。`document_type: rdb-logical-data-modeling`はwrite-doc公開契約のtemplate選択値であり、consumerからprovider内部templateのpathへ到達しない。

## 5. 報告する

永続化シナリオ、BDDを含むRDB論理設計資料の絶対パス、CUDの扱い、追加記録にした変化、保持・削除条件、未決を報告する。
