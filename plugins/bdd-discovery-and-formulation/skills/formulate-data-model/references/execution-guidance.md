# data model BDD formulation 実行指示書

## 背景と目的

この入口は、既存のBDD付きRDB論理設計を永続化の業務判断から反証し、確認済みの発見を同じ論理資料へ戻してから物理設計へ進む。論理構造を物理都合で作り替えない。

## 前提

- 既存のBDDとtable構造の対応を説明できることが開始条件である。
- 論理設計の深化と、Read、型、index、分離レベル、配置の物理設計を分ける。
- 確認できない問いに依存するBDDや論理構造は更新しない。
- 対象RDBの製品と版、論理モデリングの手法は入力で受け取る。既定を持たず、決め方を報告する。

## 各工程を実行するときの指示

### challenge-persistence（grill）

既存論理資料のどの永続化上の主張を反証しているかを明らかにしてから1問ずつ確認する。作成・更新・削除、同値と境界、精度と単位、条件組合せ、状態遷移、順序、重複、同時実行、役割と権限、権限内の悪用、時間、規則変更と遡及、失敗時保証、不変条件によって、残す事実・履歴・業務制約が変わるかを意識する。Readやindexを論理設計の問いへ混ぜない。

`context`には`purpose`（既存の論理設計を反証して同じ資料へ戻し、対象RDBの物理設計へ写す）、`audience`（業務責任者、開発者、DB設計者）、`boundary`（API、DTO、ORM、画面、サービス分割は扱わない）を渡し、題材固有の観点は`questions`で渡す。

### deepen-scenarios と revise-logical-model（論理設計の深化）

確認済みの発見をBDD、table、column、business constraintへ対応づける。BeforeとAfterで全tableを同じ順序に置き、変更なしとレコードなしを省略しない。更新先は入力論理資料と同じパスにする。

### design-physical（物理設計）

更新済み論理構造を固定したまま、典型的なRead、対象RDBの機能根拠、型、制約、index、分離レベル、配置を決める。論理BDDを物理資料へ複製しない。冒頭の段落は、どの論理設計をどの製品と版でどう実現するかを読み手の既知の語で文章として運ぶ。

### update-logical-document / document-physical（write-doc）

論理資料は`document_type: rdb-logical-data-modeling`と`update_target`で同じpathを差し替え、物理資料は`document_type: rdb-physical-design`と`output_directory` / `name`で新規に1本保存する。呼び方は[入れ子の段取りを呼ぶ](nested-playbook.md)に従う。
