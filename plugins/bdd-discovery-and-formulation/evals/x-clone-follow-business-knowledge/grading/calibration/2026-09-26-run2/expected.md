# 期待する判定

この較正の資料は、2026-09-26 の2回目の実行（claude plugin eval、`--runs 1 --ablation none`）で作られた `business-knowledge.md` と `grill-log.md` である。下の判定は、eval を組んだ担当が資料、記録、要件を読んで出したもので、採点役がこれを再現できるかで採点の形を確かめる。境目と書いた条件は、読み方で判定が分かれうるので、一致の数を別に数える。

採点役には、このファイルを読ませない。

## 判定

- boundary-no-mechanism: PASS
- boundary-value-placement: PASS
- boundary-kept-rules: PASS
- rules-who-can: PASS
- rules-command-and-query: PASS
- rules-rejection-linked: FAIL
- rules-bdd-shape: PASS
- rules-concurrency: PASS
- rules-explanation: FAIL
- rules-crud-coverage: FAIL（境目）
- language-naming: FAIL
- language-ownership: PASS
- language-consistency: FAIL（境目）
- guess-marked: FAIL
- guess-foreign-owner: PASS
- guess-no-unmarked-specifics: FAIL
- grill-answers: PASS

## 理由

rules-rejection-linked は、BDD-013、BDD-014、BDD-015 の通らなかった側に拒む理由の NOTE が無く、BDD-016 は地の文で理由を述べるだけなので FAIL とした。

rules-bdd-shape は、同時に起きたときの BDD（BDD-013〜016）を条件の例外に当て、ほかの BDD に When の二つの行いや包括表現が無いので PASS とした。1回目の judge の基準ではここが FAIL だったが、それは基準の書き方の問題で、条件を直した。

rules-explanation と guess-no-unmarked-specifics は、「常に守られること」の説明の節が、説明する相手を「サービスを運用する開発チーム」と断定し、「障害の後には、…同じ事実で確かめる」とも断定しているので FAIL とした。記録の問い1 (c) は、これを要件に無いので推奨を採ったと書いており、資料の「まだ決まっていないこと」にも載っていない。

guess-marked は、「同時に起きたときに先に受け付けた方から判断する」仮説に採らなかった案が無く、並びの向きと状態の名前の仮説に誰が決めるかが無く、問い1 (c) の推奨が仮説として現れていないので FAIL とした。

language-naming は、「自分との関係」（RelationToMe）が業務の人の言葉ではなく説明のための語なので FAIL とした。

rules-crud-coverage は、作ること（フォローする）となくすこと（フォローを外す）に BDD があるが、変えることを対象外とする文が無い。状態の図からは変える行いが無いと読めるので、境目とした。

language-consistency は、表の「フォローしていない」と、BDD の Given の「フォロー中ではない」が同じものを指して混ざり、「存在しない利用者」と「登録していない」も混ざるので FAIL とした。言い回しの揺れを語の揺れと見るかで分かれるので、境目とした。
