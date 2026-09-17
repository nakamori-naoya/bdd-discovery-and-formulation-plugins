# RDB論理設計 — 予約

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 正本 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | `created_at` | 更新あり | 予約の業務知識 |

## 論理テーブル定義

### `reservations`（予約）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `reservation_id` | NOT NULL | 予約 |
| `created_at` | NOT NULL | 成立日時 |

### `reservation_notes`（予約メモ）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `reservation_id` | NOT NULL | 予約 |
| `created_at` | NOT NULL | 成立日時 |

## BDD

