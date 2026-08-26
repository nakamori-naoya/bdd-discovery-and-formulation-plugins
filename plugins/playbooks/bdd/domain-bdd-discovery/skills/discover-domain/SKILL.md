---
name: discover-domain
description: コアドメインの業務知識と代表的な振る舞いを共通理解にし、BDDを含むdomain-ruleの正本を1本作る。業務イベント、事前状態、アクター、判断、次状態を整理する。「業務知識をBDD付きで整理して」「コアドメインを発見して」と言われたとき、実装やQA反証へ進む前に使う。
---

# discover-domain

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
