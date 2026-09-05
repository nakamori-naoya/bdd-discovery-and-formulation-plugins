# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証し、User Journeyを線引きしてユーザー目的達成BDDを発見・深化する、Claude Code/Codex両対応のmarketplaceである。

## BDDを使う場面

**業務上の正しさを、具体的な事前状態・出来事・判断・結果で共有したいときに使う。** 実装方法やテストコードを先に決めるためではなく、関係者が同じ例を見て同じ結論へ到達できる状態を作る。

- 人によって業務ルールの説明が違う
- 正常系は分かるが、境界値や拒否条件が決まっていない
- 画面やAPIの話が先行し、何を守る業務なのか説明できない
- DBへ何を残すべきか、業務上の根拠から決めたい
- 個別機能は説明できるが、ユーザーが目的を達成する一連の流れがつながらない

既存資料も業務シナリオもない状態で、いきなりFormulationから始めない。最初の正本を作る場合はDiscoveryを使い、既存の正本を反証して更新する場合にFormulationを使う。

## どのpluginを使うか

| 今の状況 | 選ぶplugin | 得られるもの |
|---|---|---|
| 業務で何が起きるかをまだ洗い出せていない | `domain-events` | 業務イベント、担い手、前提、結果、確からしさの台帳 |
| コア・支援・汎用の境界が曖昧 | `core-domain` | コアと実装上の関心を分けた境界 |
| 何がUser Journeyで何がJourneyでないかを分けたい | `user-journey` | 目的、両端、意味ある場面、状態の受け渡しを持つJourney map |
| コアドメインの正本を初めて作る | `domain-bdd-discovery` | 代表BDDを含むdomain-rule資料 |
| 既存のdomain-ruleへ境界例や拒否条件を足す | `domain-bdd-formulation` | 反証を反映した更新済みdomain-rule資料 |
| ユーザー目的達成BDDの正本を初めて作る | `user-journey-bdd-discovery` | 複数場面を接続した最初のユーザー目的達成BDD正本 |
| 既存のユーザー目的達成BDDを反証する | `user-journey-bdd-formulation` | 分岐・中断再開・役割移譲を戻した同一パスの正本 |
| 作成・更新・削除に関係する業務断面を先に整理する | `persistence-scenarios` | 永続化対象を判断できる業務シナリオ |
| 業務シナリオから論理データモデルを設計する | `data-model` | BDDと対応したRDB論理データモデル |
| 永続化の発見から論理設計まで初めて通す | `data-model-bdd-discovery` | 検査済みBDD付きRDB論理設計 |
| 既存のBDD付き論理設計を反証し、物理設計まで進める | `data-model-bdd-formulation` | 更新済み論理設計と対象RDBの物理設計 |
| 論理構造は確定済みで、PostgreSQLなどへ写したい | `rdb-design` | 対象製品・版に基づく型、制約、index、分離性の設計 |

## 代表的なユースケース

### 新しい業務ルールを整理する

**業務イベントも境界も曖昧なら`domain-bdd-discovery`を使う。** たとえば「キャンセルできる」という言葉だけがある場合、誰が、どの状態で、何を起こし、どの条件なら受理または拒否されるかまで具体化する。

```text
予約取消の業務知識を、代表BDDを含むコアドメイン資料として初めて整理して。
```

### 既存BDDの抜けを探す

**正本がすでにあり、境界値や競合時の判断を深めるなら`domain-bdd-formulation`を使う。** 正常系を別資料へ作り直さず、反証結果を同じ正本へ戻す。

```text
既存の予約取消domain-ruleを反証し、締切時刻ちょうどと二重取消のシナリオを検査して。
```

### 業務からDB設計へ進む

**何を記録するか未確定なら`data-model-bdd-discovery`を使う。** すでに論理テーブルが確定していて、PostgreSQL 18でのindexや分離レベルだけを決めるなら`rdb-design`を使う。

```text
注文確定・取消・返金の業務シナリオから、BDD付きRDB論理データモデルを作って。
```

### ユーザーの目的達成を一続きにする

**最初に`user-journey`で何がJourneyで何がJourneyでないかを分ける。** 複数の意味ある場面が状態を受け渡し、観測可能な完了へ進む場合だけJourneyとして扱う。対象システム一つの責任ならユースケース、感情と接点ならUX Journey map、業務判断ならdomain、残す事実ならdata modelへ分ける。

最初の正本には`user-journey-bdd-discovery`、既存正本の反証には`user-journey-bdd-formulation`を使う。

```text
初回訪問者が商品を比較し、購入し、受取を確認するまでを、最初のユーザー目的達成BDD正本として発見して。
```

## インストール

### Codex

Codexのpluginコマンドには`--scope`がない。通常の手順はuser単位でmarketplaceとpluginを登録する。

```bash
codex plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins
codex plugin add domain-bdd-discovery@bdd-discovery-and-formulation
codex plugin add domain-bdd-formulation@bdd-discovery-and-formulation
codex plugin add data-model-bdd-discovery@bdd-discovery-and-formulation
codex plugin add data-model-bdd-formulation@bdd-discovery-and-formulation
codex plugin add user-journey-bdd-discovery@bdd-discovery-and-formulation
codex plugin add user-journey-bdd-formulation@bdd-discovery-and-formulation
codex plugin add domain-events@bdd-discovery-and-formulation
codex plugin add core-domain@bdd-discovery-and-formulation
codex plugin add user-journey@bdd-discovery-and-formulation
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
codex plugin add user-journey-bdd-discovery@bdd-discovery-and-formulation
codex plugin add user-journey-bdd-formulation@bdd-discovery-and-formulation
codex plugin add domain-events@bdd-discovery-and-formulation
codex plugin add core-domain@bdd-discovery-and-formulation
codex plugin add user-journey@bdd-discovery-and-formulation
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
claude plugin install user-journey-bdd-discovery@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install user-journey-bdd-formulation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install domain-events@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install core-domain@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install user-journey@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install persistence-scenarios@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install data-model@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install rdb-design@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
```

## 配布するplugin

- 入口: `domain-bdd-discovery`、`domain-bdd-formulation`、`data-model-bdd-discovery`、`data-model-bdd-formulation`、`user-journey-bdd-discovery`、`user-journey-bdd-formulation`
- 下段: `domain-events`、`core-domain`、`user-journey`、`persistence-scenarios`、`data-model`、`rdb-design`。中間生成物の後片付けは外部の `write-doc-cleanup@write-doc` を使う。

`user-journey`はUser Journeyの該当・非該当を判定する。`user-journey-bdd-discovery`は最初の正本を作り、`user-journey-bdd-formulation`は既存正本を同じパスへ深化する。いずれもユースケース、UX Journey map、domain-rule、data model、画面・API・テスト実行環境を混ぜない。

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
