# 検証結果

- 状態: **PASS**
- 検証日: 2026-08-25
- 上流commit: `f9e30db06f98309840066789c8d7844bd217ffe5`
- 対象: [vendor-lock.json](vendor-lock.json)に固定した15 pluginと、その最小shared正本

## 上流確認

- `git pull --ff-only origin main`: `Already up to date.`
- 上流の`bash scripts/lint.sh`: PASS（skill runtimeは52 passed、0 failed）
- 直近3件のmerged PRと取込判断は[VENDORING.md](VENDORING.md)に記録した。
  - PR #140: BDD入口の公開plugin名へ`bdd`を含める変更を反映
  - PR #139: BDDのdirectory名変更とMarkdown出力を反映
  - PR #138: sandbox資料だけのため除外

## prototype必須検証

`bash scripts/validate.sh`を実行し、終了code 0を確認した。

| 検証 | PASS | FAIL |
|---|---:|---:|
| 構造・manifest・marketplace・コピー境界 | 152 | 0 |
| resolver・prepare・依存欠落・入力根拠の負の試験 | 83 | 0 |

実行時検証には次を含む。

- 4つのBDD入口と`write-doc`のresolver
- 4入口の全skill工程と、入れ子`write-doc`の全skill工程の`prepare.sh`
- `data-model`の`method`欠落・空値拒否
- `grill`が先頭でない、`grounded_input`が伝播しない、入力根拠契約を弱めた設定の拒否
- manifest、skill、入口script、入れ子保存scriptの欠落拒否
- 電子チケットのお題に探索場面・問い・推奨回答などのヒントがないこと
- `content-types`が`domain-rule`と`rdb-logical-data-modeling`の2型だけであること
- Slack関連資産と、除外対象plugin directoryが存在しないこと

Claude Codeの`claude plugin validate <plugin> --strict`は15 pluginすべてPASSした。

Codexでは恒久配置後に次を確認した。

- `codex plugin marketplace add <prototype-root> --json`: exit 0
- 取込名: `knowledge-hub-bdd-prototype`
- `codex plugin marketplace list --json`: 恒久配置の絶対pathをrootとするlocal marketplaceを確認
- plugin本体のglobal install: 未実施。既存`harness-plugins`と依存plugin名が競合し得るため

## 別エージェントによる受入

### Codexエージェント

別のCodexエージェントがprototypeを読み取り専用で使用・再検証し、最終判定PASSとした。

- `bash scripts/validate.sh`: Structure 152/0、Runtime 83/0
- 4入口から入れ子`write-doc`までの全skill prepare: PASS
- `content-types`の2型限定、marketplace description一致、ヒントなしfixture: PASS
- ファイル変更・生成物: なし

先行受入では電子チケットのお題を`domain-bdd-discovery`へ渡し、先頭の`grill`で一問だけ確認して回答待ちになり、後続工程へ進まないことも確認した。

### Claude Opus 5

`agent-run` 0.2.6をホストのread modeで実行した。最終実行結果は次のとおり。

- `requested_model`: `claude-opus-5`
- `used_model`: `claude-opus-5`
- `status`: `done`
- 経過時間: 180秒
- 最終判定: PASS
- 実測: Structure 152/0、Runtime 83/0、上流`f9e30db`とPR #140/#139/#138、4つのBDD公開名、15 plugin集合、コピー境界、grill契約に不具合なし

先行レビューで検出された`content-types`の過剰な公開面、Claude marketplace descriptionのずれ、入れ子`write-doc`検証不足、任意診断のsilent skipはすべて修正した。さらにPR #140を反映して内容を固定した後の最終監査で再確認した。

## Codex plugin-creator互換診断

必須受入とは別に、PyYAMLを`/private/tmp`の隔離dependencyへ導入して`bash scripts/validate-plugin-creator.sh`を実行した。結果は0 passed、15 failedだった。

これは実行不具合ではなく、汎用validatorが`skills`を`skills/` directoryとして解決し、`interface` objectを要求する一方、`harness-plugins`の正式規範がroot `SKILL.md`配布を採用している契約差である。そのため必須受入には含めず、Claudeのstrict validator、対象限定構造検証、実resolver・prepare検証を配布判定に用いた。任意診断はdependencyやvalidatorが無い場合も成功扱いせず、exit 2で停止する。

## 既知の制約

- prototypeは上流と同じplugin名・skill名を持つ。既存`harness-plugins`版とのglobal同時installは競合し得るため、正式な派生名を決めるまではinstallしない。
- `grill`で未確定事項が残る入力は、仕様どおり一問ずつ回答を待つため、無回答のまま最終BDD資料まで自動完走させる対象ではない。
