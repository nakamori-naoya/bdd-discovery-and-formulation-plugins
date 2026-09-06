# 入れ子の段取りを呼ぶ

`playbook:` の工程は、別の配布物が公開した段取りである。**公開されているのは段取り1枚だけで、その中の作りは公開面ではない。**

## 見てよいもの

外部依存の参照形は次の**2形だけ**である。

| # | 参照 | 使い道 |
|---|---|---|
| 1 | `${.deps.<論理名>.root}` | 直下の `playbook.yml` / `scripts/prepare.sh` / `scripts/resolve.sh` の3つだけを組み立ててよい |
| 2 | `${.deps.<論理名>.entry}` | **入口のSKILL.mdの絶対path**。実行手順はここに従う |

**これ以外は見ない。** `root` 配下のその他のscript、参考資料、設定、下段の部品、工程の呼び名、保存の呼び名、引数、exit codeは、いつ変わってもよい相手の事情である。名前で掴んだ瞬間に、その相手は差し替えられなくなる。

次の形は resolver と lint が拒否する。

- `${.deps.<論理名>.skills.<名前>}`（相手の公開skill一覧を引く形）
- `${.deps["<論理名>"]...}`（ブラケット形）
- `${.deps.<論理名>.root}/..` を含むpath、上の3つ以外のroot配下path
- `${<論理名>:.<key>}`（相手の解決済みYAMLをプロパティで読む形）

## 呼び方 — 解決はこちら、実行は相手

呼び出しは**2段**である。**解決するのは呼び出し元で、相手は解決をやり直さない。**

**1段目: 入力を書いて、こちらが解決する。**

```bash
NESTED_INPUT=$(mktemp "${TMPDIR:-/tmp}/nested-input.XXXXXX") || exit 2
NESTED_OUTPUT=$(mktemp "${TMPDIR:-/tmp}/nested-output.XXXXXX") || exit 2
# NESTED_INPUT へ契約の入力を書く（output_to は "$NESTED_OUTPUT"）
NESTED_CFG=$(bash "${.deps.<論理名>.root}/scripts/prepare.sh" "$(pwd)" \
  --input="$NESTED_INPUT" --scope="${.resolution.scope_root}" --bindings="${.resolution.bindings_lock}") || exit 2
```

`--scope` と `--bindings` は、入口が決めたものをそのまま流す。**自分の名前で作り直さない。** 出力が空なら先へ進まない。

**2段目: 得た解決済みYAMLのpathを渡して、相手のSKILL.mdに従って実行する。**

`${.deps.<論理名>.entry}` のSKILL.mdを読み、そこに書かれた手順を `NESTED_CFG` を `CFG_FILE` として実行する。**相手に `prepare.sh` を実行し直させない。** 解決は1段目で済んでおり、やり直すと入力も束縛も落ちる。

**3段目は無い。** 完了したら `"$NESTED_OUTPUT"` を読む。`status` が `completed` でなければ先へ進まない。劣化した結果で続けない。

実行設定の後始末は相手が自分で行う。こちらから相手のscriptを実行しない。

## grill（契約 `grill/grill` 版1）

| 向き | キー |
|---|---|
| 入力 | `contract`（`grill/grill`）、`version`（`1`）、`topic`、`context`（`purpose` / `audience` / `boundary`）、`questions`（`{id, question, recommendation}` の配列。空配列でもよい）、`grounding`（任意。絶対pathの配列）、`output_to` |
| 出力 | `status`、`decisions`（`{id, question, answer, rationale}`）、`open_questions`（`{id, question, state, reason}`。`state` は `open` または `withdrawn`） |

**題材固有の観点は `context` と `questions` で渡す。** 相手に業務の観点を持たせない。`topic` は日本語のままでよい。

`questions` の空配列は「問いはこちらで立ててよい」であって「問わなくてよい」ではない。

**「根拠づけられた入力」は相手の出力ではない。** `decisions` と `open_questions` から、こちらの `ground` 工程が作る。

## write-doc（契約 `write-doc/write-doc` 版1）

| 向き | キー |
|---|---|
| 入力 | `contract`（`write-doc/write-doc`）、`version`（`1`）、`document_type`（型slug）、`material`（**絶対pathの配列**。1つ以上、それぞれregular file）、`output_format`（`markdown` / `html`）、新規なら `name`（保存先directoryを明示するときだけ `output_directory` も添える）、差し替えなら `update_target`、`references`（任意。**自分の配布物の文書だけ**）、`output_to` |
| 出力 | `status`、`path`（保存した資料1本の絶対path）、`document_type`、`output_format`。`failed` のときは `path` を持たず `reason` を持つ |

- **未知のキーを書くと止まる。** 上の表に無いキーを足さない。
- `material` は配列である。1本のファイルでも配列で渡す。
- `name` と `update_target` は**排他**である。両方渡しても、どちらも渡さなくても止まる。
- `output_directory` は任意である。渡すなら `name` も要る（`output_directory` だけでは止まる）。省けば保存先は利用者の設定が決める。
- `document_type` を渡したら、相手は型を選び直さない。
- `references` に相手の配布物内のpathを渡すと止まる。渡してよいのは自分の配布物の文書だけである。
- 1回の呼び出しで作る資料は**1本だけ**である。複数本が要るなら複数回呼ぶ。
- 保存先を相手の設定ファイルから作り直させない。差し替えなら `update_target`、新規なら `name` を渡す。`output_directory` を添えるのは**依頼で保存先directoryが明示されたとき**か、こちらの設定が保存先を持つときだけで、明示が無ければ省いて利用者の設定に委ねる。依頼に無いpathを推測して渡さない。
