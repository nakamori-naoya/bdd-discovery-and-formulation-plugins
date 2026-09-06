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

## 公開入口を選ぶ

次の入口から依頼します。内部のスキルや処理は、入口が必要に応じて呼び出します。

| 今の状況 | 公開入口 | 得られるもの |
|---|---|---|
| コアドメインの正本を初めて作る | `discover-domain` | 代表BDDを含むdomain-rule資料 |
| 既存のdomain-ruleへ境界例や拒否条件を足す | `formulate-domain` | 反証を反映した更新済みdomain-rule資料 |
| ユーザー目的達成BDDの正本を初めて作る | `discover-user-journey` | 複数場面を接続した最初のユーザー目的達成BDD正本 |
| 既存のユーザー目的達成BDDを反証する | `formulate-user-journey` | 分岐・中断再開・役割移譲を戻した同一パスの正本 |
| 永続化の発見から論理設計まで初めて通す | `discover-data-model` | 検査済みBDD付きRDB論理設計 |
| 既存のBDD付き論理設計を反証し、物理設計まで進める | `formulate-data-model` | 更新済み論理設計と対象RDBの物理設計 |

## 代表的なユースケース

### 新しい業務ルールを整理する

**業務イベントも境界も曖昧なら`discover-domain`を使う。** たとえば「キャンセルできる」という言葉だけがある場合、誰が、どの状態で、何を起こし、どの条件なら受理または拒否されるかまで具体化する。

```text
予約取消の業務知識を、代表BDDを含むコアドメイン資料として初めて整理して。
```

### 既存BDDの抜けを探す

**正本がすでにあり、境界値や競合時の判断を深めるなら`formulate-domain`を使う。** 正常系を別資料へ作り直さず、反証結果を同じ正本へ戻す。

```text
既存の予約取消domain-ruleを反証し、締切時刻ちょうどと二重取消のシナリオを検査して。
```

### 業務からDB設計へ進む

**何を記録するか未確定なら`discover-data-model`を使う。** 既存の論理設計から物理設計へ進める場合は`formulate-data-model`を使う。

```text
注文確定・取消・返金の業務シナリオから、BDD付きRDB論理データモデルを作って。
```

### ユーザーの目的達成を一続きにする

**ユーザー目的達成の入口では、最初に何がJourneyで何がJourneyでないかを分ける。** 複数の意味ある場面が状態を受け渡し、観測可能な完了へ進む場合だけJourneyとして扱う。対象システム一つの責任ならユースケース、感情と接点ならUX Journey map、業務判断ならdomain、残す事実ならdata modelへ分ける。

最初の正本には`discover-user-journey`、既存正本の反証には`formulate-user-journey`を使う。

```text
初回訪問者が商品を比較し、購入し、受取を確認するまでを、最初のユーザー目的達成BDD正本として発見して。
```

## インストール

インストールするのは`bdd-discovery-and-formulation@bdd-discovery-and-formulation`です。外部の工程を実行するため、`grill@grill`、`write-doc@write-doc`も必要です。下のコマンドには、それらも含めています。

内部のスキルは同梱されています。個別にインストールせず、公開入口から利用してください。

### Codex

利用するCodexと同じ設定環境で実行してください。

```bash
codex plugin marketplace add nakamori-naoya/grill-plugins
codex plugin add grill@grill
codex plugin marketplace add nakamori-naoya/write-doc-plugins
codex plugin add write-doc@write-doc
codex plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins
codex plugin add bdd-discovery-and-formulation@bdd-discovery-and-formulation
codex plugin list
```

一覧で導入先を確認し、新しい会話で利用してください。

### Claude Code

次は自分の全プロジェクトで使う例です。このプロジェクトのチームで共有する場合は`project`、このプロジェクトで自分だけが使う場合は`local`に変更し、利用先のディレクトリで実行してください。

```bash
CLAUDE_PLUGIN_SCOPE=user
claude plugin marketplace add nakamori-naoya/grill-plugins --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install grill@grill --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin marketplace add nakamori-naoya/write-doc-plugins --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install write-doc@write-doc --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin marketplace add nakamori-naoya/bdd-discovery-and-formulation-plugins --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin install bdd-discovery-and-formulation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin list
```

一覧で導入を確認し、Claude Codeを再起動してください。すでに導入しているパッケージは、次の更新手順を使ってください。

## 更新する

GitHubから登録したmarketplaceを更新し、その公開パッケージを更新します。新規インストールと同じCodexの設定環境、Claude Codeの適用範囲を使ってください。

### Codex

```bash
codex plugin marketplace upgrade bdd-discovery-and-formulation
codex plugin add bdd-discovery-and-formulation@bdd-discovery-and-formulation
codex plugin list
```

更新後は新しい会話で確認してください。ローカルのパスからmarketplaceを登録した場合は、Git版の更新コマンドではなく、その登録先のソースを更新してから追加し直します。

### Claude Code

```bash
# インストール時に合わせてuser / project / localを選ぶ
CLAUDE_PLUGIN_SCOPE=user
claude plugin marketplace update bdd-discovery-and-formulation
claude plugin update bdd-discovery-and-formulation@bdd-discovery-and-formulation --scope "$CLAUDE_PLUGIN_SCOPE"
claude plugin list
```

更新後はClaude Codeを再起動してください。外部の依存パッケージも使っている場合は、それぞれのREADMEの更新手順を実行してください。

marketplaceの取得と、インストール済みパッケージの更新は分けて確認します。同じバージョンとして公開された変更は、更新コマンドだけでは反映されない場合があります。「最新」と表示された場合は公開バージョンを確認し、キャッシュ内のファイルを直接編集しないでください。

コマンドは2026-09-06時点のCLIヘルプと、[Codexのmarketplace管理](https://developers.openai.com/plugins/build/plugins)、[Claude Codeの更新仕様](https://code.claude.com/docs/en/plugins-reference#plugin-update)を確認しています。

## 公開インストール単位と内包する機能

利用者がインストールするのは`bdd-discovery-and-formulation@bdd-discovery-and-formulation`だけである。6つのplaybookと、その実行に使う`domain-events`、`core-domain`、`user-journey`、`persistence-scenarios`、`data-model`、`rdb-design`は同じpackageへ内包する。内部機能をmarketplaceの個別インストール対象にはしない。中間生成物の後片付けは、各playbookが自分の`scripts/cleanup.py`で行う。外部packageの後片付け機能へ委譲しない。

`user-journey`はUser Journeyの該当・非該当を判定する。`discover-user-journey`は最初の正本を作り、`formulate-user-journey`は既存正本を同じパスへ深化する。いずれもユースケース、UX Journey map、domain-rule、data model、画面・API・テスト実行環境を混ぜない。

各入口では、`playbook.yml`が工程順・依存・入出力という決定的な契約を持ち、`references/execution-guidance.md`が背景・前提・目的と各工程実行時の付加的な指示を持つ。`grill`へdomainやdata model固有の文脈を与えるのは後者であり、相手へ観点を持ち込まない。

外部の段取り（`grill`、`write-doc`）は、`references/nested-playbook.md`に書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。差し替えは利用者が`dependencies.yml`で契約IDへ実体を束縛して行う。

## インストール済みである必要があるplugin

このrepository外の依存だけを記載する。利用する工程に応じて、次がインストール済みである必要がある。

- `grill@grill`
- `write-doc@write-doc`

外部依存は公開playbook packageの`marketplace / plugin / runtime`で解決し、versionは固定しない。install済みcacheに複数versionがあれば最新のsemantic versionを選び、そのmanifestのpackage名と、`metadata.harness.implements`が宣言する契約IDを検査する。契約を宣言していない実体、外部packageの内部機能名は解決しない。名前が一致する公開packageが無ければ停止する。開発時だけ`HARNESS_PLUGIN_DEV_ROOTS`の明示mapでsource checkoutを指定できる。

利用者は`~/.config/harness-plugins/dependencies.yml`、`<repo>/.harness-plugins/dependencies.yml`、`<repo>/.harness-plugins/scopes/<入口playbook>/dependencies.yml`で、契約ID（`grill/grill`、`write-doc/write-doc`）へ別の実体を束縛できる。playbook側の`requires`は変えない。

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

構造、旧cleanup配布物がないこと、両runtimeのcache・repository・明示dev-mapによる依存解決、契約の未宣言、依存欠落、manifest版違い、runtime不明、bare依存名の拒否を検査する。

さらに、fixtureだけで緑になる状態を許さないために、**実際に配布されている依存先package**（兄弟checkoutの`../grill-plugins/plugins`と`../write-doc-plugins/plugins`）に対する解決と、消費側lintを両runtimeで実行する。実配布物が見つからなければこの検査は落ちる。契約ID→package rootのJSONを`HARNESS_PLUGIN_REAL_ROOTS`で渡すこともできる。

install cacheは編集せず、このrepositoryを正本として変更する。

## 実行契約と保守

設定はprepareが返すrun専用の絶対pathで引き継ぐ。別shellで同じpathを明示し、完了・失敗停止の最後に同梱run-configのcleanupを呼ぶ。中断後は保存したpathを使い、既にcleanup済みなら設定を再解決する。

依存宣言のversionは固定しない。対応する実行契約は`contractVersion: 1`で、未宣言の旧fixtureは契約1として扱う。未知の契約版は拒否する。installed cacheでは安定版の最大SemVerを選び、prereleaseは`HARNESS_PLUGIN_ALLOW_PRERELEASE=1`を明示した場合だけ候補にする。解決したversion、内容hash、契約版を記録し、工程直前とwrite-doc再開時に内容変更を拒否する。

[doctor](scripts/doctor.py)は`python3 scripts/doctor.py --repo <対象project>`でCLI構文、両runtime公開入口、依存、設定の解決元を読み取り専用で診断する。`--distribution-only`は依存・project設定を検査しない限定診断であり、full診断の代用にはしない。

共通実装の開発時正本はProduct Planning repositoryの`shared/runtime-source`にある。更新時はそのsource checkoutを取得し、[生成CLI](scripts/sync-runtime.py)へ`--source <取得した正本directory>`を渡す。`--check`は生成差分と[生成履歴](shared/runtime-manifest.json)のversion・内容hash・対象集合を検査する。正本checkoutなしのCIでも同梱物のhashと対象集合を検査できる。実行時に別repositoryや生成CLIは不要である。変更は正本へ加え、同じ生成コマンドを各source repositoryへ適用する。

[release CLI](scripts/release.py)は`--plugin --version --notes --breaking --migration --checks`で更新計画を返す。`--checks`にはcodex/claudeの実検証結果、または未検証と理由を明示する。`--apply`で両manifestとcatalogの整合を確認して一括更新し、releases配下へ変更内容・移行・検証結果のJSON記録を残す。依存宣言は変更しない。

[意味評価fixture](evals/scenarios.json)を[評価runner](scripts/evaluate-skills.py)へ渡し、異なる生成modelとjudge modelを指定する。モデル名、実model利用、適用設定、入力、出力、SKILL hash、判定の引用と理由を保存する。これはツール無効の次応答を対象とした代表caseの意味評価であり、実ツールを使った全工程E2Eや全行動の保証ではない。保存・CLI・再開の検証は[振る舞い回帰試験](scripts/test-hardening.py)と既存validateが担う。実モデル未実行のfixtureを合格扱いにしない。

### 依存先を束縛する`dependencies.yml`

契約ID（`marketplace/plugin`）に対する実体を`{plugin, marketplace}`で束縛する。**top-levelは`version: 1`と`bindings`の2つだけである。** それ以外のキーがあると`[error:binding-file-invalid] reason=top-level-keys`で停止する。

```yaml
version: 1
bindings:
  "grill/grill": {plugin: ask-one, marketplace: my-marketplace}
  "write-doc/write-doc": {plugin: write-documents, marketplace: my-marketplace}
```

置き場所は3層で、下ほど優先する。**層はマージせず、見つかった最優先の1ファイルだけを使う。**

1. personal: `$XDG_CONFIG_HOME/harness-plugins/dependencies.yml`（未設定時は`~/.config/harness-plugins/dependencies.yml`）
2. repository: `<repo>/.harness-plugins/dependencies.yml`
3. scope: `<repo>/.harness-plugins/scopes/<入口playbook>/dependencies.yml`

値に書けるのは`plugin`と`marketplace`だけで、**pathやversionは書けない。** 差し替え先はmarketplace経由（installed cache、同一repository、開発時の`HARNESS_PLUGIN_DEV_ROOTS`）で解決でき、manifestの`metadata.harness.implements`にその契約IDを宣言しているpluginでなければならない。宣言が無ければ`[error:binding-not-implemented]`で停止する。playbook側の`requires`は書き換えない。

入口が選んだ束縛はrun専用のlockへ固定して子へ渡す。同じ実行の中で実体が食い違うことはなく、実行中に`dependencies.yml`を書き換えても、そのrunの解決は変わらない。

### explainの読み方

`scripts/prepare.sh`は`--explain`を引数に取らない。**explainは常にstderrへ出る。** stdoutは解決済みYAMLの絶対path1行だけなので、解決の内訳（選んだ設定層、依存の実体、束縛の出どころ、静的に解けた工程入力）はstderrで読む。`--explain`のような未知optionを渡すとusageを表示してexit 2で止まる。

### 破壊的変更の移行

重複した薄いSKILL入口を廃止した。利用者は公開manifestに列挙された入口を使い、旧入口pathを保存した独自ランチャーは新しい宣言へ切り替える。設定のEXIT trapは廃止し、返されたrun pathを明示して完了・停止時にcleanupする。旧式の一時pathやshell変数だけを再利用しない。

### 開発CLIの入力境界

`doctor`、`release`、`sync-runtime`、意味評価runnerは、操作者が明示したローカルsource、出力先、adapter argvを扱う開発CLIである。外部から受け取った文書やモデル出力をCLI引数へ自動変換しない。doctorのfull modeは選んだrepositoryのresolverを実行するため、信頼するsource checkoutを対象にする。doctorは配布treeのsymlinkを読取・実行前に拒否し、sync-runtimeは生成先と正本treeのsymlinkをcopy前に拒否する。評価の会話・fixture・モデル出力はadapterへstdinデータとして渡し、実行argvに混ぜない。
