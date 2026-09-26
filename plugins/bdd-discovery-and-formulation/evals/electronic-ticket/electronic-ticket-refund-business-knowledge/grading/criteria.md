<!-- common: business-knowledge -->
<!-- document: out/払い戻し/business-knowledge.md -->
<!-- grill-log: grill-log/払い戻し.md -->

# 払い戻しの業務に固有の条件

この条件は、お題の viewpoints.md のうち、払い戻しの業務の業務知識で確かめられる観点を判断の型に書き直したものである。

### refund-to-whom

重み: 2

PASS：返す相手を役割の語で書き、要件が受け付けないとした場合を拒む理由にしている。

FAIL：返す相手が役割として書かれていない、または要件が受け付けないとした場合が拒む理由になっていない。

### refund-request-outside

重み: 3

PASS：返金の依頼とその結果の待ち方を、払い戻しが成り立つ条件や結果に入れず、業務の外のどこへ置いたかを書いている。

FAIL：返金の依頼の届き方や再試行を、業務の決まりや BDD の結果にしている。
