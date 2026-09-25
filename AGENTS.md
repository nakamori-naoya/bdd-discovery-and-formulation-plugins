> 共通の規約は /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/AGENTS.md にある。ここには、この repository だけの規則を置く。

# bdd-discovery-and-formulation

この repository は、BDD を含む業務の資料を作って深める skill を配布する。インストール対象は package `bdd-discovery-and-formulation` 一つで、公開入口は資料の種類ごとに一つずつ、`model-domain-rule`（domain-rule）、`map-user-journey`（user-journey）、`model-logical-data`（論理データモデル）の三つである。作ることと深めることは同じ入口で行い、深さは grill で何を問うかで決める。内部 skill は置かない。

- 資料の節構成と記法は、保存に使う write-doc の各型の template が持つ。この repository は template を持たない。
- 業務知識の BDD には、業務の言葉とユビキタス言語だけを使う。語の種類と英名の付け方は `model-domain-rule` の `references/ubiquitous-language.md` が一か所で持つ。
- User Journey は、1 人の主たるユーザーの 1 つの目的について、開始から観測可能な完了までに複数の場面が状態を受け渡す場合だけ扱う。
- 「誰が行えるか」は、すべてのコマンドとクエリについて業務知識に書く。
- 物理設計、対象 RDB の製品と版、index、分離レベル、運用は、この repository の責務外とする。
