# 予約の一覧のクエリデータモデル

会議室の担当者が、ある日の予約を会議室の順に見られることを、予約のコマンドデータモデルの行だけで確かめる。

## 読むテーブル

| 読むテーブル | 持ち主の資料 |
|---|---|
| `reservations` | [予約のコマンドデータモデル](../command-data-model/valid.md) |

## BDD

### [BDD-001] その日の予約だけが会議室の順に並ぶ

```gherkin
Given: 2026年10月1日の予約が二件、10月2日の予約が一件ある
When: 担当者が2026年10月1日の予約の一覧を見る
Then: 10月1日の二件が会議室の順に返る
```

**Before**

**`reservations`**

| reservation_id | room_code | use_on | status |
|---|---|---|---|
| R-1 | B | 2026-10-01 | reserved |
| R-2 | A | 2026-10-01 | reserved |
| R-3 | A | 2026-10-02 | reserved |

**取得結果**

| 会議室 | 予約 |
|---|---|
| A | R-2 |
| B | R-1 |

### [BDD-002] 予約の無い日は何も返らない

```gherkin
Given: 2026年10月3日の予約は無い
When: 担当者が2026年10月3日の予約の一覧を見る
Then: 何も返らない
```

**Before**

**`reservations`**

| reservation_id | room_code | use_on | status |
|---|---|---|---|
| R-3 | A | 2026-10-02 | reserved |

**取得結果**

| 会議室 | 予約 |
|---|---|
| （行なし） | |
