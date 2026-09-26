#!/usr/bin/env bash
# X のクローンのケースが共有する準備。空の作業場所へ、依頼の入力（要件と業務の分け方）と、
# skill が読む別 package のファイルを置く。各ケースの scaffold.sh がこれを呼ぶ。
# 別 package（write-doc、grill）は隔離環境に入らないので、兄弟 checkout の最新のファイルを写す。
# 兄弟 checkout が無ければ、写しで代用せずに止まる。
set -euo pipefail

TOPIC_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY=$(cd "$TOPIC_DIR/../../../.." && pwd)
WORKSPACE=$(cd "$(dirname "$REPOSITORY")" && pwd)
WRITE_DOC="$WORKSPACE/write-doc-plugins/plugins/write-doc/skills/write-doc"
GRILL="$WORKSPACE/grill-plugins/plugins/grill/skills/grill"

for skill in "$WRITE_DOC" "$GRILL"; do
  [ -f "$skill/SKILL.md" ] || { echo "兄弟 checkout の skill が無い: $skill" >&2; exit 2; }
done

mkdir -p input harness out grill-log
cp "$TOPIC_DIR"/materials/input/*.md input/
cp "$TOPIC_DIR/materials/split.md" split.md
cp -R "$WRITE_DOC" harness/write-doc
cp -R "$GRILL" harness/grill
