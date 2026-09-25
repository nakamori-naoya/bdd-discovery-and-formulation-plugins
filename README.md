# BDD Discovery and Formulation

業務の決まり、ユーザーの目的達成、残す事実の三つを、業務の言葉とBDDの具体例で書いた資料にするmarketplaceである。Claude CodeとCodexの両方で使える。資料を見た業務の人と開発者が、同じ例から同じ結論を出せるようにすることが目的で、実装方法やテストコードを先に決めるためのものではない。

## 資料の種類ごとに入口が一つある

公開入口は三つで、どれも資料の種類に対応する。新しく作るときも、既存の資料へ反例を当てて深めるときも、同じ入口を使う。違いは、入口がgrillで何を問うかだけである。

`model-domain-rule`は、コアドメインの業務知識をdomain-rule資料にする。業務の話かどうかを三つの問いで線引きし、業務の行いごとに誰が行えるか、成り立つ条件、拒む理由を一か所にそろえる。業務の言葉と英名の対応（ユビキタス言語）もこの資料が持つ。

`map-user-journey`は、1人の主たるユーザーが1つの目的を達成するまでを、ユーザーが観測できる場面の連なりとしてユーザー目的達成BDD資料にする。

`model-logical-data`は、domain-rule資料を根拠に、何を時間を越えて残すかを決め、BDDごとにテーブルのBeforeとAfterを具体的な行で示したRDB論理データモデル資料にする。保存するのは起きた事実と業務が与えた値だけで、集計のような情報は持たない。RDB物理設計は別の`rdb-design` packageが受け持つ。

```text
既存の用語集と要件資料を根拠に、予約取消の業務知識をBDD付きで整理して。
既存の予約取消のdomain-rule資料を、締切時刻ちょうどと二重取消で深掘りして。
注文確定・取消・返金のdomain-rule資料から、論理データモデルを作って。
初回訪問者が商品を比較し、購入し、受取を確認するまでをユーザー目的達成BDDにして。
```

資料の節構成と記法は、write-docの文書型（`domain-rule`、`user-journey-bdd`、`rdb-logical-data-modeling`）のtemplateが持つ。このrepositoryはtemplateを持たない。どの入口も、止まるか進むかは各入口の`SKILL.md`の「停止条件」の節に従う。

## インストール

インストールするのは`bdd-discovery-and-formulation@bdd-discovery-and-formulation`です。各入口は問いを立てるのに`grill@grill`を、資料を保存するのに`write-doc@write-doc`を使うので、それらも必要です。下のコマンドには、それらも含めています。

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

## 検証

```bash
bash scripts/validate.sh
```

package の配置とmanifestは、兄弟checkout`../harness-tools/`の保守toolが検査する。このrepositoryに固有の検査は、`model-logical-data`が保存した資料に一回かける`immutable_model.py`の正例・反例・境界例（`scripts/test-immutable-model.sh`）だけである。検査が通っても、資料の業務上の正しさは保証されないので、資料を読んで判断する。
