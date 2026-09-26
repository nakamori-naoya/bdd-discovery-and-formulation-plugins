# 予約のコマンドデータモデル

## リソース系とイベント系

| 系列 | 性質 | 論理テーブル | 保存表現 | 根拠 |
|---|---|---|---|---|
| リソース系 | 業務 | `reservations` | 現在状態 | 予約の業務知識 |

## データモデル図

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

## テーブル定義

### `reservations`（予約）

予約。

### `reservation_notes`（予約メモ）

予約のメモ。

## BDD

## 業務知識のBDDとの対応

| 業務知識のBDD | この資料のBDD |
|---|---|
| BDD-001 | 対象外 |
| BDD-002 | クエリデータモデル |

BDD-001 は保存の前に拒まれて記録に届かない。
