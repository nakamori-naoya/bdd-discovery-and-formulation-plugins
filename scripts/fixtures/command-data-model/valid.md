# 予約のコマンドデータモデル

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 保存表現 | 根拠 |
|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | 予約の業務知識 |
| イベント系 | 業務 | `reservation_base_events` | イベント列 | 予約の業務知識 |
| イベント系 | 業務 | `reservation_cancelled_events` | イベント列 | 予約取消の業務知識 |
| イベント系 | 技術 | `cancel_notice_requested_events` | イベント列 | 取消を知らせる要求 |
| イベント系 | 技術 | `cancel_notice_claimed_events` | イベント列 | 取消を知らせる要求 |
| イベント系 | 技術 | `cancel_notice_succeeded_events` | イベント列 | 取消を知らせる要求 |

## データモデル図

```mermaid
erDiagram
    reservations {
        uuid reservation_id PK "予約"
        text room_code "会議室"
        date use_on "業務が与えた値。利用日"
        text status "いまの状態"
        bigint current_version "反映済みの最後の版"
    }
    reservation_base_events {
        uuid event_id PK "イベント"
        uuid reservation_id FK "対象予約"
        text event_type "種類"
        bigint version "予約の中の順序"
        timestamptz occurred_at "起きた時点"
    }
    reservation_cancelled_events {
        uuid event_id PK, FK "基底イベント"
        text reason "取消の理由"
    }
    cancel_notice_requested_events {
        uuid request_id PK "要求"
        uuid source_event_id FK "起因の基底イベント"
        timestamptz occurred_at "要求した時点"
    }
    cancel_notice_claimed_events {
        uuid claim_id PK "回収"
        uuid request_id FK "要求"
        bigint version "要求の中の回収の順序"
        text worker_id "引き受けた担い手"
        timestamptz occurred_at "回収した時点"
    }
    cancel_notice_succeeded_events {
        uuid request_id PK, FK "要求"
        uuid claim_id FK "終えた回収"
        timestamptz occurred_at "終えた時点"
    }
    reservations ||--|{ reservation_base_events : "起きたこと"
    reservation_base_events ||--o| reservation_cancelled_events : "取消の事実"
```

## テーブル定義

### `reservations`（予約）

予約を見分ける識別子と、予約したときに決まる会議室と利用日。

### `reservation_base_events`（予約に起きたこと）

予約に起きた出来事に共通する事実。

### `reservation_cancelled_events`（予約取消）

取消に固有の事実。

### `cancel_notice_requested_events`（取消の通知の要求）

取消を知らせる要求。

### `cancel_notice_claimed_events`（取消の通知の回収）

担い手が要求を引き受けた事実。

### `cancel_notice_succeeded_events`（取消の通知の成功）

知らせ終えた事実。

## BDD

## 業務知識のBDDとの対応

| 業務知識のBDD | この資料のBDD |
|---|---|
| BDD-001 | 対象外 |
| BDD-002 | クエリデータモデル |

BDD-001 は保存の前に拒まれて記録に届かない。
