# user-journey-bdd-discovery

1人の主たるユーザーが1つの目的を達成するまでを発見し、複数の場面を接続したユーザー目的達成BDDの正本として初めて作る。

## 責務

- ユーザーの目的、開始地点、最終地点、完了条件を確定する
- 目的達成までの場面を順番に並べる
- 前の場面の結果と次の場面の前提を接続する
- 各場面をGiven / When / Thenで記述する
- 既知の分岐と未決を残す

既存正本の深化、domain-ruleの発見、data modelの設計、画面やAPIの操作手順、テストの実行環境は扱わない。

## 依存

- 同じpackage内の`user-journey`
- `grill@grill`
- `write-doc@write-doc`

別repositoryには公開playbook packageだけで依存し、その内部機能名へは依存しない。versionは固定しない。

## 設定

同梱の`playbook.yml`が既定である。repositoryでは`<repo>/.harness-plugins/user-journey-bdd-discovery.config.yml`を置くと、同梱設定を丸ごと差し替える。

出力型は`user-journey-bdd`、媒体はMarkdown、既定の保存先は`bdd/user-journey`である。
