---
name: write-persistence-scenarios
description: 既存の業務シナリオと業務イベントから、データの作成・更新・削除に関係する断面を選び、アクター、事前状態、業務イベント、判断、残す事実、次状態、履歴、保持理由を永続化シナリオとして記録する。3操作を検討済みで、未確認事項のない資料をデータモデリング工程へ渡す。「永続化シナリオを作って」「データモデリングの前提を整理して」と言われたときに使う。
---

# write-persistence-scenarios

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
