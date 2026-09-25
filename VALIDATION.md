# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
bash /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/scripts/validate.sh "$(pwd)"
```

`scripts/validate.sh`は、兄弟checkout`../harness-tools/tools/`の保守tool（`validate-plugin-repository.py`とその`--self-test`、`test-hardening.py --repository`）でpackageの配置とmanifestを検査し、三つの検査スクリプトを正例・反例・境界例にかける。`scripts/test-business-knowledge.sh`は`business_knowledge.py`を、`scripts/test-immutable-model.sh`は`immutable_model.py`を、`scripts/test-query-model.sh`は`query_model.py`を確かめる。fixtureは`scripts/fixtures/`の下の`business-knowledge/`、`command-data-model/`、`query-data-model/`にある。`../harness-tools/`が無ければexit 2で止まる。

検査が見るのは、宣言と名前から一意に決まることだけである。SKILL本文の判断や、作られた資料の業務上の正しさは、対象を読んで評価する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。
