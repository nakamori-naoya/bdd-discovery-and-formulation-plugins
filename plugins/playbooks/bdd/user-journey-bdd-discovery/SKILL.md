---
name: discover-user-journey
description: 1人の主たるユーザーが1つの目的を達成するまでを発見し、開始地点、完了条件、接続した場面のBDDを最初の正本として1本作る。「ユーザーJourneyをBDDで発見して」「目的達成までの振る舞いを初めて資料にして」と言われたときに使う。既存正本の深化、ドメインルール、データモデル、テスト実行は扱わない。
---

# ユーザー目的達成BDDの正本を初めて作る

**これは、目的達成までの連続性を最初の正本にするplaybookである。** Journey mapから、開始地点、観測可能な完了、意味のある場面、状態の受け渡しをBDDとして1本へまとめる。

**これはユースケース、UX Journey map、ドメインルール、データモデル、テスト仕様ではない。** 対象システム一つの責任、感情と接点、個別の業務判断、保存構造、実行方法はそれぞれの正本へ返す。既存のユーザー目的達成BDDを直す場合は`formulate-user-journey`を使う。

## 0. プラグインrootを決める

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。

## 1. 工程を解決する

```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

このコマンドは必ず実行する。解決済みYAMLが空、依存が欠けている、設定が契約を外している場合は先へ進まない。

`${.instructions.execution.directive}`に従い、`${.playbook.steps}`を上から順に実行する。[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は順序・依存・入出力を決め、実行指示書は背景、前提、目的と各skillで意識することを補う。grillへJourney固有の観点を渡し、grill自身にその観点を持たせない。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。場面ごとに条件マトリクスを作り、`python3 "${PLUGIN_ROOT}/scripts/scenario_matrix.py" check --file <condition-matrix.json>`を通す。失敗場面の業務ルールが別資料にある場合は、`NOTE:`の`Source:`から外部正本の見出しを参照し、本文を複製しない。

各工程へ`--scope=${.resolution.scope_root}`を渡す。`exit 2`で止まったら後続へ進まない。

## 2. Journeyに該当するかを先に決める

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、grillで確認した決定だけを`grounded_input`にする。

`map-user-journey`を実行し、何がJourneyで何がJourneyでないかを判定する。ユーザーの目的、開始地点、最終地点、完了条件のどれかが分からなければ場面を書き始めない。目的ではなく機能利用が中心、意味のある場面が一つだけ、対象システム一つの責任だけを問う依頼ならJourneyへ広げず、非該当理由と適切な成果物を返して停止する。

## 3. 長さを削らず、場面へ分けて接続する

[Journeyの構造](references/journey-structure.md)と[場面のBDD](references/scenario-writing.md)を読む。

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

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" check --config "$CFG_FILE" --file <story-draft.md> --matrix <condition-matrix.json>
```

違反があれば資料化しない。通った`validated_journey_bdd`だけを`document_type=${.playbook.document_type}`、`output_format=${.playbook.output_format}`としてwrite-docへ渡し、`${.playbook.out_dir}`へ最初の正本を1本保存する。指定先に正本がすでにあれば上書きせず、formulationへ切り替える。

## 6. 報告する

- 作成したユーザー目的達成BDD正本の絶対パス
- ユーザーの目的、開始地点、最終地点、完了条件
- 目的達成までの場面数と主要な接続
- 未決の接続と、確認すべき人
- ユースケース、UX Journey map、domain、data model、実装、テスト実行へ送り返した事項
