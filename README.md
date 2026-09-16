# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証し、User Journeyを線引きしてユーザー目的達成BDDを発見・深化する、Claude Code/Codex両対応のmarketplaceである。公開入口は6つで、1つのpackage `bdd-discovery-and-formulation` に同梱する。

## BDDを使う場面

**業務上の正しさを、具体的な事前状態・出来事・判断・結果で共有したいときに使う。** 実装方法やテストコードを先に決めるためではなく、関係者が同じ例を見て同じ結論へ到達できる状態を作る。

- 人によって業務ルールの説明が違う
- 正常系は分かるが、境界値や拒否条件が決まっていない
- 画面やAPIの話が先行し、何を守る業務なのか説明できない
- DBへ何を残すべきか、業務上の根拠から決めたい
- 個別機能は説明できるが、ユーザーが目的を達成する一連の流れがつながらない

既存資料も業務シナリオもない状態で、いきなりFormulationから始めない。最初の正本を作る場合はDiscoveryを使い、既存の正本を反証して更新する場合にFormulationを使う。

## 公開入口を選ぶ

次の入口から依頼します。内部skillは入口の`playbook.yml`が必要な工程で呼び出します。保存先は依頼で示すか、示されなければ入口が既存資料の構成を読んで一度だけ提案します。

| 今の状況 | 公開入口 | 得られるもの |
|---|---|---|
| コアドメインの正本を初めて作る | `discover-domain` | 代表BDDを含むdomain-rule資料 |
| 既存のdomain-ruleへ境界例や拒否条件を足す | `formulate-domain` | 反証を反映した更新済みdomain-rule資料 |
| ユーザー目的達成BDDの正本を初めて作る | `discover-user-journey` | 複数場面を接続した最初のユーザー目的達成BDD正本 |
| 既存のユーザー目的達成BDDを反証する | `formulate-user-journey` | 分岐・中断再開・役割移譲を戻した同一パスの正本 |
| 永続化の発見から論理設計まで初めて通す | `discover-data-model` | 検査済みBDD付きRDB論理設計 |
| 既存のBDD付き論理設計を反証し、物理設計まで進める | `formulate-data-model` | 更新済み論理設計と、依頼で指定したRDB製品・版の物理設計 |

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

内部skillは同梱されています。個別にインストールせず、公開入口から利用してください。

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

利用者がインストールするのは`bdd-discovery-and-formulation@bdd-discovery-and-formulation`だけである。packageは`plugins/bdd-discovery-and-formulation/`にあり、公開入口6つを`skills/<entry>/`に、2つ以上の公開入口が共有する判断規律を内部skillとして`internal/<name>/`に持つ。

| 内部skill | 共有する公開入口 | 担う判断 |
|---|---|---|
| `explore-events` | discover-domain、discover-data-model | 業務で起きた事実を時系列に洗い出す |
| `map-user-journey` | discover-user-journey、formulate-user-journey | 何がJourneyで何がJourneyでないかを判定し、両端と場面を決める |
| `write-persistence-scenarios` | discover-data-model、formulate-data-model | 作成・更新・削除に関係する断面を永続化シナリオにする |
| `design-data-model` | discover-data-model、formulate-data-model | 記録すべき事実を先に決め、BDD付きの論理設計本文を作る。手法は`fact-recording` / `normalized` / `dimensional`、または利用者の手法file |

内部skillはmarketplaceの個別インストール対象にせず、公開入口の`playbook.yml`が`skill:`工程で呼ぶ。1つの公開入口だけが使っていた判断（コア・支援・汎用の線引き、RDB物理設計）はその公開入口へ統合した。

各公開入口では、`playbook.yml`が工程順・依存・入出力という決定的な契約を持ち、`SKILL.md`が目的・入力・判断基準・手順・停止条件・出力を持ち、`references/execution-guidance.md`が背景・前提と各工程実行時の付加的な指示を持つ。入口が使うtool（`scripts/scenario.py`、`scripts/scenario_matrix.py`、`scripts/actor-coverage.py`、`scripts/update-guard.py`、`scripts/rdb.py`）は、入口directoryを基準にした相対pathで示し、入力・出力・終了code・失敗時の扱いをSKILL.mdが宣言する。設定fileは持たず、保存先、対象RDB、論理モデリングの手法は依頼と対話から決める。

外部の段取り（`grill`、`write-doc`）は、`references/nested-playbook.md`に書いた入口・入力・出力だけで呼ぶ。`write-doc/write-doc`は版2を使い、型付き`material`と明示した保存先を直接渡す。新規作成には`output_directory`と`.md`の`name`、既存更新には`update_target`だけを渡す。`grill/grill`版1は契約objectを公開入口へ直接渡し、`decisions`と`open_questions`を持つ結果objectを直接受け取る。

ハーネスが作る資料は、冒頭を読み手の既知の語で書いた本文段落から始め、型や確認日のようなメタ情報の一覧を置かない。中心の問い、扱う理由、役割×目的の一覧、Journeyから外した事項の送り先のような作業記録は報告に載せ、正本へ写さない。保存先と名前は利用者の既存資料構成に従い、日本語のdirectory名・file名を許す。

## インストール済みである必要があるplugin

このrepository外の依存だけを記載する。利用する工程に応じて、次がインストール済みである必要がある。

- `grill@grill`
- `write-doc@write-doc`

公開入口は同じagentの利用可能Skill一覧と`requires`を照合する。契約IDと版が異なる、または必要な公開Skillが無い場合は停止する。consumerが依存先のroot、cache、設定、内部pathを探さない。

## 検証

```bash
bash scripts/validate.sh
```

`validate-structure.sh`は、両marketplaceと両runtime manifestのidentity、公開入口6つと内部skill4つの集合、`playbook.yml`の外部依存宣言と`script:` / `skill:`参照の実在、共有複製のbyte一致、禁止参照形の不在を検査し、各tool（条件マトリクス、Gherkin検査、誰が行えるかの網羅、ユーザー目的達成BDD、同一パス更新、物理設計検査）を正例・反例・境界例で実行する。続けて共有保守tool（`test-hardening.py`、`sync-runtime.py --check`、`validate-distribution.py`）と、兄弟checkout（`../grill-plugins/plugins/grill`、`../write-doc-plugins/plugins/write-doc`）の実配布物に対する消費側lint（`lint-consumer-contract.py`）を両runtimeで実行する。実配布物が見つからなければ落ちる。

workspace rootの`bash scripts/validate.sh <このrepositoryの絶対path>`が配置・manifest・隣接playbook.yml・禁止参照形の構造契約を検査する。構造検査の成功は、SKILL本文の判断規律や生成された資料の業務上の正しさを保証しない。

install cacheは編集せず、このrepositoryを正本として変更する。

## repository保守用tool

以下はsource repository自体の配布検証と保守の説明であり、公開入口が`grill`または`write-doc`を呼ぶ手順ではない。公開入口は設定解決runtimeを持たず、公開契約objectと直接結果だけを扱う。

共通実装の開発時正本はProduct Planning repositoryの`shared/runtime-source`にある。更新時はそのsource checkoutを取得し、[生成CLI](scripts/sync-runtime.py)へ`--source <取得した正本directory>`を渡す。`--check`は生成差分と[生成履歴](shared/runtime-manifest.json)のversion・内容hash・対象集合を検査する。同期対象は`.github/workflows/validate.yml`と`scripts/`配下の保守toolであり、配布物（`plugins/`）には複製を置かない。

[doctor](scripts/doctor.py)は`python3 scripts/doctor.py --repo <対象project>`でCLI構文、両runtime公開入口、依存の解決元を読み取り専用で診断する。[release CLI](scripts/release.py)は`--plugin --version --notes --breaking --migration --checks`で更新計画を返し、`--apply`で両manifestとcatalogの整合を確認して一括更新し、releases配下へ記録を残す。[意味評価fixture](evals/scenarios.json)を[評価runner](scripts/evaluate-skills.py)へ渡すと、モデル名、入力、出力、SKILL hash、判定の引用と理由を保存する。criterionの真偽は意味評価の記録であり、CLIの合否にはしない。

CIは同ownerの依存repositoryを兄弟directoryへcheckoutしてからvalidate.shを走らせる。兄弟のrefは既定でmainである。PR headと同名のbranchを採るのは、(1)実行が`pull_request`であり、(2)PR headが同一repository（forkではない）で、(3)同ownerの兄弟repoにその名前のbranchが実在する、の3つが揃うときだけで、選んだrefと理由はログへ出る。code scanningの`actions/untrusted-checkout/medium`はこの根拠により`won't fix`として扱う。

### 破壊的変更

公開入口を`plugins/bdd-discovery-and-formulation/skills/<entry>/`へ、内部skillを`internal/<name>/`へ移し、入口ごとのnested manifest、設定file（`<repo>/.harness-plugins/<entry>.config.yml`と同梱既定）、`prepare.sh` / `resolve.sh`による設定解決、`${.…}`マクロ、台帳scriptを廃止した。旧pathや設定fileを前提にした独自ランチャーは、公開manifestに列挙された入口と、SKILL.mdが宣言する入力へ切り替える。

### 開発CLIの入力境界

`doctor`、`release`、`sync-runtime`、意味評価runnerは、操作者が明示したローカルsource、出力先、adapter argvを扱う開発CLIである。外部から受け取った文書やモデル出力をCLI引数へ自動変換しない。doctorは配布treeのsymlinkを読取・実行前に拒否し、sync-runtimeは生成先と正本treeのsymlinkをcopy前に拒否する。評価の会話・fixture・モデル出力はadapterへstdinデータとして渡し、実行argvに混ぜない。
