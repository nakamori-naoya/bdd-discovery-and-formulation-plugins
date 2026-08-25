# persistence-scenarios

**データモデリングより先に、永続化に関係する業務シナリオを書く。** 業務イベントと事前状態から、作成・更新・削除で何を残し、何を履歴として保ち、いつ物理削除できるかを明らかにします。

## 成果物

| 出力 | 中身 |
|---|---|
| `<scenario_dir>/<題材>.persistence.jsonl` | 永続化シナリオと作成・更新・削除の検討状況 |
| `<scenario_dir>/<題材>.md` | アクター、事前状態、業務イベント、判断、残す事実、履歴、保持を読む資料 |

`check`は、作成・更新・削除がすべて`covered`または理由つき`not-applicable`であること、`covered`の操作にシナリオがあること、未確認のシナリオが残っていないことを検査します。

## 設定

`<repo>/.harness-plugins/persistence-scenarios.config.yml`が無ければpersonal、それも無ければ同梱既定を使います。設定層は混ぜません。

```yaml
version: 1
scenario_dir: domain/persistence-scenarios
instructions:
  discovery:
    directive: 業務イベントと事前状態から、作成・更新・削除で残す事実、履歴、保持の必要をシナリオとして先に記録する
```

## しないこと

- データモデル、テーブル、DDLを設計すること
- API、DTO、ORM、メッセージ形式を決めること
- 業務資料に無い判断を推測で確定すること
