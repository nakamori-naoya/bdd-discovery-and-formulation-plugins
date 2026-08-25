# data-model

**何を記録しないと業務が回らないかから論理設計する。** BDDシナリオを論理データモデルに含め、テーブルと列がどの業務上の条件・結果を支えるかを残します。保存の物理的な実現は後で、手法は差し替えられます。

**手法によらない部分がこのプラグインの本体である。** 記録すべき事実のシナリオが洗い出されていること。それが無ければ、どの手法でも設計は始まらない。

## 何を返すか

| 成果物 | 中身 |
|---|---|
| `<model_dir>/<題材>.facts.jsonl` | 記録すべき事実のシナリオ。要素・事実・**記録しないと困ること**・必要とする人・出所・確からしさ |
| `<model_dir>/<題材>.md`（利用者が置く） | BDDシナリオを含む論理データモデル。RDB向けは同梱テンプレートを使う |

`fact.py check`が**両側から突き合わせます**。入力された永続化シナリオが資料末尾のBDDに無い場合、モデルにあるのに記録の必要が説明されていないテーブル、記録すると決めたのにモデルに無いものを落とします。物理の実装（`CREATE TABLE`、SQL、DDL、index、分離レベル）が混ざっていても落とします。

RDBの論理設計には`assets/logical-design.md`を使います。論理テーブル、列、業務上のキーと制約はここで固定し、物理設計では増減・再編しません。

## 手法

`method` に**同梱のID**か、**利用者のファイルのパス**（`/` か `.` を含むもの）を書きます。指したのに無ければ止まります。

| ID | 何を先に決めるか | 向くとき |
|---|---|---|
| `fact-recording` | 残す事実の単位、同一性、時間、今の姿の導き方 | 「なぜそうなったか」を必ず問われる業務 |
| `normalized` | 対象、識別、多重度、上書きの可否 | 対象がはっきりし、重複を避けたい |
| `dimensional` | 測るもの、粒度、切り口、切り口の変化 | 集計して比べることで判断する業務 |

**手法が決めるのは配置の仕方だけです。** 何を記録するかは手法では決まりません。自分の手法を足すなら、同梱の3つと同じ節（先に決めること／成果物として出すもの／向くとき／向かないとき／見直しの問い）を持つファイルを書いて指してください。

## 設定

`<repo>/.harness-plugins/data-model.config.yml`（無ければ `${XDG_CONFIG_HOME:-~/.config}/harness-plugins/data-model.config.yml`、それも無ければ同梱既定）。**1ファイルだけが選ばれ、層は混ざりません。**

```yaml
version: 1
model_dir: domain/model         # モデルと記録シナリオの置き場
prompt_parameters:
  method:
    type: string
    required: true
instructions:
  design:
    directive: 記録すべき事実を先に洗い出し、BDDシナリオを含む論理データモデルへ写す
```

**`method`は依頼のたびに変わる値なので、設定ファイルのどの層にも実値の既定を持ちません。** 実値は依頼から`--override=method=<同梱IDまたは利用者ファイルのパス>`として都度渡されます。依頼で手法が指定されていればそれを使い、無ければ文脈で判断するか利用者に聞きます。**どちらを使ったかは必ず報告されます。**

## 使うもの

| コマンド | 必要な場面 |
|---|---|
| `bash` | 設定の解決 |
| `jq` / `yq` v4系 | 設定の検証と読み取り |
| `python3` | 記録シナリオの台帳と突き合わせ（標準ライブラリのみ） |
| `git` | repository root の判定（無ければカレントを root として扱う） |

## 中身

| 場所 | 役割 |
|---|---|
| `scripts/resolve.sh` | 設定を1件選び、手法をIDかパスで解決する |
| `scripts/fact.py` | 記録シナリオの台帳、表化、モデルとの双方向突き合わせ |
| `references/domain-events.md` | 要求・通知・event recordと区別した、すでに起きた業務事実 |
| `references/event-sourcing.md` | 変更列から状態を再構成する設計の便益・費用・採否の問い |
| `references/data-models.md` | ドメインモデルから業務の永続化へ進み、現在値・履歴・write・read・分析・物理modelを分ける判断 |
| `references/immutable-data-modeling.md` | 業務イベントから成立済みの事実を見出し、上書きせずに現在状態と分ける判断 |
| `references/relational-data-modeling-principles.md` | 関係、識別、型、制約を明示し、汎用の器へ業務事実を隠さない原則 |
| `references/null-avoidance.md` | NULLへ複数の業務上の意味を押し込めず、状態、関係、種類、業務イベントへ分ける原則 |
| `references/relational-data-lifecycle.md` | 現在と履歴、正本と派生、制約と変化、並行処理、復旧の境界を長期で守る原則 |
| `references/concept-map.md` | 振る舞いから記録と目的別モデルへ至る関係と、混同したときの失敗 |
| `references/fact-recording-contract.md` | 手法によらず共通の、記録シナリオの形と良し悪し |
| `references/methods/` | 同梱の設計手法 |
| `assets/logical-design.md` | BDDを末尾に置き、全テーブルのER図・定義・Before / Afterを一つにするRDB論理設計テンプレート |
| `skills/design-data-model/` | 設計の入口 |

## しないこと

- 物理設計（物理名、物理型、DDL、索引、分離レベル、パーティション、移行手順、性能）
- 手法の優劣を決めること。**向き不向きを示すだけ**
