---
name: explore-events
description: 業務で起きる事実（業務イベント）を時系列に洗い出し、引き金・担い手・前提・業務上の結果・確からしさを1件ずつ台帳へ残す。要約も設計もせず、洗い出せた範囲と未確認の残りを返す。「業務の流れを洗い出して」「何が起きるのか整理して」「イベントを洗い出して」と言われたとき、業務知識を文章にする前に使う。
---

# explore-events（業務で起きる事実を洗い出す）

**このスキルは設計しないし、資料も書かない。** 何が起きるのかを、起きた順に残すところまでを担う。

**業務の側で起きたことだけを拾う。** 画面・保存・通知は仕組みの都合であって、業務の事実ではない。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 置き場と方針を読む

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.instructions.exploration.directive}` に従い、台帳は `${.event_dir}` へ積む。置き場が決まらないまま洗い出すと、台帳が散って次に読めない。

## 2. 何を1件と数えるかを決めてから始める

`${.grain}`、`${.actors_stakeholders}`、`${.use_cases}`、`${.domain_events}`、`${.event_sourcing}`、`${.concept_map}` を必ず読む。名前の付け方、粒度、引き金の4種、確からしさの3段は `${.grain}` にある。**ここを読まずに始めると、粒度が途中で変わって並べ直せなくなる。**

要求と起きた事実、業務上の意味とevent record、内部の事実と外部契約を混同しない。Event Sourcingは洗い出しの前提にしない。

## 3. 幹から枝へ、1つずつ問う

[洗い出しの進め方](references/exploration.md)を必ず読む。**普通の流れを1本通してから**例外・時間・外部・後始末へ降りる。

## 4. 出た瞬間に台帳へ入れる

```bash
python3 "${PLUGIN_ROOT}/scripts/event.py" add --config "$CFG_FILE" --topic <題材> \
  --name '<起きたこと（過去形の業務語）>' --actor '<担い手>' \
  --trigger 操作 --outcome '<業務上どう変わったか>' \
  --precondition '<前提>' --status assumed --source '<誰・どこからの知識か>'
python3 "${PLUGIN_ROOT}/scripts/event.py" render --config "$CFG_FILE" --topic <題材>
```

**まとめて後から入れない。** 会話が進むと、誰が何を確かめたのかが混ざる。

**確認していないものを `confirmed` にしない。** 業務を知る人がその場で肯定したものだけが確認済みである。

## 5. 報告する

- 台帳のパスと件数
- **未確認のまま残った事実と、誰に聞けば確かめられるか**
- 業務の事実へ言い換えられず、台帳へ入れなかったもの

設定形式は[README](README.md)を参照する。設計・分類・資料化へ進まず、一度に大量の問いを出さない。
