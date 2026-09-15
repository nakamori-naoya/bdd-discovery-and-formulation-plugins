---
name: discover-user-journey
description: 1人の主たるユーザーが1つの目的を達成するまでを発見し、開始地点、完了条件、接続した場面のBDDを最初の正本として1本作る。「ユーザーJourneyをBDDで発見して」「目的達成までの振る舞いを初めて資料にして」と言われたときに使う。既存正本の深化、ドメインルール、データモデル、テスト実行は扱わない。
---

# ユーザー目的達成BDDの正本を初めて作る

**これは、目的達成までの連続性を最初の正本にするplaybookである。** Journey mapから、開始地点、観測可能な完了、意味のある場面、状態の受け渡しをBDDとして1本へまとめる。

**これはユースケース、UX Journey map、ドメインルール、データモデル、テスト仕様ではない。** 対象システム一つの責任、感情と接点、個別の業務判断、保存構造、実行方法はそれぞれの正本へ返す。既存のユーザー目的達成BDDを直す場合は`formulate-user-journey`を使う。

## 1. 実行契約を受け取る

このSKILLを実行する同じagentが、同じdirectoryの`playbook.yml`と本文から参照する資料を全文読み、利用者の入力と明示された資料を保持した一つの文脈で最後まで判断する。`playbook.yml`の`steps`、`needs`、`provides`は仕事の順序と前後関係を示す正本であり、宣言順に辿る。`agent_work: invoking_agent`はこのagentが同じ文脈で担う意味ある認知工程、`script:`は明示した実在入力から閉じた結果を得る決定論的tool、`playbook:`は外部公開Skillの直接呼び出しである。外部runtimeによる値注入や、値運搬だけの中間fileを前提にしない。必要な入力、判断、成果、公開Skill結果が無ければ推測せず停止する。

`${.instructions.execution.directive}`に従い、`${.playbook.steps}`を上から順に実行する。[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は順序・依存・入出力を決め、実行指示書は背景、前提、目的と各工程で意識することを補う。`grill`工程へJourney固有の観点を`context`と`questions`として渡し、相手にその観点を持たせない。

[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む。`playbook:`の工程（`grill`、`write-doc`）は、そこに書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。

**資料保存は版2の直接呼び出しである。** `write-doc`には型付き`material`と明示した保存先を直接渡す。返された`status: completed`と保存済みMarkdownの絶対パスを確認し、`path`を`user_journey_bdd_path`へ対応させる。`path`が指定した`output_directory`と`name`による新規保存先に一致することも確認する。失敗や結果欠落なら後続工程と素材削除へ進まない。入力・出力YAMLや相手の設定解決は使わない。

`grill:grill`が直接返した`decisions`と`open_questions`を利用者入力・明示資料と突き合わせ、同じagentが根拠づけられた入力を確定する。`grounded_input`はこの確認済み集合の論理名であり、別の認知担当から受け取る中間成果ではない。

後片付けは、最終資料の保存成功を確認した同じagentが`${.playbook.agent_work.temporary_files}`に従い、system temporary directory内に自分が作った検査用fileだけへ明示pathで適用する。保存失敗時は削除しない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。場面ごとに条件マトリクスを作り、対応する検査工程の成功結果を確認する。失敗場面の業務ルールが別資料にある場合は、`NOTE:`の`Source:`から外部正本の見出しを参照し、本文を複製しない。

同じagentが利用者の入力と前工程で得た判断を保持して進み、決定論的toolの失敗結果を受けたら後続へ進まない。

## 2. Journeyに該当するかを先に決める

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、`grill`工程で確認した`decisions`だけを`ground`工程で`grounded_input`へ束ねる。

[Journeyを判定し接続する判断規律](references/journey-judgment.md)を全文読み、`map-journey`で何がJourneyで何がJourneyでないかを判定する。ユーザーの目的、開始地点、最終地点、完了条件のどれかが分からなければ場面を書き始めない。目的ではなく機能利用が中心、意味のある場面が一つだけ、対象システム一つの責任だけを問う依頼ならJourneyへ広げず、非該当理由と適切な成果物を返して停止する。

## 3. 長さを削らず、場面へ分けて接続する

[Journeyの構造](references/journey-structure.md)、[Journeyを判定し接続する判断規律](references/journey-judgment.md)、[場面のBDD](references/scenario-writing.md)を適用する。

主たるユーザーの視点を各場面の軸にする。`When`にはそのユーザーまたは協働役割が行うこと、`Then`には主たるユーザーが見える、知らされる、判断できる、または次にできるようになることを書く。期間の開始・対象化・保存状態など内部の論理状態だけを応答や完了条件にせず、その境界が利用者へもたらす観測可能な結果まで表す。時刻の包含・除外など確認済みの業務境界は言い換えによって変えない。語彙は利用者が実際に使う自然な行動や状態の言葉を入力根拠から選び、内部モデル用の造語へ置き換えない。

Journey全体に場面数の上限を置かない。目的達成までに必要な意味のある変化は省略しない。その代わり、全体を複数の場面へ分け、各場面で次を明らかにする。

```text
前の場面から受け取った状態
→ その場面で行う役割と働きかけ
→ 観測できる応答
→ 次の場面へ渡す状態
```

各場面は1組のGiven / When / Thenを中心に書く。ストーリー全体には複数のWhen / Thenがあってよい。前の場面の結果と次の場面の前提がつながらない場合は、間を推測で埋めず未決にする。

## 4. 責務を越えない

既存のdomain-ruleやdata model資料は入力根拠として読めるが、変更しない。新しい業務ルールを確定したり、保存する事実や構造を設計したりしない。そこに不足が見つかった場合は未決として残し、対応するdomainまたはdata modelのpluginへ送る。

画面、ボタン、URL、API、endpoint、request、response、DB、tableなど、実現方法の手順へ落とさない。test runner、実行環境、試行回数、証拠、CI、flakyなど、テスト実行の関心も書かない。

## 5. 検査して資料化する

条件マトリクスとBDD本文に対する検査工程の成功結果が無ければ資料化しない。開始時に公開入力の`output_directory`が既存の書き込み可能な絶対directory、`name`がパス要素を含まない`.md`名であることを確かめる。不明・相対path・同名fileが既存する場合は推測や上書きをせず停止する。同じ文脈で完成させたMarkdown本文を`{kind: text, content: <完成本文>}`の1要素配列にして`material`、`${.playbook.document_type}`を`document_type`、確認済みの2入力をそのまま`output_directory`と`name`に渡し、最初の正本を1本保存する。指定先に正本がすでにあるという工程結果なら上書きせず、formulationへ切り替える。

## 6. 報告する

- 作成したユーザー目的達成BDD正本の絶対パス
- ユーザーの目的、開始地点、最終地点、完了条件
- 目的達成までの場面数と主要な接続
- 未決の接続と、確認すべき人
- ユースケース、UX Journey map、domain、data model、実装、テスト実行へ送り返した事項
