# 検証結果

- 状態: **PASS**
- 検証日: 2026-08-26
- 上流commit: `10852c3365df0c454160082b1458ca381e5d3dab`
- 対象: [vendor-lock.json](vendor-lock.json)に固定したBDD依存閉包16 pluginと、その最小shared正本

## 上流確認

`git ls-remote origin refs/heads/main`でremote `main`が上流commitと一致することを確認した。前回固定点以降の取込判断は[VENDORING.md](VENDORING.md)に記録している。

- PR #146: 4つのBDD入口の最終cleanup契約と`intermediate-cleanup`を反映
- PR #142: BDD資料化でも使う`visual-guidance`の汎用図解ガイダンスを反映
- PR #145、#144、#143、#141: product planningまたは`docs`中心のため移行しない
- `content-types`: 上流0.6.2の27型は持ち込まず、BDD用2型だけの派生0.6.3を維持

## prototype必須検証

`bash scripts/validate.sh`を実行し、終了code 0を確認した。

| 検証 | PASS | FAIL |
|---|---:|---:|
| 構造・manifest・marketplace・コピー境界 | 157 | 0 |
| resolver・prepare・cleanup・負の試験 | 99 | 0 |

実行時検証には次を含む。

- 4つのBDD入口と`write-doc`のresolver
- 4入口の全skill工程、最終`remove-intermediate-artifacts`、入れ子`write-doc`の全skill工程の`prepare.sh`
- `data-model`の`modeling.method`欠落・空値拒否
- `grill`が先頭でない、`grounded_input`が伝播しない、入力根拠契約を弱めた設定の拒否
- 最終cleanupの欠落・順序変更と、cleanup依存manifest欠落の拒否
- cleanup正常系として、明示した未追跡中間ファイルだけを削除し、最終資料を保持すること
- cleanup負の試験として、Git追跡中ファイルとrepository外ファイルを拒否すること
- manifest、skill、入口script、入れ子保存scriptの欠落拒否
- 電子チケットのお題に探索場面・問い・推奨回答などのヒントがないこと
- `content-types`が`domain-rule`と`rdb-logical-data-modeling`の2型だけであること
- product planning、Slack関連資産、除外対象plugin directoryが存在しないこと

## 既知の制約

- prototypeは上流と同じplugin名・skill名を持つ。既存`harness-plugins`版とのglobal同時installは競合し得るため、正式な派生名を決めるまではinstallしない。
- `grill`で未確定事項が残る入力は、仕様どおり一問ずつ回答を待つため、無回答のまま最終BDD資料まで自動完走させる対象ではない。
