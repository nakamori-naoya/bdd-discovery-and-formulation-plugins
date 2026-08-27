# E2E BDD資料の責務と構造

- **対象**: BDD marketplaceの設計・保守担当者
- **調査日**: 2026年8月27日
- **結論**: E2E BDD資料は、目的を持つユーザーが開始地点から複数のインタラクションを経て、目的が満たされた最終地点へ到達するまでを一続きのストーリーとして残す

## 結論

今回のE2Eは、E2Eテストの実行基盤ではない。test runner、実行環境、試行回数、証拠、flaky、UIやAPIの操作方法を扱わない。

中心に置くのはユーザーの目的である。1本の資料は、主たるユーザー、1つの目的、開始地点、最終地点、完了条件を持つ。目的達成までのインタラクションが多ければ、資料全体は長くてよい。途中を省略せず、複数の場面へ分けて前後を接続する。

## 調査から採用したこと

[CucumberのBDD overview](https://cucumber.io/docs/bdd/)は、BDDをDiscovery、Formulation、Automationの反復的な実践として説明し、具体例を使った協働と共通理解を中心に置く。[BDD myths](https://cucumber.io/docs/bdd/myths/)も、自動化だけをBDDとはしない。このpluginは、目的達成ストーリーのDiscoveryとFormulation、資料化を担い、Automationを所有しない。

[Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)では、Scenarioはルールを示す具体例であり、Givenは既知の状態、Whenは出来事や働きかけ、Thenは観測できる結果を表す。[Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/)が勧めるように、実現方法ではなく意図する振る舞いを書く。この規律をE2Eストーリー内部の各場面へ適用する。

[Example Mapping](https://cucumber.io/docs/bdd/example-mapping/)は、具体例と未回答の問いを区別する。場面間の接続や完了条件を確認できない場合、もっともらしい内容で補わず未決と確認先を残す。

[Agile Testing Quadrantsの解説](https://agiletester.ca/applying-the-agile-testing-quadrants-to-continuous-delivery-and-devops-culture-part-1-working-towards-continuous-delivery/)では、quadrantを工程順ではなく、チームが必要なテスト活動を考える分類として扱う。business-facingでチームを支える例は、顧客価値と期待する振る舞いを話す材料になる。E2E BDD資料はこの位置づけに近いが、テストの実行計画や結果記録ではない。

## 長いシナリオをどう扱うか

[Cucumberは通常のScenarioを簡潔に保つ](https://cucumber.io/blog/bdd/keep-your-scenarios-brief/)ことを勧めている。一方、今回のE2Eストーリーは、1つの目的を達成するまでに複数のインタラクションを必要とする。

そこで、ストーリー全体を短く制限しない。代わりに、全体を次の場面へ分ける。

```text
前の場面から受け取った状態
→ その場面での役割と主要な働きかけ
→ 観測できる応答
→ 次の場面へ渡す状態
```

各場面は1組のGiven / When / Thenを中心にする。ストーリー全体では場面ごとにWhen / Thenが繰り返される。前のThenから次のGivenへ渡る状態を`接続`として明示する。

これはCucumberの標準構文ではなく、短く宣言的なScenarioという知見と、長いインタラクティブなE2Eストーリーという要件を両立するための設計上の推論である。

## 他のBDD資料との境界

| 資料 | 中心に置く問い | このE2E資料から行わないこと |
|---|---|---|
| domain-rule | 業務として何が正しいか | 業務ルールを発見・変更しない |
| data model | 何を状態・事実として残すか | 永続化と論理構造を設計しない |
| E2E BDD | ユーザーが目的を達成するまでに何が起きるか | 個別ルールとデータ構造へ降りない |

既存のdomain-ruleやdata model資料は根拠として参照できる。ただし、E2Eストーリーからそれらを更新しない。不足が見つかった場合は未決として残し、対応するpluginへ返す。

## pluginへ反映する契約

- 1本につき主たるユーザーと目的は1つ
- 開始地点、最終地点、完了条件を場面より先に確認
- 目的達成に必要な場面数とstep数は制限しない
- 各場面にはGiven、主要なWhen、観測できるThenを置く
- 最後以外の場面は、次へ渡す状態を`接続`として明示
- UI、API、data model、テスト実行環境の関心を拒否
- 確認できない接続は未決と確認先を残す

## 調査の限界

この資料は、作成したE2E BDDが自動化できることや、個々の業務ルールが正しいことを保証しない。内容の正しさは、利用者の説明、明示された資料、確認済みの決定に依存する。

調査はBDDの共通理解、Scenarioの意味、Example Mapping、アジャイルテスト上の位置づけを説明できた時点で終了した。訂正後の対象外であるtest frameworkの機能比較は、最終設計の根拠に使用していない。
