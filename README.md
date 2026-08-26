# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証する、Claude Code/Codex両対応のmarketplaceである。

## 配布するplugin

- 入口: `domain-bdd-discovery`、`domain-bdd-formulation`、`data-model-bdd-discovery`、`data-model-bdd-formulation`
- 下段: `domain-events`、`core-domain`、`persistence-scenarios`、`data-model`、`rdb-design`、`intermediate-cleanup`

## インストール済みである必要があるplugin

このrepository外の依存だけを記載する。利用する工程に応じて、次がインストール済みである必要がある。

- `grill@grill`
- `write-doc@write-doc`
- `writing-rules@write-doc`

依存は`marketplace / plugin / exact version / runtime`で解決する。同名pluginを推測で選ばず、要求したidentityがinstall済みcacheに無ければ停止する。開発時だけ`HARNESS_PLUGIN_DEV_ROOTS`の明示mapでsource checkoutを指定できる。

## 検証

```bash
bash scripts/validate.sh
```

構造、両runtimeの依存解決、依存欠落、manifest版違い、runtime不明、bare依存名の拒否を検査する。

install cacheは編集せず、このrepositoryを正本として変更する。
