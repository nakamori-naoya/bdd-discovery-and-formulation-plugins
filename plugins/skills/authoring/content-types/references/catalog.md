# BDD資料のコンテンツタイプ

## 選び方

1. 読み手が、作りを変えても残る業務上の正しさと代表BDDを確定したいなら`domain-rule`を選ぶ。
2. 読み手が、CUDの業務シナリオからRDBへ記録する事実と論理構造を決めたいなら`rdb-logical-data-modeling`を選ぶ。
3. どちらにも当てはまらない場合は、別の型を推測せず対象外として停止する。

## 一覧

| 型 | slug | 読み手 | 目的 | 詳細 |
|---|---|---|---|---|
| 業務知識・コアドメイン | `domain-rule` | 業務を知る人と、それを形にする人 | 業務として何が正しいかを確定する | [detail/domain.md](detail/domain.md) |
| RDB論理設計 | `rdb-logical-data-modeling` | 業務を知る人と、RDBへデータを永続化する人 | CUDの業務シナリオから記録する事実と論理構造を決める | [detail/data-modeling.md](detail/data-modeling.md) |

## 混ぜない

- `domain-rule`へ画面、保存方式、API、DB構造を入れない。
- `rdb-logical-data-modeling`へ物理型、索引、分離レベル、DDLを入れない。
- 未決を空欄や推測で補わず、未決のまま示す。
