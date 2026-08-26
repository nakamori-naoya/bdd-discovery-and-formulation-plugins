# knowledge-hub BDD plugin prototype

`harness-plugins`から、BDDのドメイン理解とデータモデリングに必要な配布物だけを切り出した検証用marketplaceである。正式な`knowledge-hub`内の配置、派生plugin名、marketplace名は未決のため、このdirectory自体はprototypeとして扱う。

knowledge-hubへ移行する目的と対象範囲は[knowledge-hubへのBDDハーネス移行方針](KNOWLEDGE-HUB-MIGRATION.md)にまとめた。

コピー元は`nakamori-naoya/harness-plugins`のcommit `10852c3365df0c454160082b1458ca381e5d3dab`である。コピー対象と固定点以降のPR判断は[VENDORING.md](VENDORING.md)、機械可読な固定情報は[vendor-lock.json](vendor-lock.json)に記録した。

## 含むもの

- 入口: `domain-bdd-discovery`、`domain-bdd-formulation`、`data-model-bdd-discovery`、`data-model-bdd-formulation`
- 実行時依存: 上記4入口の依存閉包12 plugin。最終資料の保存後に中間生成物を安全に片付ける`intermediate-cleanup`を含む
- 開発用正本: 対象pluginが使う`shared`と同期script
- 受入用入力: [電子チケット入退場のお題](fixtures/electronic-ticket-entry-exit-exercise.md)
- 対象限定検証: [scripts/validate.sh](scripts/validate.sh)

Slack、meeting、session収集、digest、cadence、agent-run、PR関連、use-case／journey BDD、MCP、connector、hookは含めない。

## 検証

```bash
bash scripts/validate.sh
```

構造、manifest、marketplace、shared正本とのbyte一致、構文、BDD入力根拠の負の試験、playbook解決、入れ子を含む全skill工程の`prepare.sh`までを検査する。実測結果は[VALIDATION.md](VALIDATION.md)に記録する。

Codexの`plugin-creator` validatorは、上流のroot `SKILL.md`方式と別のmanifest契約を要求するため必須受入から分離している。互換差分を確認するときは、PyYAMLを利用できるPython環境で`bash scripts/validate-plugin-creator.sh`を別途実行する。

## install前の注意

prototypeは上流と同じplugin名・skill名を保持している。既存の`harness-plugins`版と同時にinstallすると競合し得るため、正式配置で派生名を決めるまではglobal installせず、同梱resolverによる隔離検証に留める。

正式名を決めた後は、Codexではこのrepository rootをmarketplaceとして追加し、16 pluginをinstallする。Claude Codeでも同じrootをmarketplaceとして追加する。名前変更時は、marketplace、両manifest、playbookの`requires`、`steps[].skill`を別々に更新して検査する。

## チューニング

install cacheは編集せず、このsourceを変更する。共有記述を変えるときは`shared`正本を先に変更し、[scripts/sync-skill-entry.py](scripts/sync-skill-entry.py)または対象の配布コピーへ同期する。配布変更ではCodex manifest、Claude manifest、両marketplaceのversionを一致させる。
