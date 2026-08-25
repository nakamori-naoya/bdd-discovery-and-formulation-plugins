# rdb-design

**論理データモデルを変えずに、対象RDBの物理設計へ写す。** 論理テーブル定義は物理資料へ複製せず、物理制約、型、index、分離レベル、パーティション、容量・性能・運用を扱い、その版で利用可能と確認した機能だけを採用します。

## 成果物

| 出力 | 中身 |
|---|---|
| `<design_dir>/<題材>.capabilities.jsonl` | 採用するRDB機能、対応版、公式資料または実機確認、採用理由 |
| `<design_dir>/<題材>.md` | 代表的なReadを根拠に、論理構造を重複させずに書く物理制約、型、index、分離レベル、配置、容量・性能・運用の設計 |

`rdb.py fingerprint`は論理モデルのテーブル・列・業務制約から指紋を作ります。`rdb.py check`は、対象製品・版、必要な見出し、現在の論理構造と記録済み指紋、論理制約の物理的な扱い、Read・index・分離性の必須項目、採用機能の根拠を突き合わせます。BDDや論理定義を物理資料へ複製した場合も落とします。

物理設計には`assets/physical-design.md`を使います。論理テーブル設計に変更が必要なら、物理資料で直さず論理設計へ戻します。

## 設定

`<repo>/.harness-plugins/rdb-design.config.yml`が無ければpersonal、それも無ければ同梱既定を使います。設定層は混ぜません。

```yaml
version: 1
design_dir: design/data-modeling
prompt_parameters:
  database:
    product: {type: string, required: true}
    version: {type: string, required: true}
instructions:
  design:
    directive: 論理構造を複製せず、対象バージョンで裏付けた物理制約・型・index・分離レベル・配置へ写す
```

単体利用では対象製品・版をprompt overrideとして必ず渡します。data-modeling playbookから呼ぶ場合は、playbookの`database.product`と`database.version`が渡されます。

## しないこと

- API、DTO、ORM、画面、サービス境界を設計すること
- 対象版で裏付けられないRDB機能を採用すること
- BDDシナリオや業務シナリオを再掲すること
- 論理テーブル、列、業務制約を増減・再編すること
- マイグレーションを適用すること
