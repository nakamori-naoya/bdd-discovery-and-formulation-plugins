# 入れ子の段取りを呼ぶ

`playbook:`の工程は、別のpackageが公開した段取りである。呼び出し元が扱うのは公開入口、入力、出力だけであり、相手の内部の工程や実装は参照しない。

## 公開入口を使う

同じagentの利用可能Skill一覧から、`playbook.yml`の`requires`に宣言された`{plugin, marketplace}`と一致する公開Skill名を選び、その公開契約に従って呼ぶ。`grill`は`grill:grill`、`write-doc`は`write-doc:write-doc`である。契約IDと版が異なる、または必要な公開Skillが無い場合は呼ばずに停止する。

両方とも公開入口へ契約入力objectを直接渡し、公開結果objectを直接受け取る。

## grill（契約 `grill/grill` 版1）

対話の作法（問う数の上限、提示の仕方、終え方）はgrillの公開契約に従う。呼び出し元は問いの選定と結果の扱いだけを担い、回答待ちを成功や失敗へ変換しない。

### 渡す入力

- `contract: grill/grill` と `version: 1`
- `topic`：確認したい題材
- `context`：`purpose`、`audience`、`boundary`
- `questions`：`{id, question, recommendation}` の配列。調べれば分かる論点を除き、成果を左右する順に並べて渡す。上限で問われなかった問いは推奨付きの`open_questions`として返るので、渡す前に数を切り詰めない。問いを相手に立ててもらう場合は空配列
- `references`：追加で従う資料の絶対パス配列。入口の`references`入力をそのまま渡す

題材固有の観点は `context` と `questions` で渡す。空の `questions` は確認を省略する指示ではない。2回目の呼び出しは、利用者が求めた場合か、決定なしでは成果物を完成できない場合だけ行う。

### 受け取る結果

直接返された結果objectを読み、`status: completed` の場合だけ続ける。`decisions` と `open_questions` はキーが存在する配列でなければならず、欠落、`null`、別の型は公開契約に反する結果として止まる。合法な空配列はそのまま受け入れる。`decisions` の各要素は `{id, question, answer, rationale}`、`open_questions` の各要素は `{id, question, state, reason}` を持ち、未決の `state` は `open` または `withdrawn` である。同じagentがこれらを利用者入力・明示資料と突き合わせて根拠づけられた入力を確定し、`open` の未決は `reason` に書かれた推奨を仮置きし、成果物のドラフトの該当箇所と未決の節へ仮説と分かる形で反映する。

## write-doc（契約 `write-doc/write-doc` 版2）

公開Skill `write-doc:write-doc`へ次の入力を直接渡してMarkdown資料を1本保存する。契約IDと版は依存の識別情報であり、執筆入力へ加えない。

### 素材と文書型を渡す

`material` は1要素以上の配列とし、各要素を次のどちらかで渡す。

- ファイル素材：`{kind: file, path: /absolute/path/to/material.md}`
- 本文素材：`{kind: text, content: "根拠となる本文"}`

同じagentが組み立てた本文は `kind: text` で直接渡す。実在する素材ファイルを渡す場合だけ `kind: file` を使う。`document_type` にはこの工程で決めた型を渡し、`references` には入口の `references` 入力をそのまま渡し、成果物の形など自分の資料を足す入口はそれを連結する（空なら空配列）。

### 保存先を明示する

新規作成では `output_directory` と `name` の両方を渡す。`output_directory` は既存の書き込み可能な絶対directory、`name` はパス要素を含まない `.md` ファイル名とする。日本語名を許す。保存先が不明なら利用者へ確認し、推測や相手の既定値で補わない。同名ファイルがあれば上書きしない。

既存正本の更新では、同一パス検査で得た `update_target` だけを渡す。新規用の `output_directory` と `name` は渡さない。更新先は既存の Markdown ファイルである。

### 直接返された結果を工程成果へ対応させる

成功時は `status: completed` と `path`、失敗時は `status: failed` と `reason` が直接返る。`completed` と、保存済み Markdown の絶対パスを確認した場合だけ、`path` を自分の資料成果物名へ対応させる。新規の場合は指定した `output_directory` と `name` による保存先、更新の場合は `update_target` と `path` が一致することも確認する。

失敗、結果欠落、不正なパス、保存先不一致の場合は理由を報告し、後続の工程へ進まない。
