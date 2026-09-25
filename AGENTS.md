> 共通の規約は /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/AGENTS.md にある。ここには、この repository だけの規則を置く。

# AGENTS.md

このrepositoryは、BDDによるdiscovery、formulation、User Journeyの意味判断を配布するsourceである。

- 対象はドメインBDD、データモデリングBDD、User Journeyの線引き、ユーザー目的達成BDDに限定する。
- marketplaceへ公開するインストール対象は`bdd-discovery-and-formulation` package 1つである。公開入口は`plugins/bdd-discovery-and-formulation/skills/<entry>/`の7つで、両runtime manifestの`skills`が列挙する。内部skillは2つ以上の公開入口が共有する判断だけを`internal/<name>/`に置き、`internalPlugins`で宣言する。1つの公開入口からしか使わない判断はその入口へ統合する。参照資料（`references/*.md`）は1か所にだけ置き、入口や内部skillへ複製しない。7入口が共有するBDDの記述規律は内部skill `write-bdd`が持ち、各入口は手順に入る前にそれを読んで適用する。
- 公開入口と内部skillは、directory名、`SKILL.md`の`name`、隣接`playbook.yml`の`name`を同じ一つの名前にする。
- `SKILL.md`は目的、入力、判断基準（観察対象と二者択一の述語を肯定形で）、手順、停止条件、出力を持つ。止まるか進むかは、各公開入口の`SKILL.md`の停止条件だけが決める。停止条件は、分からないことがその資料の結論を変えるなら止まって提案し、表し方や細部にとどまるなら仮説を明示して進む、という一つの判断基準を冒頭に置く。内部skillとreferencesは止まるか進むかを決めず、分からないことを仮説・未決・`assumed` / `unknown`として区別して返す。実行基盤の配管（環境変数によるroot解決、設定解決script、`${.…}`マクロ、同期block、「解決済みYAMLを読め」型の指示）を書かない。入口が使うtoolは入口directory基準の相対pathで示し、入力（agentが作った本文は標準入力、保存済みの資料はpath引数）、出力、終了code、失敗時に止まるか回復するかを手順の1か所で宣言する。検査のためだけの一時file、作業directory、後片付け工程を置かない。
- 資料のtemplateを持たない。成果物の節構成と記法は、保存に使う`write-doc`の`document_type`（`domain-rule` / `user-journey-bdd` / `rdb-logical-data-modeling`）をwrite-docが所有するtemplateが定め、このrepositoryのtoolが読む記法はそのtemplateが機械検査の記法として宣言する。
- 設定fileを持たない。保存先（`output_directory` / `name` / `update_target`）と論理モデリングの手法は公開入力で受け取り、既定値を持たない。物理設計、対象RDBの製品・版、Read、index、分離レベル、配置、容量・運用はこのrepositoryの責務外とする。案件固有の役割名、本数、置き場をSKILL・reference・fixtureの既定にしない。
- ハーネスが作る資料の冒頭は読み手の既知の語で書いた本文段落から始め、メタ情報の一覧を置かない。中心の問い、扱う理由、役割×目的の一覧、除外事項の送り先のような作業記録は報告に載せ、資料へ写さない。
- User Journeyは、1人の主たるユーザーの1つの目的について、開始から観測可能な完了までに複数の意味ある場面が状態を受け渡す場合だけ扱う。場面と分岐は主たるユーザーが観測できる振る舞いだけで書き、判定は「この違いが起きたとき、主たるユーザーは何を見て気づくか」である。
- 「誰が行えるか」は成立条件と同じ重さのコアの決まりとして、すべてのコマンドとクエリについて業務知識に書く。判定は「破られたときに困るのは業務か運用か」である。
- ユーザー入力、明示された資料、grillで確認した決定にない用語・イベント・役割・状態・制約を確定事項として作らない。不明点のうち成果を左右するものを外部`grill@grill`を呼ぶ先頭工程で厳選して確認し（問う数の上限と対話の作法はgrillの公開契約に従う）、上限で問えなかった論点と決まらなかった論点は、各公開入口の停止条件の判断基準で扱う。2回目のgrillは利用者が求めた場合か、決定なしでは成果物を完成できない場合だけ行う。
- `write-doc`と`grill`は同梱せず、別repositoryへは`playbook.yml`の`requires`と`playbook:`工程だけで依存する。相手の内部の部品名、工程、script、参考資料、設定へ触れず、依存versionも固定しない。呼び方は同梱の内部skill `write-bdd`の`references/nested-playbook.md`が1か所で定め、各入口はその規律を適用する。
- Slack、meeting、session収集、digest、cadence、agent-run、PR関連を追加しない。
