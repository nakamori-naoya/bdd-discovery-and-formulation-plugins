---
name: formulate-user-journey
description: 既存のユーザー目的達成BDDを、目的、両端、場面接続、分岐、中断再開、役割移譲、完了の観測可能性から反証し、確認済みの理解と未決を同じ正本へ戻す。「このUser Journey BDDを深掘りして」「目的達成シナリオの抜けを検査して」と言われたときに使う。新規正本、ユースケース、ドメインルール、データモデル、テスト仕様は作らない。
---

# 既存のユーザー目的達成BDDを深化する

読み終えると、既存のユーザー目的達成BDD正本に反例を当て、Journeyである条件を再判定し、確認済みの理解と未決を同じpathへ戻せる。作るのは更新後の正本1本だけで、新しい資料は作らない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存正本を保持したまま`steps`を宣言順に辿り、最後まで同じ文脈で判断する。`agent_work: invoking_agent`の工程はこのagentの認知工程、`skill:`の工程は同じpackageに同梱された同名skillの`SKILL.md`をこのagentが同じ文脈で読んで適用する工程、`script:`の工程は明示した入力から閉じた結果を返す決定論的tool、`playbook:`の工程は外部公開Skillの直接呼び出しである。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。どの観点を深めたいか、新しく分かったこと | 反証の焦点が読めなければ`challenge`で問う |
| `referenced_artifacts` | 利用者が明示した既存資料の絶対path | 相対path、読めないpath、symlinkは停止して確認する |
| `existing_user_journey_bdd_path` | 更新する既存正本の絶対path。symlinkではない既存file | 無い、複数ある、別pathへの出力を求められた場合は停止する |

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、`challenge`で確認した決定だけを確定事項にする。既存本文は仮説を含み得るため、書いてあるという理由だけで確定事項にしない。

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| 既存本文の問い | 1人の主たるユーザー、1つの目的、開始地点、複数の意味ある場面、状態の受け渡し、観測可能な完了が一続きである | Journeyとして深化する。対象システム一つの責任、感情と接点、業務判断、保存設計、テスト実行へ変質した部分は同じ資料へ足さず、適切な正本と移動対象を報告する |
| 反例の候補 | この違いが起きたとき、主たるユーザーが何を見て気づく | 場面または分岐として戻す。気づかないなら書かず、断り書きも書かない |
| `When`の役割 | 主たるユーザー自身、または主たるユーザーとやり取りする人である | 残す。システム上の主体が役割になっていれば、主たるユーザーが観測する結果へ畳む |
| `Then`と完了条件 | 主たるユーザーが見る、知らされる、判断できる、次にできるようになる、のどれかで書けている | 残す。内部の成立だけなら、確認済みの時間境界を保ったまま観測できる結果へ戻す。戻せなければ未決にする |
| 語彙 | 入力根拠にある利用者の言葉である | 使う。内部モデルの造語に置き換わっていれば根拠のある言葉へ戻し、根拠がなければ未決にする |
| 成功に必要な前提 | 値ごと`Given`に書けている（境界値も含む） | 残す。省かれていれば値を戻す |
| 反証で見つかった違い | 既存理解で説明できる / 確認済みの修正が要る / 回答責任者つきの未決 / Journeyの外、のどれかに分けられる | 確認済みの修正だけを本文へ戻し、未決は確認相手と影響場面を持たせて未決の節へ置く |
| 目的が違う流れ | 別のJourneyである | 同じ資料へ混ぜず、作業記録の別Journey候補に残す |

## 手順

1. **challenge（`grill`）。** [実行指示書](references/execution-guidance.md)の観点と[Formulationの反証観点](references/formulation-probes.md)を`context`と`questions`に渡し、既存正本を根拠に答えで本文の変更が一つに決まる問いだけを1問ずつ確かめる。呼び方は[入れ子の段取りを呼ぶ](references/nested-playbook.md)に従う。返った`decisions`と`open_questions`を利用者入力・既存正本・明示資料と突き合わせる。
2. **ground。** 既存正本、依頼、決定、未決を根拠・仮説・未確認へ区別して`grounded_input`として保持する。
3. **remap-journey。** 同梱skillの判断規律で、既存本文を既成事実として追認せずJourneyの該当を再判定し、目的、両端、場面、状態の受け渡し、分岐を`journey_map`として保持する。
4. **revise。** [Journeyを判定し接続する判断規律](references/journey-judgment.md)、[Journeyの構造](references/journey-structure.md)、[場面のBDD](references/scenario-writing.md)、[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を適用し、確認済みの発見を該当する既存の場面へ戻し、未決を未決の節へ置く。変更するBDDごとに条件マトリクスを作り、場面草案、条件マトリクス、改訂本文を同じ文脈で完成させる。更新先は入力された既存正本と同じpathであり、これを`requested_output_path`にする。
5. **validate（`scripts/scenario.py`）。** 場面草案（`user-journey-bdd`型の本文記法: `## 場面 <連番>: <名前>`、コードフェンス内の`Given:` / `And:` / `When:` / `Then:`、失敗場面の`NOTE: Rule:` / `Source:` / `Reason:`、`**接続**:`）と条件マトリクスをsystem temporary directoryの一時fileへ書き、`python3 scripts/scenario.py check --file <場面草案> --matrix <条件マトリクスJSON>`を実行する。pathはこのSKILLと同じdirectoryを基準にする。stdoutにJSONを1行ずつ返し、終了codeは0が違反なし、1が違反あり（各行が`line` / `kind` / `detail` / `howto`）、2が入力を読めない。0以外なら更新へ進まず、診断に従って`revise`へ戻る。
6. **guard-update（`scripts/update-guard.py`）。** `python3 scripts/update-guard.py --existing <既存正本の絶対path> --output <requested_output_path>`を実行する。既存fileがsymlinkでない通常fileで、両pathが同じ実体を指すときだけ終了code 0で`{"update_target": <絶対path>}`をstdoutへ返す。それ以外は終了code 1と診断を返すので、既存正本を変えずに停止する。
7. **document（`write-doc`）。** 改訂本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`user-journey-bdd`を`document_type`に、`update_target`をそのまま渡す。新規作成用の`output_directory`と`name`は渡さない。返った結果の`status`が`completed`で、`path`が`update_target`と一致することを確かめ、その`path`を`updated_user_journey_bdd_path`にする。`failed`、結果欠落、path不一致なら理由を報告して停止する。
8. **後片付け。** 保存成功を確認した後に、自分が作った一時fileだけを明示pathで削除する。保存に失敗したときは残す。

## 停止条件

- 既存正本のpathが無い、symlinkである、複数ある、または別pathへの出力を求められた
- 既存本文からJourneyである条件を再構成できず、`challenge`でも決まらない。不足項目と確認相手を返す
- `grill`が`completed`以外を返した、または`decisions` / `open_questions`が配列でない
- 検査または更新先検査が0以外で終了し、`revise`へ戻しても解消しない
- `write-doc`が`completed`以外を返した、または`path`が`update_target`と一致しない

停止したときは既存正本を変更せず、どこまで確定し、何が分かれば続けられるかを返す。業務知識やデータモデルの資料は入力根拠として読むが変更しない。

## 報告

- 更新した正本の絶対path
- 追加・変更・削除した場面と、その根拠
- 反証して維持した境界
- Journeyから外した事項と送り先（業務知識 / 非機能要件 / 別Journey / 実現方式）
- 未決と、確定に必要な情報

新規資料を作った場合、または既存正本以外を変更した場合は完了と報告しない。
