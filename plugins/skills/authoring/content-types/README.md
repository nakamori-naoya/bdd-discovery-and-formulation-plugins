# content-types

BDDのドメイン理解とRDB論理データモデリングに必要な文書型だけを選び、その骨格を渡します。

## 公開する2型

| 型 | slug | 用途 |
|---|---|---|
| 業務知識・コアドメイン | `domain-rule` | 業務として何が正しいかと代表BDDを残す |
| RDB論理設計 | `rdb-logical-data-modeling` | CUDの業務シナリオ、記録する事実、論理構造を残す |

期間ダイジェスト、PR実装解説、一般的な技術文書、RDB物理設計の文書型は公開しません。

## 設定

```yaml
# <repo>/.harness-plugins/content-types.config.yml
version: 1
default_type: domain-rule
instructions:
  selection:
    directive: catalogの選び方を上から判定し、型を1つだけ選ぶ
```

設定は1ファイルで完結させます。テンプレートと記載例の対応は`assets/template-examples.yml`を正本とし、選んだ型の両方を執筆前に読みます。

## しないこと

- 文章を書かない
- 媒体の書式を決めない
- 2型以外を推測で追加しない
- テンプレートの見出し構成を勝手に変えない
