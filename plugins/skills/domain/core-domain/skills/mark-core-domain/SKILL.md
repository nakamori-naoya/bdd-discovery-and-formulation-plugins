---
name: mark-core-domain
description: 題材をコア・支援・汎用へ分け、そう判定した理由とともに境界を引き、画面・保存・手順のような実装の関心をスコープ外へ落とす。「これはコアドメインの話か」「業務の話と実装の話を切り分けて」「どこに力を注ぐべきか」と聞かれたとき、また業務の決まりを正本として書き残す前に使う。
---

# mark-core-domain

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
