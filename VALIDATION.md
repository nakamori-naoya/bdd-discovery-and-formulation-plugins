# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
```

`validate-structure.sh`は、BDD責務の10 pluginだけを配布すること、両marketplaceと両runtime manifestのidentityが一致すること、外部依存が完全修飾されていること、shared resolverの配布コピーがbyte一致することを検査する。

`validate-runtime.sh`は、Codex/Claudeそれぞれのinstall済みcache fixtureからexact identityを解決する正常系と、依存欠落・manifest版違い・runtime不明・bare依存名を必ず拒否する負の試験を実行する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。
