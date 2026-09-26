# Validation

受入検査は次で実行する。

```bash
bash scripts/validate.sh
bash /Users/naoya-nakamoriq/Documents/Github/harness-pluginsv2/scripts/validate.sh "$(pwd)"
```

`scripts/validate.sh`は、兄弟checkout`../harness-tools/tools/`の保守tool（`validate-plugin-repository.py`とその`--self-test`、`test-hardening.py --repository`）でpackageの配置とmanifestを検査し、三つの検査スクリプトを正例・反例・境界例にかける。`scripts/test-business-knowledge.sh`は`business_knowledge.py`を、`scripts/test-immutable-model.sh`は`immutable_model.py`を、`scripts/test-query-model.sh`は`query_model.py`を確かめる。fixtureは`scripts/fixtures/`の下の`business-knowledge/`、`command-data-model/`、`query-data-model/`にある。`../harness-tools/`が無ければexit 2で止まる。

検査が見るのは、宣言と名前から一意に決まることだけである。SKILL本文の判断や、作られた資料の業務上の正しさは、対象を読んで評価する。

Codexの`plugin-creator` validatorはPyYAMLを含む隔離環境で`bash scripts/validate-plugin-creator.sh`として別途実行する。

## 検証の eval

skill が要件だけから正しい資料を作れるかは、`plugins/bdd-discovery-and-formulation/evals/` の下のケースで確かめる。一つのケースは、一つのお題の一つの業務の一つの資料である。実行は `claude plugin eval` が受け持ち、資料の出来の採点は、作業したエージェントとは別の Claude（採点役）が、条件ごとに判定と根拠の引用と理由を書いて受け持つ。今は、X のクローン、電子チケット、つむぎウォレット、経費精算、読書ツールの五つのお題について、業務の分け方の業務ごとに業務知識のケースを置いている。

採点を plugin eval の `llm` grader に任せないのは、judge が資料一本しか読めず、PASS か FAIL の一語しか返さないからである。資料を要件や grill の記録と突き合わせる条件で、judge は判定を誤り、その理由も残らなかった。plugin eval の `graders/` には、読まずに判定できるもの（資料と記録ができたか、skill と検査の script と template と grill を使ったか）だけを置く。

置き場は次のとおりである。`evals/criteria/` には、採点役への指示 `brief.md` と、資料の種類ごとの共通の条件（今は `business-knowledge.md`）を置く。`evals/scaffold.sh` は、渡されたお題の要件と業務の分け方と、write-doc と grill の skill を作業場所へ置く。write-doc と grill は隔離環境に入らないので、兄弟 checkout `../write-doc-plugins/` と `../grill-plugins/` から写し、無ければ exit 2 で止まる。`evals/<お題>/` には、お題の要件と業務の分け方 `materials/` と、お題のどの業務にも当てる条件 `criteria.md`（あれば）を置く。`evals/<お題>/<ケース>/` には、実行の指示 `prompt.md` と `case.yaml`、共通の準備を呼ぶ `scaffold.sh`、`graders/`、ケースに固有の条件 `grading/criteria.md` を置く。お題とケースの条件は、お題の viewpoints.md のうち業務知識で確かめられる観点を、判断の型に書き直したものである。固有の条件の先頭の注記が、共通の条件の種類と、判定する資料と記録のパスを決める。`when-stopped` の注記に並べた条件は、実行の担当が資料を作らずに止まったとき、報告と記録だけで判定し、点数はその条件だけで出す。止まることが正しい答えになりうるケースのためである。採点役を確かめる資料と期待する判定は `grading/calibration/` に置く。

実行の指示では、依頼元として、業務の分け方に足りない答え（業務をまたぐ問いの答え、役割の語の持ち主など）を推奨の仮置きで進めるよう渡し、分け方の一覧に無い業務が要るときだけ skill の指示どおりに止まらせる。お題の分け方は、skill が求める答えをすべては持っていないので、仮置きを許さないと、ほとんどの担当が書き始める前に止まる。

実行は次のとおりである。skill が資料と記録を書き、検査の script を実行するので、書き込みと shell の許可を渡す。`--scaffold` は、ケースの `scaffold.sh` をあなたの権限で実行するので、この repository のケースにだけ使う。`--case` は最後に渡した一つだけが効き、`[...]` の文字の集まりも使えないので、複数のケースは別々のコマンドで並べて動かす。

```bash
cd plugins/bdd-discovery-and-formulation
claude plugin eval . --case x-clone-follow-business-knowledge \
  --runs 1 --ablation none --keep-temp \
  --scaffold --allow-tools Write Edit Bash \
  --max-cost-usd 5 --no-publish
```

採点は、実行が残した一時ディレクトリ（`kept temp:` の行に出る）を渡して次で行う。採点役は Read、Glob、Grep だけを使い、成果物、実行の担当の最後の報告、`materials/` を写した採点用のディレクトリの外は読めない。期待する判定を三つ目の引数に渡すと、条件ごとに突き合わせて一致の数を出す。

```bash
bash scripts/grade-eval.sh plugins/bdd-discovery-and-formulation/evals/<お題>/<ケース> /private/tmp/e-XXXXXX
```

採点は、全部の条件が PASS かどうかではなく、点数で見る。完璧な資料は作れず、ある程度の見逃しは残る、という前提に立つからである。採点役は既定で3回、互いに独立に回し、条件ごとに多数決を取る。多数決の判定に条件の重みを掛けて足し、100点満点の点数にする。重みは、利用者の原則の芯に当たる条件（推測で埋めない、業務と仕組みの線引き、業務の言葉、拒む理由の結び）を3、行いごとの決まりの骨組みを2、細部を1とし、条件の見出しの下に書く。

点数には目安の帯を置く。85点以上は、下流の資料へそのまま渡せる「実用に足る」、70点以上85点未満は、減点の条件を直せば使える「手直しで使える」、70点未満は「作り直しが要る」である。帯は合否ではない。報告には、点数と一緒に、減点の大きかった条件と採点役の根拠を並べる。採点の報告は `evals/results/grading/<ケース>-<時刻>.md` に、各回の判定は同じ名前の `.vote<N>.md` に残る。多数決と点数は `scripts/grade_eval_score.py` が出すので、各回の結果から点数だけを出し直すときは `python3 scripts/grade_eval_score.py evals/results/grading/<ケース>-<時刻> 3` を使う。

条件や採点役への指示を変えたら、`grading/calibration/` の資料に採点役をかけ、期待する判定を再現できるかを先に確かめる。較正の資料は作業場所と同じ形（`out/` と `grill-log/`）で置いてあるので、そのディレクトリを二つ目の引数に渡せばよい。実行と採点の結果は `evals/results/` に書かれ、git の管理から外してある。
