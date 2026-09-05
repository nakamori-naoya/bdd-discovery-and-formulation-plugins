# user-journey-bdd-formulation

既存のユーザー目的達成BDDを、目的、両端、場面接続、分岐、中断再開、役割移譲、完了の観測可能性から反証し、確認済みの理解と未決を同じ正本へ戻す。

## 前提

入力には既存の`user-journey-bdd`正本が必要である。新しい資料を作る依頼には`user-journey-bdd-discovery`を使う。

## 更新しないもの

ユースケース、UX Journey map、domain-rule、data model、UIフロー、テスト実行仕様は変更しない。不足が見つかった場合は、正本と確認相手を示した未決として返す。

## 依存

- 同じpackage内の`user-journey`
- `grill@grill`
- `write-doc@write-doc`

別repositoryには公開playbook packageだけで依存し、その内部機能名へは依存しない。versionは固定しない。
