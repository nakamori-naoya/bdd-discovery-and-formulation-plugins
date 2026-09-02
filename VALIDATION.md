# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
```

`validate-structure.sh`は、marketplaceに登録したBDD責務のpluginだけを配布し、旧cleanup配布物が残らないこと、両marketplaceと両runtime manifestのidentityが一致すること、外部依存がmarketplace名とplugin名だけで宣言されていること、shared resolverの配布コピーがbyte一致することを検査する。E2E資料については、ユーザーの目的・開始地点・最終地点・1つ以上のインタラクション場面を必須にし、長い複数場面も受理し、実装やテスト実行環境の関心を拒否する負の試験も行う。

`validate-runtime.sh`は、Codex/Claudeそれぞれのinstall済みcache fixtureから名前一致で依存を解決し、複数versionから最新を選ぶ正常系と、依存欠落・manifest名違い・runtime不明・bare依存名・version pinを必ず拒否する負の試験を実行する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。
