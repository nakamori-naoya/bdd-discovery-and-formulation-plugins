---
name: formulate-domain
description: コアドメインの既存domain-rule資料をQA観点で反証し、境界シナリオ、新しい業務理解、未決の問いを同じ資料へ戻して深化させる。「BDDを定式化して」「境界値も含めてドメイン資料を深掘りして」と言われたときに使う。新規資料は作らない。
---

# formulate-domain

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
