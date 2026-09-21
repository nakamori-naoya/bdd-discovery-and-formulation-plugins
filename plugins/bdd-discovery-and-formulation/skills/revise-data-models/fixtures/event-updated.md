# RDB論理設計 — 予約

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 正式な定義 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| イベント系 | 業務 | `reservation_events` | イベント列 | `occurred_at` | 更新あり | 予約の業務知識 |

## 論理テーブル定義

### `reservation_events`（予約イベント）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `event_id` | NOT NULL | イベント |
| `status` | NOT NULL | 現在の状態 |
| `completed_at` | NOT NULL | 完了日時 |
| `occurred_at` | NOT NULL | 発生日時 |

## BDD

