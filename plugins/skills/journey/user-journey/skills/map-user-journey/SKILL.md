---
name: map-user-journey
description: 1人の主たるユーザーが1つの目的を達成するまでについて、何がJourneyで何がJourneyでないかを判定し、開始、観測可能な完了、複数の意味ある場面、状態の受け渡しを検査済みmapにする。「これはUser Journeyか」「目的達成までを場面でつないで」「ユースケースやドメインとの境界を分けて」と言われたときに使う。BDD、UIフロー、業務ルール、データモデル、テスト仕様は作らない。
---

# map-user-journey

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
