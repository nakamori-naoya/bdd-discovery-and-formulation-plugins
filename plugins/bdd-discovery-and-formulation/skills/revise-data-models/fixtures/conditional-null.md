# RDB論理設計 — 設定

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 正式な定義 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| リソース系 | 業務 | `settings` | 現在状態 | `created_at` | 更新あり | 設定の業務知識 |

## 論理テーブル定義

### `settings`（設定）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `setting_id` | NOT NULL | 設定 |
| `status` | NOT NULL | 現在状態 |
| `completed_at` | NULL可 | 完了日時 |
| `is_deleted` | NOT NULL | 削除表示 |
| `optional_value` | 種類Aの場合に必要、その他はNULL | 条件付き値 |
| `created_at` | NOT NULL | 成立日時 |

## BDD
