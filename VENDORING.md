# コピー境界と上流確認

## 上流の固定点

- repository: `https://github.com/nakamori-naoya/harness-plugins`
- branch: `main`
- commit: `10852c3365df0c454160082b1458ca381e5d3dab`
- 取得日: 2026-08-26

## 前回固定点以降のmerged PR

1. [PR #146 中間生成物の後片付け](https://github.com/nakamori-naoya/harness-plugins/pull/146)
   - 今回へ直接反映した。4つのBDD入口へ最終`cleanup`工程を追加し、直接依存する`intermediate-cleanup`をコピーした。
2. [PR #145 電子チケット業界題材とProduct Strategyの整理](https://github.com/nakamori-naoya/harness-plugins/pull/145)
   - product planningと`docs`の変更であり、BDD実行時依存ではないためコピーしない。
3. [PR #144 product planning用template](https://github.com/nakamori-naoya/harness-plugins/pull/144)
   - `content-types`へ追加されたproduct型はコピーしない。prototypeではBDD用2型だけを保つ。
4. [PR #143 product directionの分割](https://github.com/nakamori-naoya/harness-plugins/pull/143)
   - product pluginだけの変更であり、コピーしない。
5. [PR #142 画像生成向け図解ガイダンス](https://github.com/nakamori-naoya/harness-plugins/pull/142)
   - BDD資料化の依存閉包にある`visual-guidance`へ直接反映した。汎用の図解判断資料と参考画像だけをコピーした。
6. [PR #141 product direction](https://github.com/nakamori-naoya/harness-plugins/pull/141)
   - product pluginだけの変更であり、コピーしない。

## コピーする16 plugin directory

| plugin | version | source |
|---|---:|---|
| `domain-bdd-discovery` | 0.3.5 | [plugins/playbooks/bdd/domain-bdd-discovery](plugins/playbooks/bdd/domain-bdd-discovery/) |
| `domain-bdd-formulation` | 0.2.6 | [plugins/playbooks/bdd/domain-bdd-formulation](plugins/playbooks/bdd/domain-bdd-formulation/) |
| `data-model-bdd-discovery` | 0.2.6 | [plugins/playbooks/bdd/data-model-bdd-discovery](plugins/playbooks/bdd/data-model-bdd-discovery/) |
| `data-model-bdd-formulation` | 0.1.5 | [plugins/playbooks/bdd/data-model-bdd-formulation](plugins/playbooks/bdd/data-model-bdd-formulation/) |
| `domain-events` | 0.2.11 | [plugins/skills/domain/domain-events](plugins/skills/domain/domain-events/) |
| `core-domain` | 0.2.11 | [plugins/skills/domain/core-domain](plugins/skills/domain/core-domain/) |
| `grill` | 0.2.12 | [plugins/skills/authoring/grill](plugins/skills/authoring/grill/) |
| `persistence-scenarios` | 0.1.2 | [plugins/skills/data-modeling/persistence-scenarios](plugins/skills/data-modeling/persistence-scenarios/) |
| `data-model` | 0.2.14 | [plugins/skills/data-modeling/data-model](plugins/skills/data-modeling/data-model/) |
| `rdb-design` | 0.3.0 | [plugins/skills/data-modeling/rdb-design](plugins/skills/data-modeling/rdb-design/) |
| `write-doc` | 0.5.3 | [plugins/playbooks/authoring/write-doc](plugins/playbooks/authoring/write-doc/) |
| `content-types` | 0.6.3 | [plugins/skills/authoring/content-types](plugins/skills/authoring/content-types/) |
| `writing-rules` | 0.4.15 | [plugins/skills/authoring/writing-rules](plugins/skills/authoring/writing-rules/) |
| `visual-guidance` | 0.2.0 | [plugins/skills/authoring/visual-guidance](plugins/skills/authoring/visual-guidance/) |
| `doc-render` | 0.7.14 | [plugins/skills/authoring/doc-render](plugins/skills/authoring/doc-render/) |
| `intermediate-cleanup` | 0.1.0 | [plugins/skills/authoring/intermediate-cleanup](plugins/skills/authoring/intermediate-cleanup/) |

上流からの初回取込はplugin directory単位で行う。prototypeで削減・修正した内容は、次のローカルパッチとしてversionと`vendor-lock.json`へ明示する。

### prototypeで追加した修正

上流0.2.5では`data-model-bdd-discovery`の論理モデル工程が`data-model`に必須の`method`を渡さず、実工程の`prepare.sh`でexit 2になる。prototypeでは上流のcleanup契約へ`modeling.method: normalized`、工程へのoverride指示、validator、負の試験を重ねて0.2.6とした。上流との差分は[vendor-lock.json](vendor-lock.json)の`local_patches`にも固定した。

上流0.6.2の`content-types`は27型を一つの配布単位に持ち、product planning、期間ダイジェスト、PR実装解説、Slackを含む記載例も公開する。今回の最小境界に合わせ、`domain-rule`と`rdb-logical-data-modeling`のtemplate・example・detailだけへ縮小して0.6.3とした。

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

上流lintを丸ごと持ち込まない代わりに、この16 pluginだけを走査する[scripts/validate.sh](scripts/validate.sh)を置く。
