> 共通の規約は /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/AGENTS.md にある。ここには、この repository だけの規則を置く。

# bdd-discovery-and-formulation

この repository は、BDD を含む業務の資料を作って深める skill を配布する。インストール対象は package `bdd-discovery-and-formulation` 一つで、公開入口は資料の種類ごとに一つずつ、`write-business-knowledge`（業務知識、business-knowledge）、`model-command-data`（コマンドデータモデル、command-data-model）、`model-query-data`（クエリデータモデル、query-data-model）、`map-user-journey`（ユーザー目的達成BDD、user-journey-bdd）の四つである。データモデルは CQRS の考えで書き込みと読み取りの二つに分け、コマンドデータモデルは作成・更新・削除で残す事実を、クエリデータモデルはその事実から、業務知識の計算とユーザー目的達成の場面で見るものが実現できるかを書く。作ることと深めることは同じ入口で行い、深さは grill で何を問うかで決める。内部 skill は置かない。

- 資料の節構成と記法は、保存に使う write-doc の各型の template が持つ。この repository は template を持たない。
- 業務知識の一つの事実をどの節（前提、制約、状況、計算、行動・出来事と判断）に書くか、業務をまたぐ決まりと名前の持ち主は、`write-business-knowledge` の `references/judgment.md` が一か所で持つ。
- User Journey は、1 人の主たるユーザーの 1 つの目的について、開始から観測可能な完了までに複数の場面が状態を受け渡す場合だけ扱う。
- 誰が起こすかは、業務知識の行動・出来事と判断の表に書く。業務知識は読み取りを書かない。事実から業務の値を導くことは計算として書く。境界の判断は `write-business-knowledge` が持つ。
- テーブルを定義するのは、そのテーブルへ書く業務のコマンドデータモデル一本だけである。ほかの資料は参照の表とリンクで指す。
- 物理設計、対象 RDB の製品と版、index、分離レベル、速さ、キャッシュ、投影、運用は、この repository の責務外とする。
