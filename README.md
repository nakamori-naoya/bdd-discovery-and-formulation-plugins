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

## 設定の上書きと優先順位

設定を持つpluginは、優先順位が最も高い1ファイルだけを選ぶ。複数層をマージしないため、上書きするYAMLには同梱設定と同じ必須項目をすべて含める。必須項目の不足、未知のキー、許可されていない値があれば実行を停止する。

skillの静的設定は、上から順に優先する。

1. scope: `<scope>/<plugin-name>.config.yml`。呼び出し元がscopeを渡した実行だけで使う
2. local: `<repo>/.harness-plugins/<plugin-name>.local.yml`。端末固有で、通常はcommitしない
3. repository: `<repo>/.harness-plugins/<plugin-name>.config.yml`
4. personal: `$XDG_CONFIG_HOME/harness-plugins/<plugin-name>.config.yml`（未設定時は `~/.config/harness-plugins/<plugin-name>.config.yml`）
5. bundled defaults: plugin同梱の既定設定

playbookの静的設定は、scope、repository、personal、同梱 `playbook.yml` の順で優先する。playbookにはlocal層がない。入口playbook自身は通常のrepository設定を使い、下段のpluginへscopeを渡す。単体呼び出しではscopeを読まない。

skillでは、同梱設定の `prompt_parameters` に宣言されたpathだけ、依頼で明示された値を `--override=<path>=<value>` として最終上書きできる。宣言されていないpathを任意に上書きすることはできない。

たとえば入口は `<repo>/.harness-plugins/domain-bdd-discovery.config.yml`、その入口から呼ぶ `grill` だけの設定は `<repo>/.harness-plugins/scopes/domain-bdd-discovery/grill.config.yml` に置く。

## 検証

```bash
bash scripts/validate.sh
```

構造、両runtimeの依存解決、依存欠落、manifest版違い、runtime不明、bare依存名の拒否を検査する。

install cacheは編集せず、このrepositoryを正本として変更する。
