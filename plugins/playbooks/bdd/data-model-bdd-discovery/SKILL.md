---
name: discover-data-model
description: 業務シナリオと業務イベントから、データの作成・更新・削除に関係する振る舞いを発見し、検査済みBDDとRDB論理データモデルを一つの資料にする。「データモデルのBDDを発見して」「業務イベントから永続化を考えて」と言われたときに使う。
---

# データモデリングのBDDを発見する

**テーブルから始めない。** 何が起きたため、どの事実を、誰の後の判断や説明のために残すのかを確定してから論理構造へ写す。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
BUNDLE_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
if [ -d "${BUNDLE_ROOT}/playbooks/bdd/data-model-bdd-discovery" ]; then
  PLUGIN_ROOT="${BUNDLE_ROOT}/playbooks/bdd/data-model-bdd-discovery"
else
  PLUGIN_ROOT="${BUNDLE_ROOT}"
fi
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 工程を解決する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
printf '%s\n' "$CFG_FILE"
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.playbook.focus}`は`data-model`、`${.playbook.document_type}`は`rdb-logical-data-modeling`に固定される。[このplaybookの焦点](references/focus.md)を読み、Readと物理設計を混ぜない。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各工程で意識することを補う。`grill`工程には実行指示書のdata model固有の文脈を`context`と`questions`として渡し、相手に永続化の観点を求めない。

[入れ子の段取りを呼ぶ](references/nested-playbook.md)を必ず読む。`playbook:`の工程（`grill`、`write-doc`）は、そこに書いた入口・入力・出力だけで呼ぶ。相手の中の部品名、工程の呼び名、保存の呼び名、script、参考資料、設定へは触れない。

**根拠づけられた入力は`ground`工程が作る。** `grill`が返すのは`decisions`と`open_questions`だけである。

**後片付けは自分でする。** 最終資料の保存を確認してから`python3 "${PLUGIN_ROOT}/scripts/cleanup.py" --config "$CFG_FILE" --artifact <名前>=<path> ...`を実行する。消えるのは`${.playbook.contract.cleanup.delete_after_document}`に宣言し、かつgitが追跡していないファイルだけである。

[BDDの前提・トリガー・失敗理由](references/scenario-premises.md)を必ず読む。永続化シナリオを資料へ写す前に条件マトリクスを作り、`python3 "${PLUGIN_ROOT}/scripts/scenario_matrix.py" check --file <condition-matrix.json>`を通す。

## 2. 永続化の振る舞いを先に発見する

[入力に根拠づける規律](references/input-grounding.md)を読み、利用者の発言、明示された資料、`grill`工程で確認した決定にない業務用語・イベント・概念を作らない。`${.playbook.steps}`を順に実行し、各工程へ`--scope=${.resolution.scope_root}`を渡す。`design-data-model`工程には加えて`--override=method=${.playbook.modeling.method}`を渡す。アクター、事前状態、業務イベント、条件、判断、結果、次状態から、初めて成立する事実、追加する履歴、保持理由、物理削除を許す条件を確かめる。

`${.playbook.contract.persistence_operations}`の作成・更新・削除を、シナリオありまたは理由つき対象外として全て検討する。不明点や深掘りが必要な点は`grill`工程で利用者へ1問ずつ確認し、`ground`工程が束ねた`grounded_input`にならない仮説を後続へ渡さない。未確認事項が残る、対象操作のシナリオが無い、業務上の取消と物理削除が混ざる場合は論理モデルへ進まない。

ここでは業務担当者が認識している代表的な永続化の共通理解を作る。境界値、同値分割、順序逆転、重複、同時実行、読み取り特性を体系的に反証しない。それらによる深化は、完成した論理資料を入力にするdata-model-formulationが担う。

## 3. 論理モデルへ写す

検査済みシナリオだけを論理モデル工程へ渡す。各シナリオを独立したGiven・When・Thenにし、BeforeとAfterの双方へ全論理テーブルを同じ順序で置く。0件は「レコードなし」、変化しないものは「変更なし」と明記する。

物理名、物理型、索引、分離レベル、パーティション、SQL、API、DTO、ORMは書かない。現在の姿を持つリソース系と、成立済みの業務イベントを残すイベント系を区別する。

## 4. RDB論理設計資料として保存する

論理モデルとBDDを1つのファイルへ束ね、その絶対pathを1要素の配列にして`material`、`${.playbook.document_type}`を`document_type`、`${.playbook.output_format}`を`output_format`、`${.playbook.out_dir}`の絶対pathを`output_directory`、資料のファイル名を`name`として`write-doc`工程へ渡す。BDDは素材の末尾に置く。

## 5. 報告する

永続化シナリオ、BDDを含むRDB論理設計資料の絶対パス、CUDの扱い、追加記録にした変化、保持・削除条件、未決を報告する。

## 実行設定の寿命

prepareが返した絶対pathを実行記録へ保持する。別shellではそのpathを`CFG_FILE`へ明示して読み、shell変数の継承を前提にしない。完了時と失敗停止時のどちらも、最後の設定利用後に`python3 "${PLUGIN_ROOT}/scripts/run-config.py" cleanup --config "$CFG_FILE"`を実行する。他runの設定やdirectoryを削除しない。

条件付き工程を含め、各工程を呼ぶ直前に`yq -o=json '.' "$CFG_FILE" | python3 "${PLUGIN_ROOT}/scripts/resolve-dependency.py" --check-steps <工程id>`を実行する。失敗時は工程を実行せず停止する。
