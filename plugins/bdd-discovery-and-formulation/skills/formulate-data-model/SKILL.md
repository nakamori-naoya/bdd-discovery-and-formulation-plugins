---
name: formulate-data-model
description: 対応する業務知識を根拠に、既存のBDD付きRDB論理データモデルへ境界値・反例・順序・重複・同時実行を当て、確認済みの発見を同じ論理設計正本へ更新する。「論理データモデルを定式化して」「永続化BDDを深掘りして」と言われたときに使う。
---

# 論理データモデルを定式化する

読み終えると、既存のBDD付きRDB論理データモデルと対応する業務知識を突き合わせ、永続化の主張をQA観点で反証し、確認済みの発見を同じpathへ保存できる。新しい論理資料、物理設計、index、DBMS固有型、分離レベル、配置は作らない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存論理資料を保持したまま`steps`を宣言順に辿る。手順に入る前に同梱の内部skill `write-bdd`の`SKILL.md`を読み、その入力根拠、業務の言葉、`grill` / `write-doc`、BDDの前提・トリガー・失敗理由、定式化の見極め、QA観点を全工程へ適用する。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。深めたい永続化の主張、新しく分かったこと | 反証の焦点が読めなければ`challenge-persistence`の問いにする。決まらなければ作成・更新・削除のBDD全体を対象に仮置きして進む |
| `business_knowledge_paths` | 必須。対象repositoryに追跡済みで、既存論理資料の各設計対象に対応する業務知識資料の絶対path配列 | 無い、空、未追跡、repository外、相対path、読めないpath、symlinkなら既存論理資料を変更せず止まる |
| `references` | 任意。追加で従う資料の絶対path配列 | 相対path、読めないpath、symlinkなら止まる |
| `existing_logical_document_path` | 更新する既存`rdb-logical-data-modeling`正本の絶対path | 無い、複数、symlink、BDDまたは論理テーブル定義が無い、別pathへの出力要求なら止まる |
| `modeling_method` | 論理構造への配置方法。同梱の`fact-recording` / `normalized` / `dimensional`、または利用者の手法fileの絶対path | 既存資料、依頼、文脈、確認結果の順で決める。決まらなければ最も筋の良い手法を仮説として選び、根拠と採らなかった解釈を未決へ書く。指した手法fileが無ければ止まる |

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| `grounded_input` | 代表的な永続化の振る舞いと反証対象を説明できる | 定式化へ進む。反証対象が無ければ、初回発見が必要な理由と未決を返して止まる |
| 反証の対象 | 作成・更新・削除に関係するBDDである | 境界、精度と単位、状態遷移、順序、重複、同時実行、権限内の悪用、時間、規則変更の遡及、失敗時保証によって残す事実や履歴が変わるかを見る |
| 反証で見つかった違い | 既存理解で説明できる／確認済み修正／仮説つき未決／論理設計外のどれかに分けられる | 確認済み修正をBDD、事実、論理テーブル、列、業務制約へ戻す。未決は推奨仮説、根拠、採らなかった解釈とともに該当箇所へ明示する |
| 技術方式の論点 | Read、index、物理型、DBMS機能、分離レベル、配置だけを変える | 論理正本へ混ぜず、論理定式化の範囲外として物理設計へ渡す |

## 手順

1. **preflight-domain-knowledge（`scripts/domain_input.py`）。** `business_knowledge_paths`をJSONで標準入力へ渡す。終了code 0以外なら既存資料を変更しない。
2. **challenge-persistence（`grill`）。** [実行指示書](references/execution-guidance.md)と[工程間の契約](references/contract.md)に従い、既存論理資料のどの永続化上の主張を反証するかを示し、答えで残す事実、履歴、業務制約が変わる問いだけを成果を左右する順に渡す。返った未決は推奨を仮説として保持する。2回目は利用者が求めた場合か、決定なしでは停止条件に当たる場合だけ呼ぶ。
3. **ground。** 既存論理資料、依頼、決定、未決を根拠・仮説・未確認へ区別して`grounded_input`として保持する。
4. **deepen-scenarios。** 同梱skillの判断規律で、作成・更新・削除、履歴、保持、失敗時保証を永続化シナリオ、3操作の検討状況、条件マトリクスへ深化させる。
5. **validate-scenarios（`scripts/scenario_matrix.py`）。** 条件マトリクスJSONを標準入力で検査する。終了code 0以外なら`deepen-scenarios`へ戻り、解消できなければ止まる。
6. **revise-logical-model。** 確認済みの発見を論理構造とBDDへ戻し、仮説を該当BDD・要素と未決へ明示した改訂本文を作る。更新先は既存論理資料と同じpathにする。
7. **validate-immutable-structure（`scripts/immutable_model.py`）。** 改訂本文を標準入力で渡し、全論理テーブルの分類、時刻規約、イベント表の追加専用宣言という構造契約を検査する。意味は業務知識とBDDを読んだagentが判断する。
8. **guard-logical-update（`scripts/update-guard.py`）。** 既存論理資料と要求した更新先が同じ実体を指すことを検査し、返った`update_target`だけを保存先にする。
9. **update-logical-document（`write-doc`）。** 改訂本文を`material: [{kind: text, content: <本文>}]`、`document_type: rdb-logical-data-modeling`、`update_target`、入力の`references`で保存する。`status: completed`かつ返却pathが`update_target`と一致した場合だけ完了する。

## 停止条件

**止まる。** 必須入力が欠ける、入力pathが公開契約に反する、既存資料に反証対象が無い、toolまたは外部playbookが失敗する、更新先が同じ実体でない場合である。既存資料を変更せず、確定済み範囲、止めた判断、必要な入力、再開条件を返す。

**仮説を明示して進む。** 反証の焦点、手法、保持理由、履歴、取消と物理削除の区別、反証で見つかった違いへの回答が一つに決まらない場合は、既存資料と業務の筋から最も筋の良い仮説を置き、根拠と採らなかった解釈を該当箇所と未決へ書く。

## 出力

- `updated_logical_document_path`: 同じpathへ更新したBDD付きRDB論理データモデル正本の絶対path
- QA反証で変化した永続化の理解、追加・修正したBDD、未回答の問い、採用した仮説と根拠の報告
- 物理設計へ渡すが論理正本には混ぜなかった技術論点
