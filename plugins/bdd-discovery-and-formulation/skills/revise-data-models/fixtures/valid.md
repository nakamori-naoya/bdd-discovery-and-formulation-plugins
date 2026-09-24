# RDB論理設計 — 予約

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 正式な定義 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | なし | 更新あり | 予約の業務知識 |
| イベント系 | 業務 | `reservation_base_events` | イベント列 | `occurred_at`は予約に起きた出来事の成立時刻 | 追加のみ | 予約の業務知識 |
| イベント系 | 業務 | `reservation_cancelled_events` | イベント列 | なし（基底イベントの`occurred_at`） | 追加のみ | 予約取消の業務知識 |
| イベント系 | 技術 | `cancel_notice_requested_events` | イベント列 | `requested_at` | 追加のみ | 取消を知らせる要求 |

## 論理テーブル定義

### `reservations`（予約）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `reservation_id` | NOT NULL | 予約 |
| `state` | NOT NULL | 現在状態 |
| `current_version` | NOT NULL | 反映済みの最後の版 |

### `reservation_base_events`（予約に起きた出来事）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `event_id` | NOT NULL | イベント |
| `reservation_id` | NOT NULL | 対象予約 |
| `version` | NOT NULL | 予約の中での順序 |
| `occurred_at` | NOT NULL | 成立した時刻 |

### `reservation_cancelled_events`（予約取消）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `event_id` | NOT NULL | 基底イベント |
| `reason` | NOT NULL | 取消の理由 |

### `cancel_notice_requested_events`（取消の通知の要求）

| 論理列 | 必須性 | 意味 |
|---|---|---|
| `request_id` | NOT NULL | 要求 |
| `source_event_id` | NOT NULL | 起因の基底イベント |
| `requested_at` | NOT NULL | 要求が成立した時刻 |

## BDD
