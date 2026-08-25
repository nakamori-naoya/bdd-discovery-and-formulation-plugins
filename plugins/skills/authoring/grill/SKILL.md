---
name: grill
description: 合意に達するまで1問ずつ問い詰めて、曖昧さを潰す。推奨回答を必ず添え、調べれば分かることは聞かない。決めたことと未決を決定ログへ残す。「詰めて」「問い詰めて」「設計を固めて」と言われたとき、実装や資料作成に入る前に使う。
---

# grill（合意に達するまで問い詰める）

**このスキルは実装しないし、資料も書かない。** 曖昧さを潰して、決めたことと未決を残すところまでを担う。

**分かった気を潰すのが仕事である。** 「たぶんこうだろう」で進むと、実装が終わってから前提の違いが出てくる。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 観点と規律を読む

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.instructions.questioning.directive}` に従い、`${.aspects.path}` と `${.questioning}` を読む。
同梱の観点を選ぶときは、[汎用](references/aspects/default.md)または[業務ルール](references/aspects/business-rules.md)のうち、解決された1つだけを読む。

**exit 2 で止まったら先へ進まない。** 指した観点ファイルが無いのに既定へ倒れると、差し替えたつもりで効いていない状態になる。

`aspects.source` が `default` なら、**「自分のファイルを指せば差し替えられる」と一度だけ伝える**。

## 2. 1問ずつ詰めて記録する

[問い詰めワークフロー](references/workflow.md)を必ず読む。先に調査し、1問ずつ聞き、決まった瞬間に`decision.py`へ記録する。statusを選ぶときは[decision-status.md](references/decision-status.md)も読む。

設定形式は[README](README.md)を参照する。実装や資料作成へ進まず、一度に大量の問いを出さず、推奨回答なしで丸投げしない。
