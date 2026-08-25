---
name: discover-data-model
description: 業務シナリオと業務イベントから、データの作成・更新・削除に関係する振る舞いを発見し、検査済みBDDとRDB論理データモデルを一つの資料にする。「データモデルのBDDを発見して」「業務イベントから永続化を考えて」と言われたときに使う。
---

# データモデリングのBDDを発見する

**テーブルから始めない。** 何が起きたため、どの事実を、誰の後の判断や説明のために残すのかを確定してから論理構造へ写す。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 工程を解決する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.playbook.focus}`は`data-model`、`${.playbook.document_type}`は`rdb-logical-data-modeling`に固定される。[このplaybookの焦点](references/focus.md)を読み、Readと物理設計を混ぜない。

## 2. 永続化の振る舞いを先に発見する

[入力に根拠づける規律](references/input-grounding.md)を読み、利用者の発言、明示された資料、grillで確認した決定にない業務用語・イベント・概念を作らない。`${.playbook.steps}`を順に実行し、各工程へ`--scope=${.resolution.scope_root}`を渡す。`design-data-model`工程には加えて`--override=method=${.playbook.modeling.method}`を渡す。アクター、事前状態、業務イベント、条件、判断、結果、次状態から、初めて成立する事実、追加する履歴、保持理由、物理削除を許す条件を確かめる。

`${.playbook.contract.persistence_operations}`の作成・更新・削除を、シナリオありまたは理由つき対象外として全て検討する。不明点や深掘りが必要な点はgrill工程で利用者へ1問ずつ確認し、`grounded_input`にならない仮説を後続へ渡さない。未確認事項が残る、対象操作のシナリオが無い、業務上の取消と物理削除が混ざる場合は論理モデルへ進まない。

ここでは業務担当者が認識している代表的な永続化の共通理解を作る。境界値、同値分割、順序逆転、重複、同時実行、読み取り特性を体系的に反証しない。それらによる深化は、完成した論理資料を入力にするdata-model-formulationが担う。

## 3. 論理モデルへ写す

検査済みシナリオだけを論理モデル工程へ渡す。各シナリオを独立したGiven・When・Thenにし、BeforeとAfterの双方へ全論理テーブルを同じ順序で置く。0件は「レコードなし」、変化しないものは「変更なし」と明記する。

物理名、物理型、索引、分離レベル、パーティション、SQL、API、DTO、ORMは書かない。現在の姿を持つリソース系と、成立済みの業務イベントを残すイベント系を区別する。

## 4. RDB論理設計資料として保存する

論理モデルとBDDを資料化工程へ渡し、型は`${.playbook.document_type}`、媒体は`output_format=${.playbook.output_format}`に固定する。対応するテンプレートと記載例を使い、BDDを資料の末尾に置く。成果は`${.playbook.out_dir}`へ集める。

## 5. 報告する

永続化シナリオ、BDDを含むRDB論理設計資料の絶対パス、CUDの扱い、追加記録にした変化、保持・削除条件、未決を報告する。
