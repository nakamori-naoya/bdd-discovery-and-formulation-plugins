---
name: design-data-model
description: 業務イベント、事前状態、判断、結果、次状態を含む業務シナリオから、時間を越えて残すべき状態・約束・権利・義務・判断根拠を見出し、BDDシナリオを含む論理データモデルを作る。手法は事実の記録中心・正規化中心・分析中心などから選べ、利用者のファイルも指せる。記録の形と業務シナリオを双方向で突き合わせ、永続化の必要を説明できない要素を残さない。「論理データモデリングして」「何を記録すべきか整理して」「このモデルに要らないものが無いか見て」と言われたときに使う。
---

# design-data-model

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
