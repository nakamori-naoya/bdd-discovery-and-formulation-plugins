# user-journey-bdd-formulation

既存のユーザー目的達成BDDを、目的、両端、場面接続、分岐、中断再開、役割移譲、完了の観測可能性から反証し、確認済みの理解と未決を同じ正本へ戻す。

## 前提

入力には既存の`user-journey-bdd`正本が必要である。新しい資料を作る依頼には`user-journey-bdd-discovery`を使う。

## 更新しないもの

ユースケース、UX Journey map、domain-rule、data model、UIフロー、テスト実行仕様は変更しない。不足が見つかった場合は、正本と確認相手を示した未決として返す。

## 外部依存

- `user-journey@bdd-discovery-and-formulation`
- `grill@grill`
- `writing-rules@write-doc`
- `write-doc@write-doc`
- `write-doc-cleanup@write-doc`

依存はmarketplace名とplugin名で解決し、versionを固定しない。
