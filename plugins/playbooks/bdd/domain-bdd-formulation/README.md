# domain-bdd-formulation

最初に利用者の説明と既存資料を意味から評価し、コアドメインの代表的な共通理解がまだ無ければ`domain-bdd-discovery`を案内して終了します。語の有無やscriptでは判定せず、定式化へ進める入力だけをQA観点で深化させます。

既存のdomain-rule資料でコアドメインと線引きされた範囲だけをQA観点で反証し、確認済みの業務理解とBDDを同じ資料へ戻すplaybookです。

焦点はコアドメインの業務判断に固定されています。

出力は入力と同じパスにある、深化済みのMarkdown `domain-rule`資料です。`output_format: markdown`は固定で、HTMLの既存資料は同一パス更新の対象にしません。境界値・同値分割・状態遷移・順序・重複・同時実行などは反証に使い、QA手法の解説として本文へ残しません。

設定を上書きする場合は`.harness-plugins/domain-bdd-formulation.config.yml`へ`playbook.yml`と同じ全項目を記載します。`focus`と`output_format`は変更できません。

新規資料は作りません。確認できない新しい決まりは代理回答せず、既存資料の未回答の問いへ戻します。支援・汎用は反証対象へ広げません。
