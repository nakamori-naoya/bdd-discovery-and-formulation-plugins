# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
bash /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/scripts/validate.sh "$(pwd)"
```

`scripts/validate.sh`は、兄弟checkout`../harness-tools/tools/`の保守tool（`validate-plugin-repository.py`とその`--self-test`、`test-hardening.py --repository`）でpackageの配置とmanifestを検査し、三つの検査スクリプトを正例・反例・境界例にかける。`scripts/test-business-knowledge.sh`は`business_knowledge.py`を、`scripts/test-immutable-model.sh`は`immutable_model.py`を、`scripts/test-query-model.sh`は`query_model.py`を確かめる。fixtureは`scripts/fixtures/`の下の`business-knowledge/`、`command-data-model/`、`query-data-model/`にある。`../harness-tools/`が無ければexit 2で止まる。

検査が見るのは、宣言と名前から一意に決まることだけである。SKILL本文の判断や、作られた資料の業務上の正しさは、対象を読んで評価する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。

## 検証の eval

skill が要件だけから正しい資料を作れるかは、`plugins/bdd-discovery-and-formulation/evals/` の下のケースで確かめる。一つのケースは一つのお題の一つの資料である。実行は `claude plugin eval` が受け持ち、資料の出来の採点は、作業したエージェントとは別の Claude（採点役）が、条件ごとに判定と根拠の引用と理由を書いて受け持つ。今はパイロットの `x-clone-follow-business-knowledge`（X のクローンのフォローの業務知識）だけを置いている。

採点を plugin eval の `llm` grader に任せないのは、judge が資料一本しか読めず、PASS か FAIL の一語しか返さないからである。資料を要件や grill の記録と突き合わせる条件で、judge は判定を誤り、その理由も残らなかった。plugin eval の `graders/` には、読まずに判定できるもの（資料と記録ができたか、skill と検査の script と template を使ったか）だけを置く。

ケースは次のものを持つ。`prompt.md` と `case.yaml` は実行の指示、`materials/` は実行の担当に渡す要件と業務の分け方、`scaffold.sh` はそれらと、隔離環境に入らない write-doc と grill の skill を、兄弟 checkout `../write-doc-plugins/` と `../grill-plugins/` から作業場所へ写す script である。兄弟 checkout が無ければ exit 2 で止まる。`grading/brief.md` と `grading/criteria.md` は採点役への指示と判定の条件、`grading/calibration/` は採点役を確かめるための資料と、期待する判定である。

実行は次のとおりである。skill が資料と記録を書き、検査の script を実行するので、書き込みと shell の許可を渡す。`--scaffold` は、ケースの `scaffold.sh` をあなたの権限で実行するので、この repository のケースにだけ使う。

```bash
cd plugins/bdd-discovery-and-formulation
claude plugin eval . --case x-clone-follow-business-knowledge \
  --runs 1 --ablation none --keep-temp \
  --scaffold --allow-tools Write Edit Bash \
  --max-cost-usd 5 --no-publish
```

採点は、実行が残した一時ディレクトリ（`kept temp:` の行に出る）を渡して次で行う。採点役は Read、Glob、Grep だけを使い、成果物と `materials/` を写した採点用のディレクトリの外は読めない。期待する判定を三つ目の引数に渡すと、条件ごとに突き合わせて一致の数を出す。

```bash
bash scripts/grade-eval.sh plugins/bdd-discovery-and-formulation/evals/<ケース> /private/tmp/e-XXXXXX
```

条件や採点役への指示を変えたら、`grading/calibration/` の資料に採点役をかけ、期待する判定を再現できるかを先に確かめる。実行と採点の結果は `evals/results/` に書かれ、git の管理から外してある。
