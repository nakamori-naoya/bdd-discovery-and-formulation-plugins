---
name: formulate-data-model
description: 既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新する。その論理構造を変えず、指定されたRDB製品・バージョンのRead、型、index、分離レベル、配置へ写す。「データモデルを定式化して」「論理設計を深掘りして物理設計して」と言われたときに使う。
---

# データモデルを定式化する

読み終えると、既存のBDD付きRDB論理設計へ永続化のQA観点の反例を当てて同じpathへ戻し、その論理構造を変えずに、指定されたRDB製品と版で確認できた機能だけを使った物理設計資料を1本新しく保存できる。論理資料は更新であり、新しい論理資料は作らない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存論理資料を保持したまま`steps`を宣言順に辿り、最後まで同じ文脈で判断する。`agent_work: invoking_agent`の工程はこのagentの認知工程、`skill:`の工程は同じpackageに同梱された同名skillの`SKILL.md`をこのagentが同じ文脈で読んで適用する工程、`script:`の工程は明示した入力から閉じた結果を返す決定論的tool、`playbook:`の工程は外部公開Skillの直接呼び出しである。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。どの永続化の主張を深めたいか、新しく分かったこと | 反証の焦点が読めなければ`challenge-persistence`で問う |
| `referenced_artifacts` | 利用者が明示した既存資料の絶対path | 相対path、読めないpath、symlinkは停止して確認する |
| `existing_logical_document_path` | 更新する既存の`rdb-logical-data-modeling`資料の絶対path。symlinkではない既存file | 無い、複数ある、別pathへの出力を求められた、BDDと論理テーブルの対応が読めない場合は停止する |
| `modeling_method` | 論理構造への配置方法。同梱の`fact-recording` / `normalized` / `dimensional`のID、または利用者の手法fileの絶対path。IDに対応する手法fileは論理モデルの工程で適用する同梱skillの`references/methods/`が持つ | 既存資料に手法が書かれていればそれを使う。無ければ依頼、文脈、利用者確認の順で決め、決め方を報告する。既定値を持たない |
| `database_product` | 物理設計の対象RDB製品名（一つ） | 無ければ利用者に聞く。既定値を持たない |
| `database_version` | 対象製品の正確な版 | 同上。「最新」「互換」のような幅を持つ指定は受けない |
| `physical_output_directory` | 物理設計資料を置く既存の書き込み可能な絶対directory | 依頼に構成が示されていればそれに従う。無ければ既存資料の構成を読み一度だけ提案する。同名fileがあれば停止する |
| `physical_name` | path要素を含まない`.md`file名。日本語名を許す | 同上 |

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、`challenge-persistence`で確認した決定だけを確定事項にする。

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| `grounded_input` | [定式化へ進める共通理解かを見極める](references/formulation-readiness.md)の基準で、代表的な永続化の振る舞いを説明できる | 進める。どの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。説明できなければ未決と回答責任者を示し、論理資料を初めて作る入口（discovery）が該当すると報告して終了する |
| 反証の対象 | 作成・更新・削除に関係するBDDである | 境界、精度と単位、状態遷移、順序、重複、同時実行、権限内の悪用、時間、規則変更の遡及、失敗時保証によって残す事実や履歴が変わるかを見る。Readやindexは論理設計へ混ぜない |
| 反証で見つかった違い | 既存理解で説明できる / 確認済みの修正が要る / 回答責任者つきの未決 / 論理設計の外、のどれかに分けられる | 確認済みの修正だけをBDD、事実、論理テーブル、列、業務制約へ戻す。未決は推測で埋めない |
| 物理設計へ進む前提 | 確認済みの変更が同じ論理資料へ保存され、全BDDと記録すると決めた事実、論理テーブルが双方向で一致している | 進む。満たさないうちは物理設計を始めない |
| 物理設計の内容 | 論理テーブル、列、業務上のキー・関係・制約を増減・再編していない | 書く。構造変更が必要なら物理側で補わず論理設計へ戻す |
| 採用する機能 | 対象製品・版の公式資料または実機で確認できた | 採用し、機能根拠台帳へ根拠を記録する。current版だけの説明、記憶、別製品の類似機能は根拠にしない |
| index | 業務で典型的かつ重要なRead（対象、絞り込み、結合、並び順、鮮度、想定件数）または制約と測定根拠を持つ | 採用し、複合indexは列順の理由を書く。持たないindexは採用しない |
| 分離レベル | 論理設計の「許してはいけない同時実行結果」を、対象版で防げる現象、併用する制約・ロック、競合時の再試行まで写している | 書く。分離レベル名だけでは完了にしない |

## 手順

1. **challenge-persistence（`grill`）。** [実行指示書](references/execution-guidance.md)、[工程間の契約](references/contract.md)、[重要なシナリオを見つけるQA観点](references/important-scenarios.md)の観点を`context`と`questions`に渡し、既存論理資料のどの永続化上の主張を反証しているかを明らかにして1問ずつ確かめる。呼び方は[入れ子の段取りを呼ぶ](references/nested-playbook.md)に従う。返った`decisions`と`open_questions`を利用者入力・既存資料と突き合わせる。
2. **ground。** 既存論理資料、依頼、決定、未決を根拠・仮説・未確認へ区別して`grounded_input`として保持する。
3. **deepen-scenarios。** 同梱skillの判断規律と[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)に従い、作成・更新・削除、履歴、保持、失敗時保証の不足を永続化シナリオ、3操作の検討状況、条件マトリクスへ深化させる。
4. **validate-scenarios（`scripts/scenario_matrix.py`）。** 条件マトリクスをsystem temporary directoryの一時fileへ書き、`python3 scripts/scenario_matrix.py check --file <条件マトリクスJSON>`を実行する。pathはこのSKILLと同じdirectoryを基準にする。stdoutにJSONを1行ずつ返し、終了codeは0が違反なし、1が違反あり（各行が`path` / `detail` / `howto`）、2が入力を読めない。0以外なら先へ進まず`deepen-scenarios`へ戻る。
5. **revise-logical-model。** 同梱skillの判断規律と`modeling_method`で選んだ手法に従い、確認済みの発見を論理構造とBDDへ戻し、BeforeとAfterで全テーブルを同じ順序に置いた改訂本文を作る。更新先は既存論理資料と同じpathであり、これを`requested_output_path`にする。
6. **guard-logical-update（`scripts/update-guard.py`）。** `python3 scripts/update-guard.py --existing <既存論理資料の絶対path> --output <requested_output_path>`を実行する。既存fileがsymlinkでない通常fileで、両pathが同じ実体を指すときだけ終了code 0で`{"update_target": <絶対path>}`をstdoutへ返す。それ以外は終了code 1と診断を返すので、既存資料を変えずに停止する。
7. **update-logical-document（`write-doc`）。** 改訂本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`rdb-logical-data-modeling`を`document_type`に、`update_target`をそのまま渡す。新規作成用の`output_directory`と`name`は渡さない。返った結果の`status`が`completed`で、`path`が`update_target`と一致することを確かめ、その`path`を`updated_logical_document_path`にする。`failed`、結果欠落、path不一致なら理由を報告して停止し、物理設計を始めない。
8. **design-physical。** [RDB物理設計へ写す判断規律](references/physical-design-judgment.md)、[RDB設計の契約](references/design-contract.md)、[関係データモデリングの原則](references/relational-data-modeling-principles.md)、[NULL回避](references/null-avoidance.md)、[関係データのライフサイクル](references/relational-data-lifecycle.md)、[トランザクション分離](references/transaction-isolation.md)を適用する。保存成功した`updated_logical_document_path`だけを入力にし、次の順に進める。
   - `python3 scripts/rdb.py fingerprint --model-file <更新済み論理資料>`で論理構造の指紋を得る。終了code 0でstdoutに`digest`を返し、1なら論理テーブル定義を読めないので論理資料へ戻る。指紋は物理資料の「対象と論理設計」に`- 論理構造の指紋: sha256:<digest>`として書く
   - 業務で典型的かつ重要なReadを記録してからindexを決める
   - 採用する型、制約、index、時間表現、生成列、範囲、トランザクション機能ごとに、`python3 scripts/rdb.py capability --ledger <一時directory内の台帳.jsonl> --product <database_product> --version <database_version> --feature <機能> --support-from <利用可能な版> --evidence <対象版の公式https URLまたはlocal:で始まる実機確認> --note <理由>`で根拠を記録する。終了code 0で記録、2は入力不正、3は同じ機能が既にある（差し替えるなら`--replace`）
   - 物理制約、型、index、分離レベル、パーティションと配置、容量・性能・運用、採用するRDB機能、代表的な読み取りを書いた物理設計本文を完成させる。節と欄の骨格は[同梱の物理設計骨格](assets/physical-design.md)に従う。この骨格は`scripts/rdb.py check`が要求する見出し（`## 対象と論理設計`〜`## 代表的な読み取り`）と欄（`### index:`、`### 分離性判断:`、`### 機能:`、`### Read-<連番>:`）の正本であり、write-docの`rdb-physical-design`型と同じ見出しを持つ。論理テーブル定義、ER図、CUDのBDDは複製せず、入力論理資料を一つ明記する
9. **verify-physical（`scripts/rdb.py`）。** 物理設計本文を一時fileへ書き、`python3 scripts/rdb.py check --design-file <物理設計本文> --model-file <更新済み論理資料> --ledger <台帳.jsonl> --product <database_product> --version <database_version>`を実行する。見出し、対象DBMSと版、指紋の一致、論理定義の非複製、業務制約の扱い、index・Read・分離性判断の欄、採用機能の根拠が揃えば終了code 0、問題があれば1でstdoutへ`problem`を1行ずつ返し、読めなければ2である。0以外なら`design-physical`へ戻る。
10. **document-physical（`write-doc`）。** 物理設計本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`rdb-physical-design`を`document_type`に、確認済みの`physical_output_directory`と`physical_name`をそのまま渡す。返った結果の`status`が`completed`で、`path`が指定した保存先と一致することを確かめ、その`path`を`physical_rdb_design_path`にする。`failed`、結果欠落、path不一致なら理由を報告して停止する。
11. **後片付け。** 両方の保存成功を確認した後に、自分が作った一時file（条件マトリクス、台帳、検査用本文）だけを明示pathで削除する。保存に失敗したときは残す。

## 停止条件

- 既存論理資料のpathが無い、symlinkである、複数ある、別pathへの出力を求められた、またはBDDと論理テーブルの対応が読めない
- `database_product` / `database_version` / `modeling_method`が決まらない
- 対話後も代表的な永続化の振る舞いを説明する基準が無い。未決と回答責任者を示し、論理資料を初めて作る入口が該当すると報告する
- `grill`が`completed`以外を返した、または`decisions` / `open_questions`が配列でない
- 検査、更新先検査、物理検査のどれかが0以外で終了し、戻しても解消しない
- 論理資料の更新が`completed`以外を返した。この場合は物理設計を始めない
- 物理設計で論理構造の変更が必要になった。物理側で補わず論理設計へ戻す
- 物理資料の保存先が確認できない、既存fileがある、`write-doc`が`completed`以外を返した

停止したときは既存資料を変更せず、どこまで確定し、何が分かれば続けられるかを返す。

## 報告

- 対象RDBと版、使った論理モデリング手法とその決め方
- 同じpathで更新したBDD付き論理設計と、新しく保存したRDB物理設計の絶対path
- QA反証で変化した永続化の理解、追加・修正したBDD、未回答の問い
- 採用した典型Readとindex、その列順の理由
- 選択した分離レベルと競合時の扱い、NULLを許した箇所
- 論理構造を物理資料へ複製せず、変更もしていないこと
