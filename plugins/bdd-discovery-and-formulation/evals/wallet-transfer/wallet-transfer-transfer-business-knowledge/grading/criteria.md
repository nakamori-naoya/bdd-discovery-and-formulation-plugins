<!-- common: business-knowledge -->
<!-- document: out/送金/business-knowledge.md -->
<!-- grill-log: grill-log/送金.md -->
<!-- when-stopped: wallet-owner-gap -->

# 送金の業務に固有の条件

この条件は、お題の viewpoints.md のうち、送金の業務の業務知識で確かめられる観点を判断の型に書き直したものである。

### transfer-deadline

重み: 3

送金には、利用者の行いではなく時間の到来で起きる移り変わりがある。

PASS：その移り変わりに、業務上判断する者の名前と、期限の手前・ちょうど・超えの結果が書かれている。期限の数え方が要件で一つに決まらないなら、一方を仮置きの印なしに断定していない。

FAIL：時間の到来で起きる移り変わりに判断する者が無い、境界の結果が無い、または二つに読める数え方の一方を仮置きの印なしに断定している。
