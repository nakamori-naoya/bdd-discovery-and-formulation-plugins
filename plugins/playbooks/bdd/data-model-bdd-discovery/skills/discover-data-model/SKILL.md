---
name: discover-data-model
description: 業務シナリオと業務イベントから、データの作成・更新・削除に関係する振る舞いを発見し、検査済みBDDとRDB論理データモデルを一つの資料にする。「データモデルのBDDを発見して」「業務イベントから永続化を考えて」と言われたときに使う。
---

# discover-data-model

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
