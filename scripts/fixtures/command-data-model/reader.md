# 入室のコマンドデータモデル

## 残す事実

| 系列 | 性質 | 論理テーブル | 保存表現 | 根拠 |
|---|---|---|---|---|
| リソース系 | 業務 | `entries` | 現在状態 | 入室の業務知識 |
| イベント系 | 業務 | `entry_base_events` | イベント列 | 入室の業務知識 |

## 読むだけのテーブル

| 参照するテーブル | 読む列 | 持ち主の資料 |
|---|---|---|
| `reservations` | `reservation_id`、`status` | [予約のコマンドデータモデル](valid.md) |

## 関係

| 関係元 | 関係先 | 多重度 | 意味 |
|---|---|---|---|
| `entries` | `entry_base_events` | 1対1以上 | 起きたこと |
| `reservations` | `entries` | 1対0以上 | 予約した部屋へ入る |

## 定義

### `entries`（入室）

予約した部屋へ入ったこと。

| 列 | 型 | キー | 意味 |
|---|---|---|---|
| `entry_id` | uuid | PK | 入室 |
| `reservation_id` | uuid | FK | 予約 |
| `status` | text |  | いまの状態 |
| `current_version` | bigint |  | 反映済みの最後の版 |

### `entry_base_events`（入室に起きたこと）

入室に起きた出来事に共通する事実。

| 列 | 型 | キー | 意味 |
|---|---|---|---|
| `event_id` | uuid | PK | イベント |
| `entry_id` | uuid | FK | 対象の入室 |
| `event_type` | text |  | 種類 |
| `version` | bigint |  | 入室の中の順序 |
| `occurred_at` | timestamptz |  | 起きた時点 |

## 業務知識のBDDとの対応

| 業務知識のBDD | この資料のBDD |
|---|---|
| BDD-001 | 対象外 |
| BDD-002 | クエリデータモデル |

BDD-001 は保存の前に拒まれて記録に届かない。
