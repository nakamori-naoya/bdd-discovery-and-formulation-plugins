---
name: formulate-data-model
description: 対応する業務知識を根拠に既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新する。その論理構造を変えず、指定されたRDB製品・バージョンのRead、型、index、分離レベル、配置へ写す。「データモデルを定式化して」「論理設計を深掘りして物理設計して」と言われたときに使う。
---

# データモデルを定式化する

読み終えると、既存のBDD付きRDB論理設計と、それに対応する業務知識を突き合わせ、永続化のQA観点の反例を当てて同じpathへ戻し、その論理構造を変えずに、指定されたRDB製品と版で確認できた機能だけを使った物理設計資料を1本新しく保存できる。論理資料は更新であり、新しい論理資料は作らない。業務知識の裏付けが無ければ既存テーブルだけから設計判断を補わない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存論理資料を保持したまま`steps`を宣言順に辿り、最後まで同じ文脈で判断する。`agent_work: invoking_agent`の工程はこのagentの認知工程、`skill:`の工程は同じpackageに同梱された同名skillの`SKILL.md`をこのagentが同じ文脈で読んで適用する工程、`script:`の工程は明示した入力から閉じた結果を返す決定論的tool、`playbook:`の工程は外部公開Skillの直接呼び出しである。工程間の値（条件マトリクス、本文）はこのagentが文脈に保持し、fileへ書き出して受け渡さない。手順に入る前に同梱の内部skill `write-bdd`の`SKILL.md`を同じ文脈で読み、その規律（入力の根拠づけ、業務の言葉、`grill` / `write-doc`の呼び方、BDDの前提・トリガー・失敗理由と条件マトリクス、定式化へ進める見極め、QA観点）を全工程へ適用する。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。どの永続化の主張を深めたいか、新しく分かったこと | 反証の焦点が読めなければ`challenge-persistence`の問いにする。決まらなければ作成・更新・削除のBDD全体を対象に仮置きして進む |
| `business_knowledge_paths` | 必須。対象repositoryに追跡済みで、既存論理資料の各設計対象に対応する業務知識資料の絶対path配列 | 無い、空、未追跡、repository外、相対path、読めないpath、symlinkなら既存論理資料を変更せず止まる |
| `references` | 任意。追加で従う資料の絶対path配列。手順の最初に読む。プロジェクト固有の規約や文脈は、対象repositoryのAGENTS.md / CLAUDE.mdとこの入力で渡される | 相対path、読めないpath、symlinkは公開契約に反する入力として止まり、正しいpathを求める |
| `existing_logical_document_path` | 更新する既存の`rdb-logical-data-modeling`資料の絶対path。symlinkではない既存file | 無い、複数ある、別pathへの出力を求められた、BDDと論理テーブル定義のどちらかが資料に無い場合は止まる |
| `modeling_method` | 論理構造への配置方法。同梱の`fact-recording` / `normalized` / `dimensional`のID、または利用者の手法fileの絶対path。IDに対応する手法fileは論理モデルの工程で適用する同梱skillの`references/methods/`が持つ | 既存資料に手法が書かれていればそれを使う。無ければ依頼、文脈、`challenge-persistence`の順で決め、それでも決まらなければ既存資料の構造から最も筋の良い手法を仮説として選び、決め方を報告と未決に書く。指した手法fileが無ければ止まる。既定値を持たない |
| `database_product` | 物理設計の対象RDB製品名（一つ） | 無ければ`challenge-persistence`の問いにする。決まらなければ論理資料の更新まで完了し、物理設計を始めずに止まる。既定値を持たない |
| `database_version` | 対象製品の正確な版 | 同上。「最新」「互換」のような幅を持つ指定は版の根拠を取れないので、一つの版を推奨して問いにする |
| `physical_output_directory` | 物理設計資料を置く既存の書き込み可能な絶対directory | 依頼に構成が示されていればそれに従う。無ければ既存資料の構成を読み、提案を`challenge-persistence`の問いに含めて確かめる。同名fileがあれば止まる |
| `physical_name` | path要素を含まない`.md`file名。日本語名を許す | 同上 |

`write-bdd`の入力に根拠づける規律に従い、利用者の発言、明示された資料、`challenge-persistence`で確認した決定だけを確定事項にする。

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| `grounded_input` | `write-bdd`の定式化へ進める共通理解かを見極める基準で、代表的な永続化の振る舞いを説明できる | 進める。どの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。既存資料にBDDと論理テーブル定義が無く反証の対象が存在しなければ、未決と回答責任者を示し、論理資料を初めて作る入口（discovery）が該当すると報告して止まる |
| 反証の対象 | 作成・更新・削除に関係するBDDである | 境界、精度と単位、状態遷移、順序、重複、同時実行、権限内の悪用、時間、規則変更の遡及、失敗時保証によって残す事実や履歴が変わるかを見る。Readやindexは論理設計へ混ぜない |
| 反証で見つかった違い | 既存理解で説明できる / 確認済みの修正が要る / 仮説つきの未決 / 論理設計の外、のどれかに分けられる | 確認済みの修正をBDD、事実、論理テーブル、列、業務制約へ戻す。未決は最も筋の良い仮説と根拠を添えて未決へ置き、仮説に依存するBDDと要素は仮説であることをその箇所に明示する |
| 物理設計へ進む前提 | 確認済みの変更が同じ論理資料へ保存され、全BDDと記録すると決めた事実、論理テーブルが双方向で一致し、`database_product`と`database_version`が一つに決まっている | 進む。満たさないうちは物理設計を始めない |
| 物理設計の内容 | 論理テーブル、列、業務上のキー・関係・制約を増減・再編していない | 書く。構造変更が必要なら物理側で補わず論理設計へ戻す |
| 採用する機能 | 対象製品・版の公式資料または実機で確認できた | 採用し、本文の`### 機能:`節の`- 利用可能な版:`と`- 根拠:`（公式https URLまたは`local:`で始まる実機確認）へ根拠を書く。根拠は読み手の判断材料なので資料自体に残す。current版だけの説明、記憶、別製品の類似機能は根拠にしない。確認できない機能は採用せず、代替と確認方法を未決に書く |
| index | 業務で典型的かつ重要なRead（対象、絞り込み、結合、並び順、鮮度、想定件数）または制約と測定根拠を持つ | 採用し、複合indexは列順の理由を書く。Readの想定件数やSLOが入力に無ければ、業務の筋から仮説の値を置き、仮説と分かる形で書く |
| 分離レベル | 論理設計の「許してはいけない同時実行結果」を、対象版で防げる現象、併用する制約・ロック、競合時の再試行まで写している | 書く。分離レベル名だけでは完了にしない |

## 手順

1. **preflight-domain-knowledge（`scripts/domain_input.py`）。** 対象repository rootをcurrent directoryにし、`business_knowledge_paths`をJSONで`python3 scripts/domain_input.py check`へ渡し、対応する業務知識資料がすべて絶対pathの通常fileとして読めることを確かめる。終了code 0以外なら既存資料を変更しない。このtoolは入力の構造だけを検査し、資料の意味は判定しない。

2. **challenge-persistence（`grill`）。** [実行指示書](references/execution-guidance.md)の「問いの選び方」、[工程間の契約](references/contract.md)、`write-bdd`の重要なシナリオを見つけるQA観点で、既存論理資料のどの永続化上の主張を反証しているかを明らかにし、答えで残す事実・履歴・業務制約または物理設計の前提（製品と版、保存先）が変わる問いを成果を左右する順に選んで推奨と理由を添え、`context`と`questions`に渡す。呼び方は`write-bdd`の入れ子の段取りを呼ぶ規律に従う。問う数の上限と対話の作法はgrillの公開契約に従い、上限で問われなかった論点は返った`open_questions`の推奨を仮置きした未決として保持する。返った`decisions`と`open_questions`を利用者入力・既存資料と突き合わせる。2回目の`grill`は、利用者が求めた場合か、決定なしでは資料を完成できない場合だけ行う。
3. **ground。** 既存論理資料、依頼、決定、未決、仮置きした推奨を根拠・仮説・未確認へ区別して`grounded_input`として保持する。
4. **deepen-scenarios。** 同梱skillの判断規律と`write-bdd`のBDDの前提・トリガー・失敗理由に従い、作成・更新・削除、履歴、保持、失敗時保証の不足を永続化シナリオ、3操作の検討状況、条件マトリクスへ深化させる。
5. **validate-scenarios（`scripts/scenario_matrix.py`）。** 条件マトリクスJSONを標準入力で`python3 scripts/scenario_matrix.py check`へ渡す。pathはこのSKILLと同じdirectoryを基準にし、fileは介さない。stdoutにJSONを1行ずつ返し、終了codeは0が違反なし、1が違反あり（各行が`path` / `detail` / `howto`）、2が入力を読めない（空、不正JSON、objectでない）。0以外なら先へ進まず`deepen-scenarios`へ戻る。
6. **revise-logical-model。** 同梱skillの判断規律と`modeling_method`で選んだ手法に従い、確認済みの発見を論理構造とBDDへ戻し、`open_questions`と仮置きした推奨を該当するBDD・要素に仮説と分かる形で書き、未決の節へ推奨・根拠・採らなかった解釈を並べ、BeforeとAfterで全テーブルを同じ順序に置いた改訂本文を作る。更新先は既存論理資料と同じpathであり、これを`requested_output_path`にする。
7. **validate-immutable-structure（`scripts/immutable_model.py`）。** 改訂本文を`python3 scripts/immutable_model.py check`へ渡し、全論理テーブルのリソース系／イベント系分類、宣言した時刻規約、イベント表の追加専用宣言という構造契約だけを検査する。状態列、完了日時、削除フラグ、条件付きNULLの業務的な妥当性はtoolに判定させず、業務知識とBDDを読んだagentが判断する。終了code 0以外なら`revise-logical-model`へ戻る。
8. **guard-logical-update（`scripts/update-guard.py`）。** `python3 scripts/update-guard.py check --existing <既存論理資料の絶対path> --output <requested_output_path>`を実行する。引数は2つのpathだけで本文は渡さない。既存fileがsymlinkでない通常fileで、両pathが同じ実体を指すときだけ終了code 0で`{"update_target": <絶対path>}`をstdoutへ返す。それ以外は終了code 1で`{"error": <診断>}`を返すので、既存資料を変えずに止まる。
9. **update-logical-document（`write-doc`）。** 改訂本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`rdb-logical-data-modeling`を`document_type`に、`update_target`をそのまま渡す。新規作成用の`output_directory`と`name`は渡さない。`references`には入力の`references`をそのまま渡す（空なら空配列）。返った結果の`status`が`completed`で、`path`が`update_target`と一致することを確かめ、その`path`を`updated_logical_document_path`にする。`failed`、結果欠落、path不一致なら理由を報告して止まり、物理設計を始めない。
10. **design-physical。** [RDB物理設計へ写す判断規律](references/physical-design-judgment.md)、[RDB設計の契約](references/design-contract.md)、[関係データのライフサイクル](references/relational-data-lifecycle.md)、[トランザクション分離](references/transaction-isolation.md)を適用し、`revise-logical-model`で適用した同梱skillの関係データモデリングの原則とNULL回避を物理設計でも保つ。保存成功した`updated_logical_document_path`だけを入力にし、次の順に進める。
   - `python3 scripts/rdb.py fingerprint --model-file <更新済み論理資料の絶対path>`で論理構造の指紋を得る。引数は保存済み正本のpathだけである。終了code 0でstdoutに`digest`を返し、1なら論理テーブル定義を読めないので論理資料へ戻り、2なら正本を読めない。指紋は物理資料の「対象と論理設計」に`- 論理構造の指紋: sha256:<digest>`として書く
   - 業務で典型的かつ重要なReadを記録してからindexを決める
   - 採用する型、制約、index、時間表現、生成列、範囲、トランザクション機能ごとに`### 機能: <機能名>`節を置き、`- 利用可能な版:`（使えるようになった版）と`- 根拠:`（対象版の公式https URL、または`local:`で始まる実機確認の要約）を欄として書く。根拠は物理設計資料そのものに残り、別の台帳やfileは持たない。同じ機能名の節を2つ置かない
   - 物理制約、型、index、分離レベル、パーティションと配置、容量・性能・運用、採用するRDB機能、代表的な読み取りを書いた物理設計本文を完成させる。節と欄は`write-doc`の`rdb-physical-design`型（公開契約の`document_type`）が定める形で書き、このpackageはtemplateを持たない。`scripts/rdb.py check`が要求するのは、その型のH2見出し11節（`## 対象と論理設計`、`## 物理制約`、`## 物理化の方針`、`## index`、`## トランザクションと分離レベル`、`## パーティションと配置`、`## 容量・性能・運用`、`## 採用するRDB機能`、`## 物理設計の完了条件`、`## 未決`、`## 代表的な読み取り`）が各1回あることと、`### index:`、`### 分離性判断:`、`### 機能:`、`### Read-<連番>:`の小見出しがその型の欄を各1回持つことである。論理テーブル定義、ER図、CUDのBDDは複製せず、入力論理資料を一つ明記する。仮説の値（想定件数、SLO、確認できなかった代替）は仮説と分かる形で書き、`## 未決`へ並べる
11. **verify-physical（`scripts/rdb.py`）。** 物理設計本文（Markdown）をそのまま標準入力で`python3 scripts/rdb.py check --model-file <更新済み論理資料の絶対path> --product <database_product> --version <database_version>`へ渡す。fileへ書かず、正本pathだけを引数にする。見出し、対象DBMSと版、指紋の一致、論理定義の非複製、業務制約の扱い、index・Read・分離性判断の欄、各`### 機能:`が`- 利用可能な版:`と`- 根拠:`を1つずつ持ち根拠が公式https URLか`local:`で始まること、機能名の重複が無いことが揃えば終了code 0、問題があれば1でstdoutへ`problem`を1行ずつ返し、入力を読めなければ（標準入力が空、正本pathが読めない）2である。0以外なら`design-physical`へ戻る。例の`...`は他の節の省略で、必須見出しと欄の全体は`write-doc`の`rdb-physical-design`型と手順8のとおりである。

   ```bash
   python3 scripts/rdb.py check --model-file /abs/path/to/logical.md --product PostgreSQL --version 16 <<'EOF'
   # RDB物理設計 — 予約
   ## 対象と論理設計
   - 対象DBMS: PostgreSQL
   - 対象バージョン: 16
   - 論理モデル: logical.md
   - 論理構造の指紋: sha256:<fingerprintが返したdigest>
   ...
   ## 採用するRDB機能
   ### 機能: 排他制約
   - 採用箇所: reservation(slot)の排他制約
   - 利用可能な版: 9.0
   - 根拠: https://www.postgresql.org/docs/16/
   - 対象バージョンで確認したこと: 実機で重なる予約の拒否を確認
   ...
   EOF
   ```

12. **document-physical（`write-doc`）。** 物理設計本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`rdb-physical-design`を`document_type`に、確認済みの`physical_output_directory`と`physical_name`をそのまま渡す。`references`には入力の`references`をそのまま渡す（空なら空配列）。返った結果の`status`が`completed`で、`path`が指定した保存先と一致することを確かめ、その`path`を`physical_rdb_design_path`にする。`failed`、結果欠落、path不一致なら理由を報告して止まる。

## 停止条件

**止まる。** 成果が無意味になる必須入力の欠落、公開契約に反する入力、toolの失敗、保存先の不確定である。止まるときは既存資料を変更せず（論理更新の保存後なら物理設計を始めず）、どこまで確定し、何が分かれば続けられるかを返す。

- `business_knowledge_paths`が無い、空、相対path、読めないpath、またはsymlinkである
- 既存論理資料のpathが無い、symlinkである、複数ある、別pathへの出力を求められた、またはBDDと論理テーブル定義のどちらかが資料に無い
- 既存資料に代表的な永続化のBDDが無く、反証の対象が存在しない。未決と回答責任者を示し、論理資料を初めて作る入口が該当すると報告する
- `modeling_method`が指した手法fileが無い、または利用者の手法fileが同梱の3本と同じ節を持たない
- `references`に相対path、読めないpath、symlinkがある
- `grill`が`completed`以外を返した、または`decisions` / `open_questions`が配列でない
- `domain_input.py` / `scenario_matrix.py` / `immutable_model.py` / `update-guard.py` / `rdb.py`のどれかが0以外で終了し、戻しても解消しない
- 論理資料の更新が`completed`以外を返した、または`path`が`update_target`と一致しない。物理設計を始めない
- `database_product`か`database_version`が`challenge-persistence`の後も一つに決まらない。論理資料の更新までを完了とし、物理設計を始めずに止まる（版の根拠が取れない物理設計は成果にならない）
- 物理設計で論理構造の変更が必要になった。物理側で補わず論理設計へ戻す
- 物理資料の保存先が確認できない、同名fileがある、`write-doc`が`completed`以外を返した、または返った`path`が保存先と一致しない

**仮説を明示して進む。** 判断の揺れ、資料の不足、複数の解釈があり得るときは止まらない。その時点の根拠から最も筋の良い仮説を立て、仮説であること、根拠、採らなかった解釈を該当箇所と未決に書いて先へ進み、確認は資料とともに仮説を添えて求める。根拠のないことを事実として書かない。既存資料の記載も仮説であり得るので、確定事項へ格上げしない。

- 反証の焦点、`modeling_method`、保持理由、履歴の要否、取消と物理削除の区別が入力から一つに決まらない。既存資料と業務の筋から仮説を置く
- 反証で見つかった違いに利用者の回答が無い。最も筋の良い解釈を仮説としてBDDと論理要素へ書き、未決へ問いを残す
- Readの想定件数、SLO、鮮度が入力に無い。業務の筋から仮説の値を置き、測定で確かめる事項として未決に書く
- grillの上限で問われなかった論点が残る。`open_questions`の推奨を仮置きした未決として資料に載せ、利用者が資料を見てから確かめる

## 報告

- 対象RDBと版、使った論理モデリング手法とその決め方（依頼指定／既存資料／文脈推定／確認済み／仮説）
- 同じpathで更新したBDD付き論理設計と、新しく保存したRDB物理設計の絶対path
- QA反証で変化した永続化の理解、追加・修正したBDD、未回答の問い
- 採用した典型Readとindex、その列順の理由
- 選択した分離レベルと競合時の扱い、NULLを許した箇所
- 仮説として置いた事項と、その根拠。`grill`で問わずに仮置きした論点（推奨つき）
- 論理構造を物理資料へ複製せず、変更もしていないこと
