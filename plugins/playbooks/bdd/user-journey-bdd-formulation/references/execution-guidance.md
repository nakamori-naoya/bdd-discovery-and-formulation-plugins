# User Journey BDD Formulation 実行指示書

## 背景と目的

このplaybookは、既存のユーザー目的達成BDDに対し、目的達成の連続性を壊す反例を当て、確認済みの理解と未決を同じ正本へ戻す。新規正本は作らない。

## 前提

- 入力はsymlinkではない既存の`user-journey-bdd`正本である。
- 利用者の発言、明示資料、確認済み決定だけを確定事項にする。
- Journeyである条件を満たさなくなった内容は無理に残さず、適切な正本へ返す。
- domain-ruleとdata modelは参照できるが、このplaybookから変更しない。
- テスト実行、環境、証拠収集は対象にしない。

## skillを実行するときの指示

### grill

既存正本と反証結果を示し、目的と完了の不一致、接続不能、分岐、中断再開、役割移譲から、答えで本文の変更が一つに決まる問いだけを一問ずつ聞く。

### map-user-journey

既存本文を既成事実として追認しない。何がJourneyで何がJourneyでないかを再判定し、別の正本が答える問いをJourneyから分離する。

### writing-rules

確認済み発見は該当する既存節へ戻し、未決は確認相手と影響場面を持たせる。別資料を新規作成しない。

### write-doc

`user-journey-bdd`の型を使い、入力正本と同じパスだけを`replace-existing-target`として更新する。
