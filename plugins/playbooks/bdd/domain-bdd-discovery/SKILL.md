---
name: discover-domain
description: コアドメインの業務知識と代表的な振る舞いを共通理解にし、BDDを含むdomain-ruleの正本を1本作る。業務イベント、事前状態、アクター、判断、次状態を整理する。「業務知識をBDD付きで整理して」「コアドメインを発見して」と言われたとき、実装やQA反証へ進む前に使う。
---

# domain-bdd-discovery（共通理解を正本にする）

**作りを全部やめても残るものだけを残す。** 画面も保存も手順も、作り替えれば変わる。変わるものを正本へ入れると、作りを変えるたびに正本が腐る。

**探求が先で、記述は後である。** 何が起きるのかを知らないまま型を埋めにいくと、型の穴を埋めるための作り話が入る。

## 1. 実行契約を受け取り、書かれた順に進める

このSKILLを実行する同じagentが、同じdirectoryの`playbook.yml`と本文から参照する資料を全文読み、利用者の入力と明示された資料を保持した一つの文脈で最後まで判断する。`playbook.yml`の`steps`、`needs`、`provides`は工程順と前後関係の正本であり、宣言順に辿る。`agent_work: invoking_agent`はこのagentが同じ文脈で担う意味ある認知工程、`script:`は明示した実在入力から閉じた結果を得る決定論的tool、`playbook:`は外部公開Skillの直接呼び出しである。外部runtimeによる値注入や、値運搬だけの中間fileを前提にしない。必要な入力、判断、成果、公開Skill結果が無ければ推測せず停止する。

`playbook.yml`の`instructions.execution.directive`と`contract`を直接読み、同じagentの判断基準へ適用する。新規保存先は公開入力の`output_directory`と`name`だけから決める。`requires`のうち同梱する`domain-events`と`core-domain`はその責務・資料をこのagentが適用し、外部の`grill`と`write-doc`だけを公開Skillとして呼ぶ。未生成の依存解決objectや解決済み設定を工程へ渡す前提は置かない。契約の役を確認するときだけ[役の契約](references/roles.md)を読む。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各工程で意識することを補う。`grill`工程には実行指示書のdomain固有の文脈を`context`と`questions`として渡し、相手にdomainの観点を求めない。

[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む。`playbook:`の工程（`grill`、`write-doc`）は、そこに書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。

**資料保存は版2の直接呼び出しである。** `write-doc`には型付き`material`と明示した保存先を直接渡す。返された`status: completed`と保存済みMarkdownの絶対パスを確認し、`path`を`domain_rule_path`へ対応させる。`path`が指定した`output_directory`と`name`による新規保存先に一致することも確認する。失敗や結果欠落なら後続工程と素材削除へ進まない。入力・出力YAMLや相手の設定解決は使わない。

`grill:grill`が直接返した`decisions`と`open_questions`を利用者入力・明示資料と突き合わせ、同じagentが根拠づけられた入力を確定する。`grounded_input`はこの確認済み集合の論理名であり、別の認知担当から受け取る中間成果ではない。

後片付けは、最終資料の保存成功を確認した同じagentが`${.playbook.agent_work.temporary_files}`に従い、system temporary directory内に自分が作った検査用fileだけへ明示pathで適用する。保存失敗時は削除しない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。代表BDDを書く前に条件マトリクスを作り、対応する検査工程の成功結果を確認する。必要条件が不明ならgrillへ戻し、暗黙に成立させない。

同じagentが利用者の入力と前工程で得た判断を保持して進む。決定論的toolが失敗結果を返したら先へ進まない。

## 2. 利用者が持っている知識から始める

**題材と、利用者がすでに知っていることを先に受け取る。** [入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、grillで確認した決定にない業務用語・イベント・概念を作らない。不明点や深掘りはgrill工程で1問ずつ確認し、`grounded_input`にならない仮説を後続へ渡さない。

受け取ったものは、そのまま事実として扱わない。**誰が確かめたのかで確からしさが変わる。** `${.playbook.contract.confidence}` の語で区別したまま先へ渡す。

## 3. 線が引けるまで、書く工程へ進まない

**「どこまでが業務の話か」が決まらないうちに書き始めると、実装の話が混ざったまま正本になる。** 線引きの工程を飛ばさない。

`${.playbook.requirements.exclude_implementation}` が `true` のとき、実装の関心を落とす工程は外せない。落とせない工程を落とすと、解決の時点で止まる。

## 4. コアの代表的な振る舞いを共通理解にする

**支援・汎用まで同じ丁寧さで問い詰めると、いちばん大事なところへ手が回らない。** 問い詰める工程へは、コアと判定した範囲を渡す。

[振る舞い発見](references/behavior-discovery.md)、[アクターとステークホルダー](references/actors-and-stakeholders.md)、[業務ルール](references/domain-rules.md)、[ユビキタス言語](references/ubiquitous-language.md)、[共通理解を作る問い](references/questions.md)を読み、コアについて次を一続きで確かめる。

ユビキタス言語は、業務関係者が仕事の会話と判断で合意して使う語、その業務上の意味、使用文脈としてまとめる。バックエンドの部品名、保存方式、内部状態名を混ぜず、技術語を平易な独自語へ言い換えて業務語に見せない。対応する合意語が無ければ作らず、回答責任者つきの未決へ戻す。

```text
役割の目的 + 協働役割 + 事前状態 + 業務イベント + 条件
→ 判断権者の業務判断 → 観測できる結果 + 次状態 + 引継ぎ + 後続イベント
```

典型、既知の代替、既知の拒否を代表BDDにする。境界値、同値分割、順序逆転、重複、同時実行などを体系的に反証しない。それは共通理解を作った後のformulationが担う。

## 5. 確からしさを落とさずに束ねる

同じagentが確定した事実、線引き、決定から振る舞い断面と代表BDDを作り、1つの素材へ束ねる。事実、線引き、決定、振る舞い、代表BDDのどれかが欠けていたら資料化しない。[成果物の形](references/discovery-deliverable.md)に沿って本文の要求を決める。

保存は`write-doc`工程が行う。開始時に公開入力の`output_directory`が既存の書き込み可能な絶対directory、`name`がパス要素を含まない`.md`名であることを確かめる。不明・相対path・同名fileが既存する場合は推測や上書きをせず停止する。同じ文脈で完成させたMarkdown本文を`{kind: text, content: <完成本文>}`の1要素配列にして`material`、`${.playbook.document_type}`を`document_type`、確認済みの2入力をそのまま`output_directory`と`name`に渡し、1本だけ保存する。`references`には[成果物の形](references/discovery-deliverable.md)の絶対pathを渡す。

## 6. 報告する

- BDDを含む正本のパスと、扱った題材
- コアの代表的な振る舞い断面
- **未確認のまま残った事実と、誰に聞けば確かめられるか**
- スコープ外へ落としたものと、その理由
- まだ決まっていない論点

設定形式は[README](README.md)を参照する。モデルと推論の強さは決定的でないため設定に持たない。
