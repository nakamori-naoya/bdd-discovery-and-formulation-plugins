---
name: discover-user-journey
description: 1人の主たるユーザーが1つの目的を達成するまでを発見し、開始地点、完了条件、接続した場面のBDDを最初の正本として1本作る。「ユーザーJourneyをBDDで発見して」「目的達成までの振る舞いを初めて資料にして」と言われたときに使う。既存正本の深化、ドメインルール、データモデル、テスト実行は扱わない。
---

# discover-user-journey

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
