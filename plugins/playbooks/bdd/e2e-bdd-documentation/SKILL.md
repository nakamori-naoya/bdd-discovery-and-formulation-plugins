---
name: document-e2e-scenarios
description: ユーザーがある目的を持って開始地点から最終地点へ到達するまでを、複数のインタラクション場面が連なるBDDストーリーとして1本の資料にする。「E2EシナリオをBDDで書いて」「目的達成までの長い振る舞いを資料にして」と言われたときに使う。ドメインルール、データモデル、E2Eテスト環境は設計しない。
---

# E2Eの目的達成ストーリーをBDD資料にする

**中心に置くのはユーザーの目的である。** 開始地点から最終地点までを一続きに読み、途中のインタラクションが目的達成へどうつながるかを説明できる資料を作る。

これは短いドメインBDDを長く引き伸ばすskillではない。ドメインルールを発見せず、データの残し方も決めず、E2Eテストの実行方法も扱わない。

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

`${.instructions.execution.directive}`に従い、`${.playbook.steps}`を上から順に実行する。[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は順序・依存・入出力を決め、実行指示書は背景、前提、目的と各skillで意識することを補う。grillへE2E固有の観点を渡し、grill自身にその観点を持たせない。

各工程へ`--scope=${.resolution.scope_root}`を渡す。`exit 2`で止まったら後続へ進まない。

## 2. 目的と両端を先に決める

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、grillで確認した決定だけを`grounded_input`にする。

最初に`${.playbook.contract.story_frame}`を確かめる。ユーザーの目的、開始地点、最終地点、完了条件のどれかが分からなければ、場面を書き始めない。1本の資料へ複数の目的を詰め込まず、目的が違うなら資料を分ける。

## 3. 長さを削らず、場面へ分けて接続する

[E2Eストーリーの構造](references/story-structure.md)と[場面のBDD](references/scenario-writing.md)を読む。

E2Eシナリオ全体にstep数の上限を置かない。目的達成までに必要なインタラクションは省略しない。その代わり、全体を複数の場面へ分け、各場面で次を明らかにする。

```text
前の場面から受け取った状態
→ その場面で行う役割と働きかけ
→ 観測できる応答
→ 次の場面へ渡す状態
```

各場面は1組のGiven / When / Thenを中心に書く。ストーリー全体には複数のWhen / Thenがあってよい。前の場面の結果と次の場面の前提がつながらない場合は、間を推測で埋めず未決にする。

## 4. 責務を越えない

既存のdomain-ruleやdata model資料は入力根拠として読めるが、変更しない。新しい業務ルールを確定したり、保存する事実や構造を設計したりしない。そこに不足が見つかった場合は未決として残し、対応するdomainまたはdata modelのpluginへ送る。

画面、ボタン、URL、API、endpoint、request、response、DB、tableなど、実現方法の手順へ落とさない。test runner、実行環境、試行回数、証拠、CI、flakyなど、E2Eテスト環境の関心も書かない。

## 5. 検査して資料化する

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" check --config "$CFG_FILE" --file <story-draft.md>
```

違反があれば資料化しない。通った`validated_story`だけを`document_type=${.playbook.document_type}`、`output_format=${.playbook.output_format}`としてwrite-docへ渡し、`${.playbook.out_dir}`へ1本保存する。

## 6. 報告する

- 作成したE2E BDD資料の絶対パス
- ユーザーの目的、開始地点、最終地点、完了条件
- 目的達成までの場面数と主要な接続
- 未決の接続と、確認すべき人
- domain、data model、実装、E2Eテスト環境へ送り返した事項
