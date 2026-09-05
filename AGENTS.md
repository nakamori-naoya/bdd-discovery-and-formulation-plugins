# AGENTS.md

このrepositoryは、BDDによるdiscovery、formulation、User Journeyの意味判断を配布するsourceである。

- 対象はドメインBDD、データモデリングBDD、User Journeyの線引き、ユーザー目的達成BDDに限定する。
- marketplaceへ公開するインストール対象は`bdd-discovery-and-formulation` playbook packageだけにし、個々のplaybookと下段skillを別entryへ公開しない。
- User Journeyは、1人の主たるユーザーの1つの目的について、開始から観測可能な完了までに複数の意味ある場面が状態を受け渡す場合だけ扱う。
- ユースケース、UX Journey map、画面・API・データ構造・テスト実行環境をUser Journeyへ混ぜない。
- ユーザー入力、明示された資料、grillで確認した決定にない用語・イベント・役割・状態・制約を確定事項として作らない。
- 不明点または深掘りが必要な点があれば、外部`grill@grill`を使う4入口の先頭工程で1問ずつ確認し、回答前に後続工程へ進まない。
- `write-doc`と`grill`は同梱せず、別repositoryにはそのrepositoryが公開するplaybook packageだけで依存する。外部packageの内部skill名へ依存せず、依存versionを固定せず、解決したpackage内に必要なskillが存在することを検査する。
- Slack、meeting、session収集、digest、cadence、agent-run、PR関連を追加しない。
- 変更後は`bash scripts/validate.sh`を実行し、正常系だけでなく意図的に壊した負の試験が落ちることも確認する。
- install cacheは編集せず、このsourceを正本としてチューニングする。
