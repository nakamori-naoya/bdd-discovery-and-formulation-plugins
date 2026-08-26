---
name: explore-events
description: 業務で起きる事実（業務イベント）を時系列に洗い出し、引き金・担い手・前提・業務上の結果・確からしさを1件ずつ台帳へ残す。要約も設計もせず、洗い出せた範囲と未確認の残りを返す。「業務の流れを洗い出して」「何が起きるのか整理して」「イベントを洗い出して」と言われたとき、業務知識を文章にする前に使う。
---

# explore-events

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
