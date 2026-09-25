# RDB論理設計 — 予約

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 保存表現 | 時刻 | 変化 | 根拠 |
|---|---|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | なし | 更新あり | 予約の業務知識 |

## 論理データモデル図

```mermaid
erDiagram
    reservations {
        uuid reservation_id PK "予約"
    }
    reservation_notes {
        uuid reservation_id FK "予約"
        text note "メモ"
    }
```

## 論理テーブル定義

### `reservations`（予約）

予約。

### `reservation_notes`（予約メモ）

予約のメモ。

## BDD
