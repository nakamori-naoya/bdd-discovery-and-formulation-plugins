---
name: design-rdb-persistence
description: 検査済みの論理データモデルを変えずに、指定されたRDB製品・バージョンで利用可能と確認した機能だけを使い、物理制約、型、index、分離レベル、パーティション、容量・性能・運用をRDB物理設計へ写す。論理定義は重複掲載せず、代表Readと採用機能の根拠を持つ資料を返す。「物理設計して」「DBの版に合わせてindexや分離レベルを設計して」と言われたときに使う。
---

# design-rdb-persistence（RDBの物理設計をする）

**論理テーブル設計を物理設計で変えない。** API、DTO、ORM、画面、サービス分割を設計せず、論理モデルを対象RDBと版でどう実現し、どう運用するかへ集中する。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 対象RDBを解決する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

依頼または上段から製品・版を受け取り、必ず解決し直す。単体呼び出しでも省略しない。

```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)" --override=database.product='<製品>' --override=database.version='<版>') || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

`${.database.product}`、`${.database.version}`、`${.design_dir}`を確認する。`${.relational_data_modeling}`、`${.null_avoidance}`、`${.relational_data_lifecycle}`、`${.transaction_isolation}`、`${.physical_rdb_template}`を必ず読む。

## 2. 検査済みの論理モデルだけを入力にする

BDDシナリオを含む検査済みの論理データモデルを受け取る。論理モデルが無ければ止まる。物理設計資料へBDDシナリオを再掲しない。テーブル、列、業務上のキー・関係・制約を増減または再編する必要を見つけたら、この工程で補わず論理設計へ戻す。

物理設計へ進む直前に論理構造の指紋を作り、物理資料へ記録する。`rdb.py check`は同じ論理モデルから指紋を再計算し、テーブル、列、業務制約が変化していれば物理設計を完了にしない。

```bash
python3 "${PLUGIN_ROOT}/scripts/rdb.py" fingerprint --config "$CFG_FILE" --model-file <論理データモデル>
```

物理設計ではReadも扱う。業務で典型的かつ重要な読み取りについて、対象、絞り込み、結合、並び順、必要な鮮度、想定件数を記録する。これはindexと性能判断の根拠であり、論理設計のCUD向けBDDには戻さない。

## 3. 論理設計が要求する保証を分離レベルへ写す

論理設計の「並行実行で必要な保証」を読む。物理設計では、`READ COMMITTED`、`REPEATABLE READ`、`SERIALIZABLE`などから必要条件を満たす分離レベルを明示する。分離レベル名だけで完了にせず、対象RDB・版で防げる現象、制約やロックとの併用、競合時の中断・再試行を`${.design_contract}`へ書く。

同じ分離レベル名でも製品と版によって挙動が異なる。予約の不存在確認や範囲の重複、書き込みスキューのように行ロックだけでは守れない条件を、対象版の公式資料または再現試験で確かめる。

## 4. 対象バージョンの機能を確かめる

採用する型、制約、index、時間表現、生成列、範囲、トランザクション機能は、**対象版の公式資料または対象版の実機**で確認する。current版だけの説明、記憶、別製品の類似機能を根拠にしない。確認できない機能は採用しない。

```bash
python3 "${PLUGIN_ROOT}/scripts/rdb.py" capability --config "$CFG_FILE" --topic <題材> \
  --feature '<設計で使う機能>' --support-from '<利用可能な版または対象版での状態>' \
  --evidence '<対象版の公式URLまたは実機確認>' --note '<この設計で使う理由>'
```

## 5. RDB物理設計を書く

`${.physical_rdb_template}`を複製し、`${.design_contract}`の見出しと追跡規則で`${.design_dir}/<題材>.md`を書く。論理設計のER図、テーブル・カラム定義、CUDのBDDは再掲せず、入力論理資料を一つ明記する。物理制約、型の選択、index、分離レベル、配置、容量・性能・運用を具体化する。indexは先に記録したReadまたは制約と測定根拠がある範囲だけにし、複合indexは列順の理由を書く。

```bash
python3 "${PLUGIN_ROOT}/scripts/rdb.py" check --config "$CFG_FILE" --topic <題材> \
  --design-file <RDB物理設計> --model-file <論理データモデル>
```

物理設計に論理構造の複製または追加、BDDシナリオが混ざった場合、設計で使う全機能の対象版根拠が無い場合は止まる。NULLは論理設計で許した箇所だけに使い、対象RDB上の扱いを残す。最後に対象RDBと版、入力論理資料、物理資料、機能根拠、典型Read、indexと列順の理由、分離レベル、NULLを許した箇所、未決を報告し、アプリケーション実装や移行実行へは進まない。
