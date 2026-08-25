# data-model-bdd-discovery

業務シナリオと業務イベントから作成・更新・削除に関係する振る舞いを発見し、検査済みBDDを含むRDB論理データモデル資料として保存するplaybookです。

テーブルから始めず、事実の成立、現在状態の変化、追加する履歴、保持理由が尽きた物理削除を業務語で確定します。Read、索引、物理型、分離レベル、SQL、API、DTO、ORMは扱いません。

出力は代表的な永続化シナリオと、`rdb-logical-data-modeling`テンプレートで保存したMarkdownの論理設計資料です。`output_format: markdown`は固定で、呼び出し先のdoc-render設定がHTMLでも変わりません。各BDDのBeforeとAfterには全論理テーブルを同じ順序で記載します。

設定を上書きする場合は`.harness-plugins/data-model-bdd-discovery.config.yml`へ`playbook.yml`と同じ全項目を記載します。`focus`、`document_type`、`output_format`、`modeling.method`は変更できません。既定の`modeling.method`は`normalized`です。
