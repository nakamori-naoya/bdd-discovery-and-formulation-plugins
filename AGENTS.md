> 作業を始める前に、workspace正本入口 `/Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/AGENTS.md` を読み、そこから指定される共通規約とこのrepository固有の規則を適用する。

# AGENTS.md

このrepositoryは、BDDによるdiscovery、formulation、User Journeyの意味判断を配布するsourceである。

- 対象はドメインBDD、データモデリングBDD、User Journeyの線引き、ユーザー目的達成BDDに限定する。
- marketplaceへ公開するインストール対象は`bdd-discovery-and-formulation` package 1つである。公開入口は`plugins/bdd-discovery-and-formulation/skills/<entry>/`の6つで、両runtime manifestの`skills`が列挙する。内部skillは2つ以上の公開入口が共有する判断だけを`internal/<name>/`に置き、`internalPlugins`で宣言する。1つの公開入口からしか使わない判断はその入口へ統合する。
- 公開入口と内部skillは、directory名、`SKILL.md`の`name`、隣接`playbook.yml`の`name`を同じ一つの名前にする。
- `SKILL.md`は目的、入力、判断基準（観察対象と二者択一の述語を肯定形で）、手順、停止条件、出力を持つ。実行基盤の配管（環境変数によるroot解決、設定解決script、`${.…}`マクロ、同期block、「解決済みYAMLを読め」型の指示）を書かない。入口が使うtoolは入口directory基準の相対pathで示し、入力、出力、終了code、失敗時に止まるか回復するかを宣言する。
- 設定fileを持たない。保存先（`output_directory` / `name` / `update_target`）、対象RDBの製品と版、論理モデリングの手法は公開入力で受け取り、既定値を持たない。案件固有の役割名、本数、置き場をSKILL・reference・fixtureの既定にしない。
- ハーネスが作る資料の冒頭は読み手の既知の語で書いた本文段落から始め、メタ情報の一覧を置かない。中心の問い、扱う理由、役割×目的の一覧、除外事項の送り先のような作業記録は報告に載せ、正本へ写さない。
- User Journeyは、1人の主たるユーザーの1つの目的について、開始から観測可能な完了までに複数の意味ある場面が状態を受け渡す場合だけ扱う。場面と分岐は主たるユーザーが観測できる振る舞いだけで書き、判定は「この違いが起きたとき、主たるユーザーは何を見て気づくか」である。
- 「誰が行えるか」は成立条件と同じ重さのコアの決まりとして、すべてのコマンドとクエリについて業務知識に書く。判定は「破られたときに困るのは業務か運用か」である。
- ユーザー入力、明示された資料、grillで確認した決定にない用語・イベント・役割・状態・制約を確定事項として作らない。不明点は外部`grill@grill`を呼ぶ先頭工程で1問ずつ確認し、回答前に後続工程へ進まない。
- `write-doc`と`grill`は同梱せず、別repositoryへは`playbook.yml`の`requires`と`playbook:`工程だけで依存する。相手の内部の部品名、工程、script、参考資料、設定へ触れず、依存versionも固定しない。呼び方は各入口の`references/nested-playbook.md`に従い、6入口の複製は同一内容にする。
- Slack、meeting、session収集、digest、cadence、agent-run、PR関連を追加しない。
- 変更後は`bash scripts/validate.sh`と、workspace rootの`bash scripts/validate.sh <このrepositoryの絶対path>`を実行し、正常系だけでなく意図的に壊した負の試験が落ちることも確認する。
- install cacheは編集せず、このsourceを正本としてチューニングする。
