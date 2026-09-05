---
name: mark-core-domain
description: 題材をコア・支援・汎用へ分け、そう判定した理由とともに境界を引き、画面・保存・手順のような実装の関心をスコープ外へ落とす。「これはコアドメインの話か」「業務の話と実装の話を切り分けて」「どこに力を注ぐべきか」と聞かれたとき、また業務の決まりを正本として書き残す前に使う。
---

# mark-core-domain（業務の話に線を引く）

**このスキルは業務の決まりを書かない。** どこまでが業務の話で、そのうちどこがコアかを決めるところまでを担う。

**全部が大事だと言うのは、何も決めていないのと同じである。**

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
BUNDLE_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
if [ -d "${BUNDLE_ROOT}/skills/domain/core-domain" ]; then
  PLUGIN_ROOT="${BUNDLE_ROOT}/skills/domain/core-domain"
else
  PLUGIN_ROOT="${BUNDLE_ROOT}"
fi
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 置き場と方針を読む

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
printf '%s\n' "$CFG_FILE"
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.instructions.marking.directive}` に従い、線引きは `${.scope_dir}` へ残す。

## 2. まず業務の話かどうかで切る

`${.boundary}`、`${.domain}`、`${.bounded_contexts}` を必ず読む。**3つの問いで判定する。** 仕組みを全部やめても残るか、業務を知る人がその言葉を使うか、破られて困るのは業務か。言葉とモデルの意味境界を、teamやserviceの境界から推測しない。

**迷ったら業務の話ではない側へ倒す。** 取りこぼしは次に業務を語れば戻ってくるが、混入した実装の話は正本を腐らせる。

## 3. 残ったものをコア・支援・汎用へ分ける

`${.subdomains}` と `${.concept_map}` を必ず読む。**選ばれる理由を1文で言えないうちは分けない。**

分類には必ず理由を添える。理由の無い分類は、次に読む人が覆せない。

## 4. 検査を通してから保存する

```bash
python3 "${PLUGIN_ROOT}/scripts/check.py" write --config "$CFG_FILE" \
  --topic <題材> --body-file <線引きを書いた一時ファイル>
```

`## コア` `## 支援` `## 汎用` `## スコープ外` の4節を必ず持たせる。**該当が無い節には「なし」と書く。** 節ごと落とすと、考えなかったのか無かったのかが読めない。

実装の語が残っていれば保存されない。**業務語として正しい場合だけ `--allow <語>` で明示する。** 通らないからといって節を削らない。拾う語と言い換え先は `python3 "${PLUGIN_ROOT}/scripts/check.py" terms` で出る。

## 5. 報告する

- 線引きのパスと、コア・支援・汎用それぞれの件数
- **スコープ外へ落としたものと、その理由**
- 判定できず保留したものと、何が分かれば決まるか

設定形式は[README](README.md)を参照する。業務の決まりそのものを書き起こす作業へは進まない。

## 実行設定の寿命

prepareが返した絶対pathを実行記録へ保持する。別shellではそのpathを`CFG_FILE`へ明示して読み、shell変数の継承を前提にしない。完了時と失敗停止時のどちらも、最後の設定利用後に`python3 "${PLUGIN_ROOT}/scripts/run-config.py" cleanup --config "$CFG_FILE"`を実行する。他runの設定やdirectoryを削除しない。
