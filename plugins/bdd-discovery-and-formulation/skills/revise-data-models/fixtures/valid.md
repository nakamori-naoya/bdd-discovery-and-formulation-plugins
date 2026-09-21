# RDB論理設計 — 予約

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 正式な定義 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | `created_at`は予約の成立時刻 | 更新あり | 予約の業務知識 |
| イベント系 | 業務 | `reservation_cancelled_events` | イベント列 | `occurred_at`は取消の成立時刻 | 追加のみ | 予約取消の業務知識 |

## 論理テーブル定義

### `reservations`（予約）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `reservation_id` | NOT NULL | 予約 |
| `state` | NOT NULL | 現在状態 |
| `created_at` | NOT NULL | 予約の成立時刻 |

### `reservation_cancelled_events`（予約取消）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `event_id` | NOT NULL | 取消イベント |
| `reservation_id` | NOT NULL | 対象予約 |
| `occurred_at` | NOT NULL | 取消が成立した時刻 |

## BDD

