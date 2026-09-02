# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証し、ユーザーの目的達成をE2Eストーリーとして資料化する、Claude Code/Codex両対応のmarketplaceである。

## インストール

### Codex

Codexのpluginコマンドには`--scope`がない。通常の手順はuser単位でmarketplaceとpluginを登録する。

```bash
codex plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins
codex plugin add domain-bdd-discovery@bdd-discovery-and-formulation
codex plugin add domain-bdd-formulation@bdd-discovery-and-formulation
codex plugin add data-model-bdd-discovery@bdd-discovery-and-formulation
codex plugin add data-model-bdd-formulation@bdd-discovery-and-formulation
codex plugin add e2e-bdd-documentation@bdd-discovery-and-formulation
codex plugin add domain-events@bdd-discovery-and-formulation
codex plugin add core-domain@bdd-discovery-and-formulation
codex plugin add persistence-scenarios@bdd-discovery-and-formulation
codex plugin add data-model@bdd-discovery-and-formulation
codex plugin add rdb-design@bdd-discovery-and-formulation
```

このrepositoryだけに分離したい場合は、repository専用の`CODEX_HOME`を作り、インストール時と利用時に同じ値を指定する。

```bash
mkdir -p .codex-home
export CODEX_HOME="$PWD/.codex-home"

codex plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins
codex plugin add domain-bdd-discovery@bdd-discovery-and-formulation
codex plugin add domain-bdd-formulation@bdd-discovery-and-formulation
codex plugin add data-model-bdd-discovery@bdd-discovery-and-formulation
codex plugin add data-model-bdd-formulation@bdd-discovery-and-formulation
codex plugin add e2e-bdd-documentation@bdd-discovery-and-formulation
codex plugin add domain-events@bdd-discovery-and-formulation
codex plugin add core-domain@bdd-discovery-and-formulation
codex plugin add persistence-scenarios@bdd-discovery-and-formulation
codex plugin add data-model@bdd-discovery-and-formulation
codex plugin add rdb-design@bdd-discovery-and-formulation
codex
```

`CODEX_HOME`には認証、設定、ログ、session、plugin metadataも保存されるため、このdirectoryはGit管理しない。

### Claude Code

Claude Codeは次のscopeを選べる。

| scope | 対象 |
|---|---|
| `user` | user全体。省略時の既定値 |
| `project` | このrepositoryで有効にする設定をGitでチーム共有する |
| `local` | このrepositoryで有効にするが、Git共有せず自分だけで使う |

repository設定としてインストールする場合は`project`を指定する。`CLAUDE_PLUGIN_SCOPE`を`user`または`local`へ変えれば、同じ手順でscopeを切り替えられる。

```bash
CLAUDE_PLUGIN_SCOPE=project

claude plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install domain-bdd-discovery@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install domain-bdd-formulation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install data-model-bdd-discovery@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install data-model-bdd-formulation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install e2e-bdd-documentation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install domain-events@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install core-domain@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install persistence-scenarios@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install data-model@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install rdb-design@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
```

## 配布するplugin

- 入口: `domain-bdd-discovery`、`domain-bdd-formulation`、`data-model-bdd-discovery`、`data-model-bdd-formulation`、`e2e-bdd-documentation`
- 下段: `domain-events`、`core-domain`、`persistence-scenarios`、`data-model`、`rdb-design`。中間生成物の後片付けは外部の `write-doc-cleanup@write-doc` を使う。

`e2e-bdd-documentation`は、目的を持つユーザーが開始地点から最終地点へ到達するまでを、複数のインタラクション場面が連なる長いBDDストーリーとして資料にする。domain-ruleやdata modelを変更せず、画面・API・テスト実行環境も扱わない。

各入口では、`playbook.yml`が工程順・依存・入出力という決定的な契約を持ち、`references/execution-guidance.md`が背景・前提・目的と各skill実行時の付加的な指示を持つ。grillへdomainやdata model固有の文脈を与えるのは後者であり、grill pluginへ観点を持ち込まない。

## インストール済みである必要があるplugin

このrepository外の依存だけを記載する。利用する工程に応じて、次がインストール済みである必要がある。

- `grill@grill`
- `write-doc@write-doc`
- `writing-rules@write-doc`
- `write-doc-cleanup@write-doc`

依存は`marketplace / plugin / runtime`の名前で解決し、versionは固定しない。install済みcacheに複数versionがあれば最新のsemantic versionを選び、そのmanifestのplugin名と、工程が要求するskill名の存在を検査する。同名pluginを別marketplaceから推測せず、名前が一致する配布物が無ければ停止する。開発時だけ`HARNESS_PLUGIN_DEV_ROOTS`の明示mapでsource checkoutを指定できる。

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

構造、旧cleanup配布物がないこと、両runtimeのcache・repository・明示dev-mapによる依存解決、必要skillの欠落、依存欠落、manifest版違い、runtime不明、bare依存名の拒否を検査する。

install cacheは編集せず、このrepositoryを正本として変更する。
