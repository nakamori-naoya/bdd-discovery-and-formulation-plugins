<!-- common: business-knowledge -->
<!-- document: out/支払/business-knowledge.md -->
<!-- grill-log: grill-log/支払.md -->

# 支払の業務に固有の条件

この条件は、お題の viewpoints.md のうち、支払の業務の業務知識で確かめられる観点を判断の型に書き直したものである。

### payroll-handoff-outside

重み: 3

給与計算システムへの受け渡しは、失敗しても支払の確定を取り消さず、結果は遅れて届く。

PASS：受け渡しの依頼と結果の待ち方を、支払の確定が成り立つ条件や結果に入れず、確定を取り消さない決まりは業務の決まりとして残している。

FAIL：受け渡しの結果を確定の条件にしている、または確定を取り消さない決まりを落としている。
