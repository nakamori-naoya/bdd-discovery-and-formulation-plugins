# BDD Discovery and Formulation

BDDを使ってドメイン理解とRDBデータモデリングを探索・反証し、User Journeyを線引きしてユーザー目的達成BDDを発見・深化する、Claude Code/Codex両対応のmarketplaceである。公開入口は7つで、1つのpackage `bdd-discovery-and-formulation` に同梱する。

## BDDを使う場面

**業務上の正しさを、具体的な事前状態・出来事・判断・結果で共有したいときに使う。** 実装方法やテストコードを先に決めるためではなく、関係者が同じ例を見て同じ結論へ到達できる状態を作る。

- 人によって業務ルールの説明が違う
- 正常系は分かるが、境界値や拒否条件が決まっていない
- 画面やAPIの話が先行し、何を守る業務なのか説明できない
- DBへ何を残すべきか、業務上の根拠から決めたい
- 個別機能は説明できるが、ユーザーが目的を達成する一連の流れがつながらない

DiscoveryとFormulationは、資料の有無ではなく仕事の目的で選ぶ。断片的な資料や同種の既存資料があっても、業務イベント、役割、判断、場面、または残す事実を探索して新しい共通理解を作るならDiscoveryを使う。指定した既存正本の主張へ反例を当て、確認した結果を同じpathへ戻すならFormulationを使う。

## 公開入口を選ぶ

次の入口から依頼します。内部skillは入口の`playbook.yml`が必要な工程で呼び出します。保存先は依頼で示すか、示されなければ入口が既存資料の構成を読んで一度だけ提案します。

| 今の状況 | 公開入口 | 得られるもの |
|---|---|---|
| 資料の有無にかかわらず、コアドメインの未知を探索して正本を作る | `discover-domain` | 代表BDDを含むdomain-rule資料 |
| 既存のdomain-ruleへ境界例や拒否条件を足す | `formulate-domain` | 反証を反映した更新済みdomain-rule資料 |
| 資料の有無にかかわらず、ユーザー目的達成の連続性を探索して正本を作る | `discover-user-journey` | 複数場面を接続したユーザー目的達成BDD正本 |
| 既存のユーザー目的達成BDDを反証する | `formulate-user-journey` | 分岐・中断再開・役割移譲を戻した同一パスの正本 |
| 資料の有無にかかわらず、残す事実を探索して論理設計まで通す | `discover-data-model` | 検査済みBDD付きRDB論理設計 |
| 既存のBDD付き論理設計を反証し、物理設計まで進める | `formulate-data-model` | 更新済み論理設計と、依頼で指定したRDB製品・版の物理設計 |
| 対応する業務知識を根拠に複数の既存論理設計を横断改訂する | `revise-data-models` | 正本選択とリソース系／イベント系分類を揃えた同一pathの論理設計群 |

## 代表的なユースケース

### 新しい業務ルールを整理する

**業務イベントも境界も曖昧なら`discover-domain`を使う。** たとえば「キャンセルできる」という言葉だけがある場合、誰が、どの状態で、何を起こし、どの条件なら受理または拒否されるかまで具体化する。

```text
既存の用語集と要件資料を根拠に、予約取消の未知の業務イベントと判断を探索し、代表BDDを含む新しいコアドメイン資料として整理して。
```

### 既存BDDの抜けを探す

**正本がすでにあり、境界値や競合時の判断を深めるなら`formulate-domain`を使う。** 正常系を別資料へ作り直さず、反証結果を同じ正本へ戻す。

```text
既存の予約取消domain-ruleを反証し、締切時刻ちょうどと二重取消のシナリオを検査して。
```

### 業務からDB設計へ進む

**何を記録するか未確定なら、既存の論理設計や関連資料があっても`discover-data-model`を使う。** 対応する業務知識資料が必須であり、無ければ先に`discover-domain`で業務知識を作る。指定した既存論理設計を反証して同じpathへ戻し、物理設計へ進める場合は`formulate-data-model`、複数の既存論理設計を同じ業務知識から横断改訂する場合は`revise-data-models`を使う。

イベント列は既定ではない。業務知識から複数の意味ある業務イベントと、順序・履歴・取消・訂正を後から使う必要が読めるときに候補にする。イベントが無いか乏しく履歴を使わない場合は現在状態、設定や契約条件の過去時点の値を使う場合は有効期間履歴を候補にする。

```text
注文確定・取消・返金の業務シナリオから、BDD付きRDB論理データモデルを作って。
```

### ユーザーの目的達成を一続きにする

**ユーザー目的達成の入口では、最初に何がJourneyで何がJourneyでないかを分ける。** 複数の意味ある場面が状態を受け渡し、観測可能な完了へ進む場合だけJourneyとして扱う。対象システム一つの責任ならユースケース、感情と接点ならUX Journey map、業務判断ならdomain、残す事実ならdata modelへ分ける。

目的達成の連続性を探索して新しい正本を作るなら、関連するJourney資料があっても`discover-user-journey`を使う。指定した既存正本を反証して同じpathへ戻すなら`formulate-user-journey`を使う。

```text
既存の画面案と別目的のJourneyを根拠に、初回訪問者が商品を比較し、購入し、受取を確認するまでを、新しいユーザー目的達成BDD正本として発見して。
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

利用者がインストールするのは`bdd-discovery-and-formulation@bdd-discovery-and-formulation`だけである。packageは`plugins/bdd-discovery-and-formulation/`にあり、公開入口7つを`skills/<entry>/`に、2つ以上の公開入口が共有する判断規律を内部skillとして`internal/<name>/`に持つ。

| 内部skill | 共有する公開入口 | 担う判断 |
|---|---|---|
| `explore-events` | discover-domain、discover-data-model | 業務で起きた事実を時系列に洗い出す |
| `map-user-journey` | discover-user-journey、formulate-user-journey | 何がJourneyで何がJourneyでないかを判定し、両端と場面を決める |
| `write-persistence-scenarios` | discover-data-model、formulate-data-model | 作成・更新・削除に関係する断面を永続化シナリオにする |
| `design-data-model` | discover-data-model、formulate-data-model、revise-data-models | 対応する業務知識から記録すべき事実と正本を選び、BDD付きの論理設計本文を作る。手法は`fact-recording` / `normalized` / `dimensional`、または利用者の手法file |
| `write-bdd` | 7入口すべて（同梱skillも適用する） | 入力の根拠づけ、業務の言葉（役割、業務イベント、ユビキタス言語）、BDDの前提・トリガー・失敗理由と条件マトリクス、定式化へ進める見極め、QA観点、`grill` / `write-doc`の呼び方という共通規律。成果物は作らず、各入口が手順に入る前に読んで全工程へ適用する |

内部skillはmarketplaceの個別インストール対象にせず、公開入口の`playbook.yml`が`skill:`工程で呼ぶか、`write-bdd`のように入口の`SKILL.md`が手順に入る前に読んで全工程へ適用する。1つの公開入口だけが使っていた判断（コア・支援・汎用の線引き、RDB物理設計）はその公開入口へ統合した。

各公開入口では、`playbook.yml`が工程順・依存・入出力という決定的な契約を持ち、`SKILL.md`が目的・入力・判断基準・手順・停止条件・出力を持ち、`references/execution-guidance.md`が背景・前提と各工程実行時の付加的な指示を持つ。入口が使うtool（`scripts/scenario.py`、`scripts/scenario_matrix.py`、`scripts/actor-coverage.py`、`scripts/update-guard.py`、`scripts/rdb.py`）は、入口directoryを基準にした相対pathで示し、入力・出力・終了code・失敗時の扱いをSKILL.mdの手順が1か所で宣言する。agentが作った本文（条件マトリクス、BDD草案、場面草案、完成本文、物理設計本文）はそのまま標準入力で渡し、条件マトリクスを併せて渡すtoolは`--matrix-json`引数で受け、保存済みの正本だけをpath引数で渡す。検査のためだけの一時fileや後片付け工程は無い。停止条件は「止まる（必須入力の欠落、契約に反する入力、toolの失敗、保存先の不確定）」と「仮説を明示して進む（判断の揺れ、資料の不足）」に分かれる。設定fileは持たず、保存先、対象RDB、論理モデリングの手法は依頼と対話から決める。

外部の段取り（`grill`、`write-doc`）は、内部skill `write-bdd`の`references/nested-playbook.md`に1か所で書いた入口・入力・出力だけで呼ぶ。`write-doc/write-doc`は版2を使い、型付き`material`と明示した保存先を直接渡す。新規作成には`output_directory`と`.md`の`name`、既存更新には`update_target`だけを渡す。`grill/grill`版1は契約objectを公開入口へ直接渡し、`decisions`と`open_questions`を持つ結果objectを直接受け取る。渡す`questions`は成果を左右する順に厳選し、対話の作法と問う数の上限は`grill`の公開契約に従う。上限で問われなかった論点は、返った`open_questions`の推奨を仮置きした未決として成果物へ載せる。各入口は任意入力`references`（追加で従う資料の絶対path配列）を持ち、手順の最初に読む。

資料のtemplateはこのrepositoryに無い。各入口は本文を`kind: text`で組み立て、`write-doc`の`document_type`（`domain-rule` / `user-journey-bdd` / `rdb-logical-data-modeling` / `rdb-physical-design`）で保存する。節構成と記法はwrite-docが所有するtemplateが定め、この入口のtool（`actor-coverage.py`、`scenario.py`、`rdb.py`）が読む見出しと欄は、そのtemplateが機械検査の記法として宣言する。参照資料は1か所にだけ置き、入口間で複製しない。

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

`validate-structure.sh`は、両marketplaceと両runtime manifestのidentity、公開入口7つと内部skill5つの集合、`playbook.yml`の外部依存宣言と`script:` / `skill:`参照の実在、入口ごとの`scripts/`に置く同名toolのbyte一致、参照資料（`references/*.md`）がpackage内で1か所にだけあること、禁止参照形の不在を検査し、各tool（業務知識入力、データモデル構造、条件マトリクス、Gherkin検査、誰が行えるかの網羅、ユーザー目的達成BDD、同一パス更新、物理設計検査）の`self-test`またはfixture（旧引数のargparse拒否を含む）を実行する。データモデルの境界fixtureは、状態列・完了日時・削除フラグ・条件付きNULLを意味評価へ残し、それらの語だけで機械的に拒否しないことも確認する。続けて兄弟checkout `../harness-tools/tools/`の保守tool（root契約の`validate-plugin-repository.py`とその`--self-test`、回帰検査の`test-hardening.py --repository`）と、兄弟checkout（`../grill-plugins/plugins/grill`、`../write-doc-plugins/plugins/write-doc`）の実配布物に対する消費側lint（`lint-consumer-contract.py --repo --runtime`）を両runtimeで実行する。`../harness-tools/`が無ければexit 2で止まり、実配布物が見つからなければ落ちる。

workspace rootの`bash scripts/validate.sh <このrepositoryの絶対path>`が配置・manifest・隣接playbook.yml・禁止参照形の構造契約を検査する。構造検査の成功は、SKILL本文の判断規律や生成された資料の業務上の正しさを保証しない。

install cacheは編集せず、このrepositoryを正本として変更する。

## repository保守用tool

以下はsource repository自体の配布検証と保守の説明であり、公開入口が`grill`または`write-doc`を呼ぶ手順ではない。公開入口は設定解決runtimeを持たず、公開契約objectと直接結果だけを扱う。

保守toolの正本は兄弟checkout`../harness-tools/`（同ownerの`harness-tools` repository）であり、このrepositoryは複製も同期機構も持たない。呼び方はharness-toolsのREADME「各repositoryからの呼び方」に従い、対象repositoryは絶対pathの引数で渡す。

- 診断: `python3 ../harness-tools/tools/doctor.py --repository <このrepositoryの絶対path>`は、CLIの有無、両runtime公開入口、全公開入口の外部依存を兄弟checkoutの実配布物に対して解決する読み取り専用診断を返す。
- リリース: `python3 ../harness-tools/tools/release.py --repo <このrepositoryの絶対path> --plugin bdd-discovery-and-formulation --version <semver> --notes … --breaking … --migration … --checks <JSON> [--apply]`が両marketplaceと両runtime manifestのversionを同時に更新し、`releases/<plugin>-<version>.json`を書く。
- eval: [意味評価fixture](evals/scenarios.json)は`bash ../harness-tools/scripts/run-evals.sh --model … --judge-model … <このrepositoryの絶対path>`で実行し、`evals/runs/<日付>/`へ記録する。モデルを更新したときにlocalで手動実行し、前回の記録と読み比べる（読み比べはagentの意味評価）。criterionの真偽は記録であり、CLIの合否にはしない。

CIは`.github/workflows/validate.yml`が自repositoryを`<workspace>/<自分の名前>`に、`harness-tools`と依存provider（`grill-plugins`、`write-doc-plugins`）を`ref: main`で兄弟checkoutし、`bash harness-tools/ci/validate.sh "$GITHUB_WORKSPACE/<自分の名前>"`を呼ぶ。実行されるcommandはlocalの`scripts/validate.sh`と同じである。PR由来のrefを依存checkoutへ渡さない。

### 破壊的変更

公開入口を`plugins/bdd-discovery-and-formulation/skills/<entry>/`へ、内部skillを`internal/<name>/`へ移し、入口ごとのnested manifest、設定file（`<repo>/.harness-plugins/<entry>.config.yml`と同梱既定）、`prepare.sh` / `resolve.sh`による設定解決、`${.…}`マクロ、台帳scriptを廃止した。旧pathや設定fileを前提にした独自ランチャーは、公開manifestに列挙された入口と、SKILL.mdが宣言する入力へ切り替える。

### 開発CLIの入力境界

`doctor`、`release`、意味評価runnerは、操作者が明示したローカルsource、出力先、adapter argvを扱う開発CLIである。外部から受け取った文書やモデル出力をCLI引数へ自動変換しない。doctorは配布treeのsymlinkを読取・実行前に拒否する。評価の会話・fixture・モデル出力はadapterへstdinデータとして渡し、実行argvに混ぜない。各CLIの契約と自己検査はharness-toolsが持つ。
