<!-- common: business-knowledge -->
<!-- document: out/取引履歴/business-knowledge.md -->
<!-- grill-log: grill-log/取引履歴.md -->
<!-- when-stopped: wallet-owner-gap -->

# 取引履歴の業務に固有の条件

この条件は、お題の viewpoints.md のうち、取引履歴の業務の業務知識で確かめられる観点を判断の型に書き直したものである。

### history-read-only

重み: 2

PASS：コマンドを持たないことが読み取れ、取引の一覧とある時点の残高のそれぞれについて、誰が見られ、何をどの順で見せるかを書いている。

FAIL：コマンドやこの業務が書く事実を作っている。または、表示対象か並び順が欠けている。
