---
name: formulate-data-model
description: 既存のBDD付きRDB論理設計をQA観点で深化させ、同じ資料へ更新する。その論理構造を変えず、設定されたRDB製品・バージョンのRead、型、index、分離レベル、配置へ写す。「データモデルを定式化して」「論理設計を深掘りして物理設計して」と言われたときに使う。
---

# formulate-data-model

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
