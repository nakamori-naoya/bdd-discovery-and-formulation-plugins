# コピー境界と上流確認

## 上流の固定点

- repository: `https://github.com/nakamori-naoya/harness-plugins`
- branch: `main`
- commit: `f9e30db06f98309840066789c8d7844bd217ffe5`
- 取得日: 2026-08-25

## 直近3件のmerged PR

1. [PR #140 BDDの公開plugin名にbddを含める](https://github.com/nakamori-naoya/harness-plugins/pull/140)
   - 今回へ直接反映した。4入口の公開plugin名、playbook名、設定ファイル名を`*-bdd-discovery`／`*-bdd-formulation`へ統一した。
2. [PR #139 BDD成果物をMarkdownへ固定しdirectory名を統一](https://github.com/nakamori-naoya/harness-plugins/pull/139)
   - 今回へ直接反映した。4入口は`plugins/playbooks/bdd/*-bdd-discovery`と`*-bdd-formulation`からコピーし、`output_format: markdown`を含む最新内容を保持した。
   - 公開plugin名は次のPR #140による名称も含め、現在の上流どおり維持する。
3. [PR #138 docs: Codex sandboxの目的と制約を説明する](https://github.com/nakamori-naoya/harness-plugins/pull/138)
   - `docs`だけの変更であり、BDD実行時依存ではないためコピーしない。

## コピーする15 plugin directory

| plugin | version | source |
|---|---:|---|
| `domain-bdd-discovery` | 0.3.4 | [plugins/playbooks/bdd/domain-bdd-discovery](plugins/playbooks/bdd/domain-bdd-discovery/) |
| `domain-bdd-formulation` | 0.2.5 | [plugins/playbooks/bdd/domain-bdd-formulation](plugins/playbooks/bdd/domain-bdd-formulation/) |
| `data-model-bdd-discovery` | 0.2.5 | [plugins/playbooks/bdd/data-model-bdd-discovery](plugins/playbooks/bdd/data-model-bdd-discovery/) |
| `data-model-bdd-formulation` | 0.1.4 | [plugins/playbooks/bdd/data-model-bdd-formulation](plugins/playbooks/bdd/data-model-bdd-formulation/) |
| `domain-events` | 0.2.11 | [plugins/skills/domain/domain-events](plugins/skills/domain/domain-events/) |
| `core-domain` | 0.2.11 | [plugins/skills/domain/core-domain](plugins/skills/domain/core-domain/) |
| `grill` | 0.2.12 | [plugins/skills/authoring/grill](plugins/skills/authoring/grill/) |
| `persistence-scenarios` | 0.1.2 | [plugins/skills/data-modeling/persistence-scenarios](plugins/skills/data-modeling/persistence-scenarios/) |
| `data-model` | 0.2.14 | [plugins/skills/data-modeling/data-model](plugins/skills/data-modeling/data-model/) |
| `rdb-design` | 0.3.0 | [plugins/skills/data-modeling/rdb-design](plugins/skills/data-modeling/rdb-design/) |
| `write-doc` | 0.5.3 | [plugins/playbooks/authoring/write-doc](plugins/playbooks/authoring/write-doc/) |
| `content-types` | 0.5.12 | [plugins/skills/authoring/content-types](plugins/skills/authoring/content-types/) |
| `writing-rules` | 0.4.15 | [plugins/skills/authoring/writing-rules](plugins/skills/authoring/writing-rules/) |
| `visual-guidance` | 0.1.5 | [plugins/skills/authoring/visual-guidance](plugins/skills/authoring/visual-guidance/) |
| `doc-render` | 0.7.14 | [plugins/skills/authoring/doc-render](plugins/skills/authoring/doc-render/) |

上流からの初回取込はplugin directory単位で行う。prototypeで削減・修正した内容は、次のローカルパッチとしてversionと`vendor-lock.json`へ明示する。

### prototypeで追加した修正

上流0.2.4では`data-model-bdd-discovery`の論理モデル工程が`data-model`に必須の`method`を渡さず、実工程の`prepare.sh`でexit 2になった。prototypeでは`modeling.method: normalized`を契約へ追加し、対象工程へoverrideとして渡す指示・validator・負の試験を追加して0.2.5とした。上流との差分は[vendor-lock.json](vendor-lock.json)の`local_patches`にも固定した。

上流`content-types`は25型を一つの配布単位に持ち、期間ダイジェスト、PR実装解説、Slackを含む記載例も公開する。今回の最小境界に合わせ、`domain-rule`と`rdb-logical-data-modeling`のtemplate・example・detailだけへ縮小して0.5.12とした。

## コピーする開発用正本

- 共通入口・resolver・状態: [shared/prepare.sh](shared/prepare.sh)、[shared/skill](shared/skill/)、[shared/playbook](shared/playbook/)、[shared/skill-entry](shared/skill-entry/)
- ドメイン判断資料: [shared/domain-modeling](shared/domain-modeling/)
- データモデリング判断資料: [shared/data-modeling](shared/data-modeling/)
- BDD品質資料: [shared/quality-engineering](shared/quality-engineering/)
- 起動block同期: [scripts/sync-skill-entry.py](scripts/sync-skill-entry.py)

rootの`shared`は開発時の正本であり、plugin installでは運ばれない。各plugin内のbyte一致コピーも残し、対象限定検証でずれを止める。

## コピーしないもの

- use-case／journey BDD、grill-to-doc
- Slack、meeting、session収集
- digest、cadence、agent-run、review、pull request関連
- MCP server、connector、hook
- 上記だけが使うsharedとtest
- 全marketplaceを前提とする上流の`bash scripts/lint.sh`

上流lintを丸ごと持ち込まない代わりに、この15 pluginだけを走査する[scripts/validate.sh](scripts/validate.sh)を置く。
