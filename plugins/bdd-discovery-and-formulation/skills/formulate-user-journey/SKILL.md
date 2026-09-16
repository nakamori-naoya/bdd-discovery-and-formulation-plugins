---
name: formulate-user-journey
description: 既存のユーザー目的達成BDDを、目的、両端、場面接続、分岐、中断再開、役割移譲、完了の観測可能性から反証し、確認済みの理解と未決を同じ正本へ戻す。「このUser Journey BDDを深掘りして」「目的達成シナリオの抜けを検査して」と言われたときに使う。新規正本、ユースケース、ドメインルール、データモデル、テスト仕様は作らない。
---

# 既存のユーザー目的達成BDDを深化する

読み終えると、既存のユーザー目的達成BDD正本に反例を当て、Journeyである条件を再判定し、確認済みの理解と未決を同じpathへ戻せる。作るのは更新後の正本1本だけで、新しい資料は作らない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存正本を保持したまま`steps`を宣言順に辿り、最後まで同じ文脈で判断する。`agent_work: invoking_agent`の工程はこのagentの認知工程、`skill:`の工程は同じpackageに同梱された同名skillの`SKILL.md`をこのagentが同じ文脈で読んで適用する工程、`script:`の工程は明示した入力から閉じた結果を返す決定論的tool、`playbook:`の工程は外部公開Skillの直接呼び出しである。工程間の値はこのagentが文脈に保持し、fileへ書き出して受け渡さない。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。どの観点を深めたいか、新しく分かったこと | 反証の焦点が読めなければ`challenge`の問いにする。決まらなければ[Formulationの反証観点](references/formulation-probes.md)の全観点を対象に仮置きして進む |
| `references` | 任意。追加で従う資料の絶対path配列。手順の最初に読む。プロジェクト固有の規約や文脈は、対象repositoryのAGENTS.md / CLAUDE.mdとこの入力で渡される | 相対path、読めないpath、symlinkは公開契約に反する入力として止まり、正しいpathを求める |
| `existing_user_journey_bdd_path` | 更新する既存正本の絶対path。symlinkではない既存file | 無い、複数ある、別pathへの出力を求められた場合は止まる |

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、`challenge`で確認した決定だけを確定事項にする。既存本文は仮説を含み得るため、書いてあるという理由だけで確定事項にしない。

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| 既存本文の問い | 1人の主たるユーザー、1つの目的、開始地点、複数の意味ある場面、状態の受け渡し、観測可能な完了が一続きである | Journeyとして深化する。対象システム一つの責任、感情と接点、業務判断、保存設計、テスト実行へ変質した部分は同じ資料へ足さず、適切な正本と移動対象を報告する。既存本文に主たるユーザーと目的が無く再構成もできなければ、Journeyの正本ではないので止まる |
| 反例の候補 | この違いが起きたとき、主たるユーザーが何を見て気づく | 場面または分岐として戻す。気づかないなら書かず、断り書きも書かない |
| `When`の役割 | 主たるユーザー自身、または主たるユーザーとやり取りする人である | 残す。システム上の主体が役割になっていれば、主たるユーザーが観測する結果へ畳む |
| `Then`と完了条件 | 主たるユーザーが見る、知らされる、判断できる、次にできるようになる、のどれかで書けている | 残す。内部の成立だけなら、確認済みの時間境界を保ったまま観測できる結果へ戻す。戻せなければ最も筋の良い観測結果を仮説として書き、未決にする |
| 語彙 | 入力根拠にある利用者の言葉である | 使う。内部モデルの造語に置き換わっていれば根拠のある言葉へ戻し、根拠がなければ既存の語を仮置きして未決にする |
| 成功に必要な前提 | 値ごと`Given`に書けている（境界値も含む） | 残す。省かれていれば値を戻す |
| 反証で見つかった違い | 既存理解で説明できる / 確認済みの修正が要る / 仮説つきの未決 / Journeyの外、のどれかに分けられる | 確認済みの修正を本文へ戻す。未決は最も筋の良い仮説と根拠を添え、確認相手と影響場面を持たせて未決の節へ置き、仮説に依存する場面は仮説であることをその箇所に明示する |
| 目的が違う流れ | 別のJourneyである | 同じ資料へ混ぜず、作業記録の別Journey候補に残す |

## 手順

1. **challenge（`grill`）。** [実行指示書](references/execution-guidance.md)の「問いの選び方」と[Formulationの反証観点](references/formulation-probes.md)で、既存正本を根拠に答えで本文の変更が一つに決まる問いを成果を左右する順に選び、推奨と理由を添えて`context`と`questions`に渡す。呼び方は[入れ子の段取りを呼ぶ](references/nested-playbook.md)に従う。問う数の上限と対話の作法はgrillの公開契約に従い、上限で問われなかった論点は返った`open_questions`の推奨を仮置きした未決として保持する。返った`decisions`と`open_questions`を利用者入力・既存正本・明示資料と突き合わせる。2回目の`grill`は、利用者が求めた場合か、決定なしでは更新を完成できない場合だけ行う。
2. **ground。** 既存正本、依頼、決定、未決、仮置きした推奨を根拠・仮説・未確認へ区別して`grounded_input`として保持する。
3. **remap-journey。** 同梱skillの判断規律で、既存本文を既成事実として追認せずJourneyの該当を再判定し、目的、両端、場面、状態の受け渡し、分岐を`journey_map`として保持する。
4. **revise。** [Journeyを判定し接続する判断規律](references/journey-judgment.md)、[Journeyの構造](references/journey-structure.md)、[場面のBDD](references/scenario-writing.md)、[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を適用し、確認済みの発見を該当する既存の場面へ戻し、`open_questions`と仮置きした推奨を該当する場面に仮説と分かる形で書き、未決の節へ推奨・根拠・採らなかった解釈・確認相手・影響場面を並べる。変更するBDDごとに条件マトリクスを作り、場面草案、条件マトリクス、改訂本文を同じ文脈で完成させる。更新先は入力された既存正本と同じpathであり、これを`requested_output_path`にする。
5. **validate（`scripts/scenario.py`）。** 場面草案（`user-journey-bdd`型の本文記法: `## 場面 <連番>: <名前>`、コードフェンス内の`Given:` / `And:` / `When:` / `Then:`、失敗場面の`NOTE: Rule:` / `Source:` / `Reason:`、`**接続**:`）をそのまま標準入力で、条件マトリクスを`--matrix-json`引数のJSON文字列で`python3 scripts/scenario.py check`へ渡す。pathはこのSKILLと同じdirectoryを基準にし、fileは介さない。stdoutにJSONを1行ずつ返し、終了codeは0が違反なし、1が違反あり（各行が`line` / `kind` / `detail` / `howto`）、2が入力を読めない（標準入力が空、`--matrix-json`がJSONでないかobjectでない）。0以外なら更新へ進まず、診断に従って`revise`へ戻る。

   ````bash
   python3 scripts/scenario.py check --matrix-json '{"scenarios": [{"name": "希望を伝える", "kind": "success", "expected": "success", "rule": "予約成立規則", "trigger": {"kind": "action", "text": "予約者が希望を伝える"}, "premises": [{"text": "予約者が希望条件を決めている", "state": "satisfied", "target": false, "source": "予約資料"}]}]}' <<'EOF'
   # 予約を完了する

   予約者が希望する条件で予約を成立させるまでを扱う。

   ## 場面 1: 希望を伝える

   ```gherkin
   Given: 予約者が希望条件を決めている
   When: 予約者が希望を伝える
   Then: 希望に合う候補が示される
   ```
   EOF
   ````

6. **guard-update（`scripts/update-guard.py`）。** `python3 scripts/update-guard.py check --existing <既存正本の絶対path> --output <requested_output_path>`を実行する。引数は2つのpathだけで本文は渡さない。既存fileがsymlinkでない通常fileで、両pathが同じ実体を指すときだけ終了code 0で`{"update_target": <絶対path>}`をstdoutへ返す。それ以外は終了code 1で`{"error": <診断>}`を返すので、既存正本を変えずに止まる。
7. **document（`write-doc`）。** 改訂本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`user-journey-bdd`を`document_type`に、`update_target`をそのまま渡す。新規作成用の`output_directory`と`name`は渡さない。`references`には入力の`references`をそのまま渡す（空なら空配列）。返った結果の`status`が`completed`で、`path`が`update_target`と一致することを確かめ、その`path`を`updated_user_journey_bdd_path`にする。`failed`、結果欠落、path不一致なら理由を報告して止まる。

## 停止条件

**止まる。** 成果が無意味になる必須入力の欠落、公開契約に反する入力、toolの失敗である。止まるときは既存正本を変更せず、どこまで確定し、何が分かれば続けられるかを返す。

- 既存正本のpathが無い、symlinkである、複数ある、または別pathへの出力を求められた
- 既存本文に主たるユーザーと目的が無く、`challenge`でも再構成できない。不足項目と確認相手を返し、正本を初めて作る入口が該当すると報告する
- `references`に相対path、読めないpath、symlinkがある
- `grill`が`completed`以外を返した、または`decisions` / `open_questions`が配列でない
- `scenario.py` / `update-guard.py`が0以外で終了し、`revise`へ戻しても解消しない
- `write-doc`が`completed`以外を返した、または`path`が`update_target`と一致しない

**仮説を明示して進む。** 判断の揺れ、資料の不足、複数の解釈があり得るときは止まらない。その時点の根拠から最も筋の良い仮説を立て、仮説であること、根拠、採らなかった解釈を該当する場面と未決に書いて先へ進み、確認は更新後の正本とともに仮説を添えて求める。根拠のないことを事実として書かない。既存本文の記載も仮説であり得るので、確定事項へ格上げしない。

- 開始地点、最終地点、完了条件、接続、分岐、中断再開、役割移譲のどれかが既存本文と回答から一つに決まらない。最も筋の良いものを仮説として場面へ書く
- 反証で見つかった違いに利用者の回答が無い。既存理解と利用者の観測から最も筋の良い解釈を仮説として戻し、未決へ問いを残す
- grillの上限で問われなかった論点が残る。`open_questions`の推奨を仮置きした未決として正本に載せ、利用者が正本を見てから確かめる

業務知識やデータモデルの資料は入力根拠として読むが変更しない。

## 報告

- 更新した正本の絶対path
- 追加・変更・削除した場面と、その根拠
- 反証して維持した境界
- 仮説として置いた事項と、その根拠
- Journeyから外した事項と送り先（業務知識 / 非機能要件 / 別Journey / 実現方式）
- 未決と確定に必要な情報、`grill`で問わずに仮置きした論点（推奨つき）

新規資料を作った場合、または既存正本以外を変更した場合は完了と報告しない。
