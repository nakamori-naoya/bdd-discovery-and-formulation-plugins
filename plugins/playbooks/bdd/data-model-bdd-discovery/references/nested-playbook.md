# 入れ子の段取りを呼ぶ

`playbook:` の工程は、別の配布物が公開した段取りである。呼び出し元が扱うのは公開入口、入力、出力だけであり、相手の内部の工程や実装は参照しない。

## 公開入口を使う

依存解決で得た `${.deps.<論理名>.entry}` が入口の `SKILL.md` の絶対パスである。この入口を読み、対応する公開契約に従って呼ぶ。依存先の内部 skill、参考資料、設定、保存処理を探さない。

両方とも公開入口へ契約入力を直接渡し、相手の設定を解決しない。`grill` の版1は入力YAMLと結果YAMLを使えるが、`write-doc` の版2は直接入力・直接結果だけを使う。両者の入出力を混用しない。

## grill（契約 `grill/grill` 版1）

契約入力をYAMLに保存し、その通常ファイルの絶対パスを `${.deps.grill.entry}` へ直接渡す。入力objectを直接渡してもよい。相手の設定解決や解決済みYAMLの引き渡しは行わず、`scope` と `bindings` も入力へ加えない。

```bash
NESTED_INPUT=$(mktemp "${TMPDIR:-/tmp}/nested-input.XXXXXX") || exit 2
NESTED_OUTPUT=$(mktemp "${TMPDIR:-/tmp}/nested-output.XXXXXX") || exit 2
# NESTED_INPUT へ grill の契約入力を書く（output_to は "$NESTED_OUTPUT"）
# NESTED_INPUT の絶対パスを公開入口へ直接渡す
```

公開入口の対話に従い、利用者の回答と、決定・未決の一覧および対話終了への明示合意を待つ。呼び出し元が回答や合意を代行しない。回答待ちを成功や失敗へ変換しない。

### 渡す入力

- `contract: grill/grill` と `version: 1`
- `topic`：確認したい題材
- `context`：`purpose`、`audience`、`boundary`
- `questions`：`{id, question, recommendation}` の配列。問いを相手に立ててもらう場合は空配列
- `grounding`：任意の根拠資料の絶対パス配列
- `output_to`：結果を書き出す絶対パス

題材固有の観点は `context` と `questions` で渡す。空の `questions` は確認を省略する指示ではない。

### 受け取る結果

`NESTED_OUTPUT` を読み、`status: completed` の場合だけ続ける。結果は `decisions`（`{id, question, answer, rationale}`）と `open_questions`（`{id, question, state, reason}`）である。未決の `state` は `open` または `withdrawn`。この結果から根拠づけられた入力を作るのは、呼び出し元の `ground` 工程である。

## write-doc（契約 `write-doc/write-doc` 版2）

呼ぶ直前に、自分の入口に同梱した依存検査を実行する。`yq -o=json '.' "$CFG_FILE" | python3 "${PLUGIN_ROOT}/scripts/resolve-dependency.py" --check-steps <資料保存の工程id>` が失敗したら呼ばない。これにより、解決後の依存の変更や契約不一致を検出する。

`${.deps.write-doc.entry}` を読み、次の入力を直接渡して Markdown 資料を1本保存する。契約IDと版は依存の識別情報であり、執筆入力へ加えない。入力YAML、解決済みYAML、出力YAMLは作らず、設定解決scriptや `output_to` は使わない。`scope`、`bindings`、`output_format` も入力に含めない。

### 素材と文書型を渡す

`material` は1要素以上の配列とし、各要素を次のどちらかで渡す。

- ファイル素材：`{kind: file, path: /absolute/path/to/material.md}`
- 本文素材：`{kind: text, content: "根拠となる本文"}`

BDD工程で束ねた素材ファイルは `kind: file` を使う。絶対パス文字列だけの配列にしない。`document_type` にはこの工程で決めた型を渡し、`references` には追加で従う自分の資料の読み取り可能な絶対パスだけを渡す。相手の内部文書は参照しない。

### 保存先を明示する

新規作成では `output_directory` と `name` の両方を渡す。保存先ディレクトリは自分の設定から絶対パスへ解決し、`name` はパス要素を含まない `.md` ファイル名とする。保存先が不明なら利用者へ確認し、推測や相手の既定値で補わない。同名ファイルがあれば上書きしない。

既存正本の更新では、同一パス検査で得た `update_target` だけを渡す。新規用の `output_directory` と `name` は渡さない。更新先は既存の Markdown ファイルである。

### 直接返された結果を工程成果へ対応させる

成功時は `status: completed` と `path`、失敗時は `status: failed` と `reason` が直接返る。`completed` と、保存済み Markdown の絶対パスを確認した場合だけ、`path` を自分の資料成果物名へ対応させる。新規の場合は指定した `output_directory` と `name` による保存先、更新の場合は `update_target` と `path` が一致することも確認する。

失敗、結果欠落、不正なパス、保存先不一致の場合は理由を報告し、後続の設計や中間素材の削除へ進まない。文書型や媒体が出力に戻ることを前提にしない。
