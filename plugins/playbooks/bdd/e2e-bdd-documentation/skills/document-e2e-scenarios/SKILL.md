---
name: document-e2e-scenarios
description: ユーザーがある目的を持って開始地点から最終地点へ到達するまでを、複数のインタラクション場面が連なるBDDストーリーとして1本の資料にする。「E2EシナリオをBDDで書いて」「目的達成までの長い振る舞いを資料にして」と言われたときに使う。ドメインルール、データモデル、E2Eテスト環境は設計しない。
---

# document-e2e-scenarios

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
