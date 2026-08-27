# e2e-bdd-documentation

ユーザーが目的を持って開始地点から最終地点へ到達するまでを、複数のインタラクション場面が連なるBDDストーリーとして1本のMarkdown資料にする。

## 責務

- ユーザーの目的、開始地点、最終地点、完了条件を確定する
- 目的達成までの場面を順番に並べる
- 前の場面の結果と次の場面の前提を接続する
- 各場面をGiven / When / Thenで記述する
- 既知の分岐と未決を残す

domain-ruleの発見、data modelの設計、画面やAPIの操作手順、E2Eテストの実行環境は扱わない。

## 外部依存

- `grill@grill`
- `writing-rules@write-doc`
- `write-doc@write-doc`

依存はmarketplace名とplugin名で解決し、versionを固定しない。

## 設定

同梱の`playbook.yml`が既定である。repositoryでは`<repo>/.harness-plugins/e2e-bdd-documentation.config.yml`を置くと、同梱設定を丸ごと差し替える。

出力型は`e2e-bdd-scenarios`、媒体はMarkdown、既定の保存先は`bdd/e2e`である。
