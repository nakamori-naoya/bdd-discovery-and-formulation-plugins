# AGENTS.md

このrepositoryは、BDDによるdiscoveryとformulationを配布するsourceである。

- 対象はドメインBDDとデータモデリングBDDだけに限定する。
- ユーザー入力、明示された資料、grillで確認した決定にない用語・イベント・役割・状態・制約を確定事項として作らない。
- 不明点または深掘りが必要な点があれば、外部`grill@grill`を使う4入口の先頭工程で1問ずつ確認し、回答前に後続工程へ進まない。
- `write-doc`、`writing-rules`、`grill`は同梱せず、完全修飾したexact versionの外部依存として扱う。
- Slack、meeting、session収集、digest、cadence、agent-run、PR関連、use-case／journey BDDを追加しない。
- 変更後は`bash scripts/validate.sh`を実行し、正常系だけでなく意図的に壊した負の試験が落ちることも確認する。
- install cacheは編集せず、このsourceを正本としてチューニングする。
