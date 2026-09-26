<!-- common: business-knowledge -->
<!-- document: out/リセール/business-knowledge.md -->
<!-- grill-log: grill-log/リセール.md -->

# リセールの業務に固有の条件

この条件は、お題の viewpoints.md のうち、リセールの業務の業務知識で確かめられる観点を判断の型に書き直したものである。

### resale-rights-move

重み: 2

PASS：元の持ち主の権利が失われる時点と、出品している間に何ができないかを、要件の文から書いている。

FAIL：権利が失われる時点か、出品中の扱いが書かれていない。

### resale-payout-outside

重み: 3

出品者への支払いは、外部へ依頼し、失敗しても諦めない。

PASS：支払いの依頼とその結果の待ち方を、リセールが成り立つ条件や結果に入れず、業務の外のどこへ置いたかを書いている。

FAIL：依頼の届き方や再試行を、業務の決まりや BDD の結果にしている。
