# data-model-bdd-formulation

**既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新した後、指定RDB・バージョンの物理設計を作るplaybookです。** 物理設計は論理テーブル構造を変えません。データの永続化へ関心を絞り、API、DTO、ORM、画面、サービス分割は扱いません。

資料成果物は`output_format: markdown`に固定します。既存論理資料の同一パス更新もMarkdownだけを受け付け、物理設計もMarkdownで保存します。

最初に利用者の説明と既存論理資料を意味から評価し、代表的な永続化の共通理解がまだ無ければ`data-model-bdd-discovery`を案内して終了します。語の有無やscriptでは判定せず、定式化へ進める入力だけをQA反証と物理設計へ渡します。

## 工程

| # | 工程 | 完了条件 |
|---|---|---|
| 1 | 永続化の反証 | 既存論理資料のCUDシナリオを境界、状態、順序、重複、同時実行、権限、失敗時保証から深掘りした |
| 2 | 論理設計の更新 | 確認済みの理解とBDDを、新規資料ではなく入力された論理資料の同じパスへ戻した |
| 3 | RDB物理設計 | 典型Readを特定し、論理テーブル・列・業務制約を変えず、対象版の型、index、分離レベル、配置へ写した |

## 必要なもの

```bash
claude plugin install grill@harness-plugins
claude plugin install persistence-scenarios@harness-plugins
claude plugin install data-model@harness-plugins
claude plugin install write-doc@harness-plugins
claude plugin install rdb-design@harness-plugins
```

Codexでは`codex plugin add <plugin>@harness-plugins`を使います。

## 設定

同梱の`playbook.yml`が既定です。`<repo>/.harness-plugins/data-model-bdd-formulation.config.yml`を置くと丸ごと差し替わります。

```yaml
version: 1
name: data-model-bdd-formulation
output_format: markdown
database:
  product: PostgreSQL
  version: "18"
modeling:
  method: normalized
contract:
  persistence_operations: [create, update, delete]
  probe_dimensions: [同値分割, 境界値, 精度と単位, 条件組合せ, 状態遷移, イベント順序, 重複と再実行, 同時実行, アクターと権限, 悪用と不正, 時間, 規則変更と遡及, 失敗時保証, 不変条件]
  logical_schema_markers: [table, column, business_constraint]
  confidence: [confirmed, assumed, unknown]
requirements:
  existing_logical_document_required: true
  update_logical_in_place: true
  create_new_logical_document: false
  bdd_scenarios_in_logical_only: true
  logical_schema_immutable_in_physical: true
  read_scenarios_in_physical_only: true
  rdb_only: true
  verified_features_only: true
out_dir: design/data-modeling
steps: [...]  # 上書き時はrequires、instructionsを含む完全な設定にする
```

`database.product`と`database.version`がRDB設計工程へ渡され、その組み合わせで裏付けられた機能だけを使います。既定はreservationで使っているPostgreSQL 18です。

## 成果物

- 同じパスで更新された、BDDシナリオを含むRDB論理データモデル
- RDB機能根拠台帳と、論理構造を変えないRDB物理設計
- indexの根拠となる典型Readと、複合indexの列順の理由
- 論理設計で必要とした同時実行上の保証と、物理設計で選択した分離レベル

論理設計テンプレートは`data-model`、物理設計テンプレートは`rdb-design`に同梱されています。
