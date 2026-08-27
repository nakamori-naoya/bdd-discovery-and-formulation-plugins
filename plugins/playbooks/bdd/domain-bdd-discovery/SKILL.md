---
name: discover-domain
description: コアドメインの業務知識と代表的な振る舞いを共通理解にし、BDDを含むdomain-ruleの正本を1本作る。業務イベント、事前状態、アクター、判断、次状態を整理する。「業務知識をBDD付きで整理して」「コアドメインを発見して」と言われたとき、実装やQA反証へ進む前に使う。
---

# domain-bdd-discovery（共通理解を正本にする）

**作りを全部やめても残るものだけを残す。** 画面も保存も手順も、作り替えれば変わる。変わるものを正本へ入れると、作りを変えるたびに正本が腐る。

**探求が先で、記述は後である。** 何が起きるのかを知らないまま型を埋めにいくと、型の穴を埋めるための作り話が入る。

## 0. プラグイン root を決める

<!-- BEGIN shared:skill-entry/root-block -->
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
```

`PLUGIN_ROOT`は配布物rootの絶対パスである。単一skill pluginではこの`SKILL.md`があるdirectory、複数skill pluginでは`skills/<skill>/`の2つ上に当たる。Claude Codeでは`${CLAUDE_PLUGIN_ROOT}`が自動展開される。
<!-- END shared:skill-entry/root-block -->

## 1. 工程を解決して、書かれた順に実行する

<!-- BEGIN shared:skill-entry/config-load -->
```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

**このコマンドは説明例ではない。必ず実行する。** 解決済みYAMLが空なら先へ進まない。設定ファイルを直接読んで代用しない。

本文中の `${...}` は解決済みYAMLのプロパティである。使用時に `yq -er` で読み、欠落または `null` なら停止する。
<!-- END shared:skill-entry/config-load -->

`${.instructions.execution.directive}` に従い、`${.playbook.contract}` と `${.deps}` を工程へ渡し、成果は `${.playbook.out_dir}` へ集める。契約の役を確認するときだけ[役の契約](references/roles.md)を読む。

[実行指示書](references/execution-guidance.md)を必ず読む。`playbook.yml`は工程順・依存・入出力を決定し、実行指示書は背景・前提・目的と各skillで意識することを補う。grill工程には実行指示書のdomain固有の文脈を与え、grill自身にdomainの観点を求めない。

**各工程を呼ぶときは `--scope=${.resolution.scope_root}` を必ず渡す。**この段取りを通るときだけ効く設定がそこにある。渡さなければ効かない。入れ子の段取りへは、受け取ったものをそのまま渡す（自分の名前で作り直さない）。

**exit 2 で止まったら先へ進まない。** 何が起きたかは `scripts/resolve.sh` の冒頭に書いてある。

## 2. 利用者が持っている知識から始める

**題材と、利用者がすでに知っていることを先に受け取る。** [入力に根拠づける規律](references/input-grounding.md)に従い、利用者の発言、明示された資料、grillで確認した決定にない業務用語・イベント・概念を作らない。不明点や深掘りはgrill工程で1問ずつ確認し、`grounded_input`にならない仮説を後続へ渡さない。

受け取ったものは、そのまま事実として扱わない。**誰が確かめたのかで確からしさが変わる。** `${.playbook.contract.confidence}` の語で区別したまま先へ渡す。

## 3. 線が引けるまで、書く工程へ進まない

**「どこまでが業務の話か」が決まらないうちに書き始めると、実装の話が混ざったまま正本になる。** 線引きの工程を飛ばさない。

`${.playbook.requirements.exclude_implementation}` が `true` のとき、実装の関心を落とす工程は外せない。落とせない工程を落とすと、解決の時点で止まる。

## 4. コアの代表的な振る舞いを共通理解にする

**支援・汎用まで同じ丁寧さで問い詰めると、いちばん大事なところへ手が回らない。** 問い詰める工程へは、コアと判定した範囲を渡す。

[振る舞い発見](references/behavior-discovery.md)、[アクターとステークホルダー](references/actors-and-stakeholders.md)、[業務ルール](references/domain-rules.md)、[ユビキタス言語](references/ubiquitous-language.md)、[共通理解を作る問い](references/questions.md)を読み、コアについて次を一続きで確かめる。

```text
役割の目的 + 協働役割 + 事前状態 + 業務イベント + 条件
→ 判断権者の業務判断 → 観測できる結果 + 次状態 + 引継ぎ + 後続イベント
```

典型、既知の代替、既知の拒否を代表BDDにする。境界値、同値分割、順序逆転、重複、同時実行などを体系的に反証しない。それは共通理解を作った後のformulationが担う。

## 5. 確からしさを落とさずに束ねる

`scripts/map.py`で振る舞い断面と代表BDDを記録する。事実、線引き、決定、振る舞い、代表BDDのどれかが欠けていたら束ねない。[成果物の形](references/discovery-deliverable.md)に沿い、`${.playbook.document_type}`の`domain-rule`を`output_format=${.playbook.output_format}`で1本だけ保存する。

## 6. 報告する

- BDDを含む正本のパスと、扱った題材
- コアの代表的な振る舞い断面
- **未確認のまま残った事実と、誰に聞けば確かめられるか**
- スコープ外へ落としたものと、その理由
- まだ決まっていない論点

設定形式は[README](README.md)を参照する。モデルと推論の強さは決定的でないため設定に持たない。
