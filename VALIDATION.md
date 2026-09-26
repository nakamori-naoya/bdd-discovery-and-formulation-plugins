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

skill が要件だけから正しい資料を作れるかは、`plugins/bdd-discovery-and-formulation/evals/` の下のケースを `claude plugin eval` で動かして確かめる。一つのケースは一つのお題の一つの資料で、作業するエージェントとは別の judge が `graders/` の基準で採点する。今はパイロットの `x-clone-follow-business-knowledge`（X のクローンのフォローの業務知識）だけを置いている。

ケースの `scaffold.sh` は、作業場所へ要件と業務の分け方を置き、隔離環境に入らない write-doc と grill の skill を、兄弟 checkout `../write-doc-plugins/` と `../grill-plugins/` から写す。兄弟 checkout が無ければ exit 2 で止まる。skill が資料と記録を書き、検査の script を実行するので、書き込みと shell の許可を渡す。

```bash
cd plugins/bdd-discovery-and-formulation
claude plugin eval . --case x-clone-follow-business-knowledge \
  --runs 1 --ablation none --judge-model sonnet \
  --scaffold --allow-tools Write Edit Bash \
  --max-cost-usd 5 --no-publish
```

`--scaffold` は、ケースの `scaffold.sh` をあなたの権限で実行する。この repository のケースにだけ使う。実行の結果は `evals/results/` に書かれ、git の管理から外してある。
