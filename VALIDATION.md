# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
bash /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/scripts/validate.sh "$(pwd)"
```

`validate-structure.sh`は、両marketplaceと両runtime manifestのidentityが一致すること、公開入口6つと内部skill5つの集合がmanifestとdirectoryで一致すること、`CONTRACT.md`を持たないpackageが`playbooks` / `implements`を宣言しないこと、runtime manifestがpackage rootにだけあること、各`SKILL.md`の`name`がdirectory名と一致すること、隣接`playbook.yml`が外部packageだけを`requires`へ宣言し`playbook:`工程でだけ呼ぶこと、`script:` / `skill:`参照が実在すること、入口ごとの`scripts/`に置く同名tool（`scenario_matrix.py`、`actor-coverage.py`、`scenario.py`、`update-guard.py`）がbyte一致すること、参照資料（`references/*.md`。入口ごとの`execution-guidance.md` / `focus.md`を除く）が同じ名前で2か所以上に無いこと、禁止参照形が配布物に無いことを検査する。

続けて、各toolの`self-test`（正例・反例・境界例: 空stdin、不正JSON、正本pathの欠落、旧引数のargparse拒否）と、SKILL.mdの手順と同じ形（本文はstdin、条件マトリクスは`--matrix-json`引数）でfixtureを渡す実行を行う。条件マトリクス（暗黙前提の拒否）、domainのGherkin検査（量を品質gateにせず、複数Whenを拒否）、誰が行えるかの網羅（`actor-coverage.py`）、ユーザー目的達成BDD（複数場面の受理、語彙責務を機械判定しない、接続欠落の拒否）、formulation 3入口の同一パス更新（`update-guard.py check`）、物理設計検査（指紋、機能節の根拠欄、論理構造の変化の拒否）である。agentが作った本文をfile引数で渡す経路が無いことは、tokenの不在では検査せず、SKILL.mdの手順文とscriptの引数を読んで評価する。

`validate.sh`はさらに兄弟checkout`../harness-tools/tools/`の保守tool（`validate-plugin-repository.py`とその`--self-test`、`test-hardening.py --repository`）と、兄弟checkoutの実配布物に対する消費側lint（`lint-consumer-contract.py --repo --runtime`）を両runtimeで実行する。`../harness-tools/`が無ければexit 2で止まり、実配布物が見つからなければ落ちる。参照資料は1か所にだけ置くので、複製のbyte一致検査は同名の不在検査へ置き換えた。各入口が内部skill `write-bdd`の規律へ到達できることは、SKILL本文を読んで評価する。

workspace rootの`scripts/validate.sh`（`../harness-tools/tools/validate-workspace.sh`へ委譲）は、規約入口と、配置・manifest・隣接playbook.yml・禁止参照形の構造契約を検査する。構造検査の成功は、SKILL本文の判断規律や生成された資料の業務上の正しさを保証しない。それらは対象を読んで評価する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。
