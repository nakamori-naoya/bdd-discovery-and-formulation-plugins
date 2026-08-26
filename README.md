# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証する、Claude Code/Codex両対応のmarketplaceである。

## 配布するplugin

- 入口: `domain-bdd-discovery`、`domain-bdd-formulation`、`data-model-bdd-discovery`、`data-model-bdd-formulation`
- 下段: `domain-events`、`core-domain`、`persistence-scenarios`、`data-model`、`rdb-design`、`intermediate-cleanup`

資料作成と対話は別marketplaceへ分離している。入口を使う前に、必要な依存をinstallする。

```bash
codex plugin marketplace add nakamori-naoya/write-doc
codex plugin add write-doc@write-doc
codex plugin add writing-rules@write-doc
codex plugin marketplace add nakamori-naoya/grill
codex plugin add grill@grill
```

依存は`marketplace / plugin / exact version / runtime`で解決する。同名pluginを推測で選ばず、要求したidentityがinstall済みcacheに無ければ停止する。開発時だけ`HARNESS_PLUGIN_DEV_ROOTS`の明示mapでsource checkoutを指定できる。

## 検証

```bash
bash scripts/validate.sh
```

構造、両runtimeの依存解決、依存欠落、manifest版違い、runtime不明、bare依存名の拒否を検査する。コピー元とローカル差分は[VENDORING.md](VENDORING.md)と[vendor-lock.json](vendor-lock.json)に固定している。

install cacheは編集せず、このrepositoryを正本として変更する。
