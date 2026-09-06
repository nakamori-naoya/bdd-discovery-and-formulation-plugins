# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
```

`validate-structure.sh`は、marketplaceに登録したBDD責務のpluginだけを配布し、旧cleanup配布物が残らないこと、両marketplaceと両runtime manifestのidentityが一致すること、外部依存がmarketplace名とplugin名だけで宣言されていること、shared resolverの配布コピーがbyte一致することを検査する。E2E資料については、ユーザーの目的・開始地点・最終地点・1つ以上のインタラクション場面を必須にし、長い複数場面も受理し、実装やテスト実行環境の関心を拒否する負の試験も行う。

`validate-runtime.sh`は、Codex/Claudeそれぞれのinstall済みcache fixtureから名前一致で依存を解決し、複数versionから最新を選ぶ正常系と、依存欠落・manifest名違い・runtime不明・bare依存名・version pinを必ず拒否する負の試験を実行する。

加えて「外部pluginの公開面はplaybook 1枚だけ」という規則の負の試験を持つ。解決済みYAMLのstepsを書き換えて`--check-steps`へ渡し、次がすべて停止することを確かめる。

- 外部pluginの公開skillを`skill:`で呼ぶ形（`external-dependency-skill`）
- 外部pluginの内部skillの名指し
- 外部pluginのscriptを`script:` + `plugin:`で実行する形（`external-dependency-script`）
- 公開面4点以外のpathを外部rootから組み立てる形（`external-dependency-path`）
- `when`付きの非活性stepへ隠した違反
- 契約が実装していない文書型（`binding-capability-unsupported`）
- `implements`を宣言していない提供側

`validate-real-distribution.sh`は、fixtureではなく**実際に配布されている依存先package**に対して6 playbook×両runtimeの解決を行い、消費側lint（`lint-consumer-contract.py`）を通す。依存先は兄弟checkout`../grill-plugins/plugins`・`../write-doc-plugins/plugins`、または`HARNESS_PLUGIN_REAL_ROOTS`で渡す契約ID→package rootのJSONから探す。見つからなければ落ちる。fixtureの乖離で緑になる状態を作らない。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。
