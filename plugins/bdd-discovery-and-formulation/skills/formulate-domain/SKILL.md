---
name: formulate-domain
description: コアドメインの既存domain-rule資料をQA観点で反証し、境界シナリオ、新しい業務理解、誰が行えるかの抜け、未決の問いを同じ資料へ戻して深化させる。「BDDを定式化して」「境界値も含めてドメイン資料を深掘りして」と言われたときに使う。新規資料は作らない。
---

# ドメインの振る舞いをBDDへ定式化する

読み終えると、既存のdomain-rule正本のコアドメインへQA観点の反例を当て、以前は説明できなかった境界を説明できる状態へ深化させ、確認済みの発見と未決を同じpathへ戻せる。作るのは更新後の正本1本だけで、新しい資料は作らない。

同じdirectoryの`playbook.yml`が工程順の正本である。このSKILLを読んだagentが、利用者の入力と既存正本を保持したまま`steps`を宣言順に辿り、最後まで同じ文脈で判断する。`agent_work: invoking_agent`の工程はこのagentの認知工程、`script:`の工程は明示した入力から閉じた結果を返す決定論的tool、`playbook:`の工程は外部公開Skillの直接呼び出しである。

## 入力

| 入力 | 内容 | 満たさないときの扱い |
|---|---|---|
| `user_input` | 依頼文。どの決まりを深めたいか、新しく分かったこと | 反証の焦点が読めなければ`challenge`で問う |
| `referenced_artifacts` | 利用者が明示した既存資料の絶対path | 相対path、読めないpath、symlinkは停止して確認する |
| `existing_domain_rule_path` | 更新する既存正本の絶対path。symlinkではない既存file | 無い、複数ある、別pathへの出力を求められた、コアの範囲が資料から読めない場合は停止する |

[入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、`challenge`で確認した決定だけを確定事項にする。既存資料も仮説を含み得るため、記載済みという理由だけで確定事項にしない。[この入口の焦点](references/focus.md)のとおり、反証の対象はコアに限る。

## 判断基準

| 観察対象 | 述語 | 行動 |
|---|---|---|
| `grounded_input` | [定式化へ進める共通理解かを見極める](references/formulation-readiness.md)の基準で、コアの代表的な業務を説明できる | 進める。どの入力から読み取れたかと、残る疑問が発見不足ではなく反証で扱う深さである理由を短く明示する。説明できなければ未決と回答責任者を示し、正本を初めて作る入口（discovery）が該当すると報告して終了する |
| 反証の対象 | 既存資料でコアと線引きされた範囲の事前状態、業務イベント、条件、誰が行えるか、業務判断、結果、次状態、後続イベントである | 反証する。支援・汎用、画面、API、DTO、DB、通信、運用は、コアの判断を変える境界でない限り掘り下げず行き先だけを残す |
| 反証で見つかった違い | 既存理解で説明できる / 確認済みの修正が要る / 回答責任者つきの未決 / コアの外、のどれかに分けられる | 確認済みの修正だけを用語、業務ルール、状態、アクター、誰が行えるか、BDDへ戻す。未決はBDDで確定事項にせず未回答の問いへ置く |
| 追加するBDD | 異なる判断、結果、次状態が生じる境界を示す | 独立したBDDにする。同じ判断しか増えない例は追加しない |
| 主体に関する決まり | 成立条件、常に守られること、誰が行えるか、拒むときの理由、BDDの5か所で同じ主体が揃っている | 揃える。片方にだけある決まりは不整合として反証し、確認後に戻す |
| 誰が行えるかの表 | すべてのコマンドとクエリに行があり、行える役割、行えない場合の業務上の理由、実現を担うものが埋まっている | 埋める。判定は「破られたときに困るのは業務か運用か」であり、運用の関心（トークン形式・有効期限、レート制限、管理者操作）は書かない |
| 本文 | QA手法の説明や検討過程を含まない | 反証によって明確になった業務理解と、それを具体化するBDDだけを残す |

## 手順

1. **challenge（`grill`）。** [実行指示書](references/execution-guidance.md)の観点と[QA観点の適用](references/qa-probes.md)、[重要なシナリオを見つけるQA観点](references/important-scenarios.md)を`context`と`questions`に渡し、既存資料のどの主張を反証しているかを明らかにして1問ずつ確かめる。呼び方は[入れ子の段取りを呼ぶ](references/nested-playbook.md)に従う。返った`decisions`と`open_questions`を利用者入力・既存資料と突き合わせる。
2. **ground。** 既存正本、依頼、決定、未決を根拠・仮説・未確認へ区別して`grounded_input`として保持し、既存資料のコアの範囲を`core_scope`にする。
3. **revise。** [シナリオの書き方](references/writing.md)、[Givenの選び方](references/given.md)、[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)に従い、複数主体や知識差が結果を変える場合だけ[登場人物と情報差](references/actors.md)を読む。確認済みの発見を既存の用語、業務ルール、状態、アクター、誰が行えるか、BDDへ対応を保って戻し、変更するBDDごとに条件マトリクスを作り、BDD草案、条件マトリクス、改訂本文を同じ文脈で完成させる。更新先は入力された既存資料と同じpathであり、これを`requested_output_path`にする。
4. **validate（`scripts/scenario.py`）。** BDD草案（Gherkin）と条件マトリクスをsystem temporary directoryの一時fileへ書き、`python3 scripts/scenario.py check --file <BDD草案> --matrix <条件マトリクスJSON>`を実行する。pathはこのSKILLと同じdirectoryを基準にする。stdoutにJSONを1行ずつ返し、終了codeは0が違反なし、1が違反あり（各行が`line` / `kind` / `detail` / `howto`）、2が入力を読めない。0以外なら更新へ進まず、診断に従って`revise`へ戻る。
5. **validate-actors（`scripts/actor-coverage.py`）。** 改訂本文を一時fileへ書き、`python3 scripts/actor-coverage.py check --file <改訂本文>`を実行する。本文の見出し`## コマンドとクエリ`と`# 誰が行えるか`の配下にある表の第1列（`業務上の行い`）が両方向で一致すれば終了code 0、片方にしか無い行い名があれば1で各行を`kind` / `detail` / `howto`として返し、読めなければ2である。0以外なら`revise`へ戻る。表記ゆれとして報告された行が同義かどうかは、このagentが読んで判断し、第1列を揃える。この2つの見出しと第1列名は、`write-doc`の`domain-rule`型（公開契約の`document_type`）が定める本文の形であり、本文をその型で書くことがtoolの前提である。
6. **guard-update（`scripts/update-guard.py`）。** `python3 scripts/update-guard.py --existing <既存正本の絶対path> --output <requested_output_path>`を実行する。既存fileがsymlinkでない通常fileで、両pathが同じ実体を指すときだけ終了code 0で`{"update_target": <絶対path>}`をstdoutへ返す。それ以外は終了code 1と診断を返すので、既存正本を変えずに停止する。
7. **document（`write-doc`）。** 改訂本文を`{kind: text, content: <完成本文>}`の1要素配列で`material`に、`domain-rule`を`document_type`に、`update_target`をそのまま渡す。新規作成用の`output_directory`と`name`は渡さない。返った結果の`status`が`completed`で、`path`が`update_target`と一致することを確かめ、その`path`を`updated_domain_rule_path`にする。`failed`、結果欠落、path不一致なら理由を報告して停止する。
8. **後片付け。** 保存成功を確認した後に、自分が作った一時fileだけを明示pathで削除する。保存に失敗したときは残す。

## 停止条件

- 既存正本のpathが無い、symlinkである、複数ある、別pathへの出力を求められた、または資料からコアの範囲が読めない
- 対話後もコアの代表的な業務を説明する基準が無い。未決と回答責任者を示し、正本を初めて作る入口が該当すると報告する
- `grill`が`completed`以外を返した、または`decisions` / `open_questions`が配列でない
- 検査または更新先検査が0以外で終了し、`revise`へ戻しても解消しない
- `write-doc`が`completed`以外を返した、または`path`が`update_target`と一致しない

停止したときは既存資料を変更せず、どこまで確定し、何が分かれば続けられるかを返す。差し替え後もコア以外の記述を勝手に深化させない。

## 報告

- 更新した既存資料の絶対path
- 追加・修正したBDDと、変化した業務理解（誰が行えるかの変化を含む）
- 未回答の問いと回答責任者
- コアの外へ送った事項
- 新規資料が無いこと
