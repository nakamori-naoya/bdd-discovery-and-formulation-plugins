# data-model-bdd-discovery

業務シナリオと業務イベントから作成・更新・削除に関係する振る舞いを発見し、検査済みBDDを含むRDB論理データモデル資料として保存するplaybookです。

テーブルから始めず、事実の成立、現在状態の変化、追加する履歴、保持理由が尽きた物理削除を業務語で確定します。Read、索引、物理型、分離レベル、SQL、API、DTO、ORMは扱いません。

出力は代表的な永続化シナリオと、`rdb-logical-data-modeling`型で保存したMarkdownの論理設計資料です。`output_format: markdown`はこの段取り自身の成果物条件であり、外部への入力には含めません。資料保存は`write-doc/write-doc`版2の直接入力で行います。各BDDのBeforeとAfterには全論理テーブルを同じ順序で記載します。

設定を上書きする場合は`.harness-plugins/data-model-bdd-discovery.config.yml`へ`playbook.yml`と同じ全項目を記載します。`focus`、`document_type`、`output_format`、`modeling.method`は変更できません。既定の`modeling.method`は`normalized`です。

新規保存先は公開入力の`output_directory`と`name`で直接指定します。前者は既存の書き込み可能な絶対directory、後者はパス要素を含まない`.md`名です。静的な相対`out_dir`から保存先を推測しません。
