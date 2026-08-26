---
name: design-rdb-persistence
description: 検査済みの論理データモデルを変えずに、指定されたRDB製品・バージョンで利用可能と確認した機能だけを使い、物理制約、型、index、分離レベル、パーティション、容量・性能・運用をRDB物理設計へ写す。論理定義は重複掲載せず、代表Readと採用機能の根拠を持つ資料を返す。「物理設計して」「DBの版に合わせてindexや分離レベルを設計して」と言われたときに使う。
---

# design-rdb-persistence

このentryは配布形式を中立化する薄い入口である。次を実行してplugin rootを検証し、root直下の正本`SKILL.md`を全文読んで、その手順に従う。

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
bash "${PLUGIN_ROOT}/scripts/prepare.sh" --root-only >/dev/null || exit 2
cat "${PLUGIN_ROOT}/SKILL.md"
```
