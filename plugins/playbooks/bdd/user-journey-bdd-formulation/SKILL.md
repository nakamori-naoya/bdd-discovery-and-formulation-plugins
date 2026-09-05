---
name: formulate-user-journey
description: 既存のユーザー目的達成BDDを、目的、両端、場面接続、分岐、中断再開、役割移譲、完了の観測可能性から反証し、確認済みの理解と未決を同じ正本へ戻す。「このUser Journey BDDを深掘りして」「目的達成シナリオの抜けを検査して」と言われたときに使う。新規正本、ユースケース、ドメインルール、データモデル、テスト仕様は作らない。
---

# 既存のユーザー目的達成BDDを深化する

**これは既存正本のformulationである。** 既存のユーザー目的達成BDDを受け、Journeyである条件を再判定し、欠落と反例を確認したうえで同じパスへ更新する。

**これは新規発見、ユースケース設計、UX Journey map、domain-rule、data model、UIフロー、テスト仕様ではない。** 入力された既存正本以外を新しく作らず、別の問いは適切な正本へ返す。

## 0. プラグインrootを決める

```bash
BUNDLE_ROOT="${CLAUDE_PLUGIN_ROOT:-/absolute/path/to/this/plugin}"
if [ -d "${BUNDLE_ROOT}/playbooks/bdd/user-journey-bdd-formulation" ]; then
  PLUGIN_ROOT="${BUNDLE_ROOT}/playbooks/bdd/user-journey-bdd-formulation"
else
  PLUGIN_ROOT="${BUNDLE_ROOT}"
fi
```

## 1. 工程を解決する

```bash
CFG_FILE=$(bash "${PLUGIN_ROOT}/scripts/prepare.sh" "$(pwd)") || exit 2
trap 'rm -f "$CFG_FILE"' EXIT
```

解決済みYAMLが空、依存が欠けている、設定が更新契約を外している場合は先へ進まない。[実行指示書](references/execution-guidance.md)を必ず読む。[入力根拠](references/input-grounding.md)も全工程へ適用する。

## 2. 既存正本とJourney境界を確かめる

入力されたpathがsymlinkではない既存fileでなければ停止する。`map-user-journey`の「何であるか／何ではないか」を適用し、既存内容が対象システム一つの責任、感情と接点、業務判断、保存設計、テスト実行へ変質していれば、同じ資料へ足さず適切な正本と移動対象を報告する。

## 3. 反証して同じ本文へ戻す

[Formulationの反証観点](references/formulation-probes.md)、[Journeyの構造](references/journey-structure.md)、[場面のBDD](references/scenario-writing.md)、[BDDの前提](references/scenario-premises.md)を読む。目的と完了の不一致、到達不能な接続、分岐後の未合流、中断後の再開不能、役割移譲の欠落、早期終了を一つずつ反証する。

入力根拠から決まらない点はgrillで一問ずつ確認する。回答前に後続の更新へ進まない。確認済み内容は既存本文へ戻し、回答されない点は確認相手と影響範囲を持つ未決として戻す。

## 4. 検査して同一パスを更新する

```bash
python3 "${PLUGIN_ROOT}/scripts/scenario.py" check \
  --config "$CFG_FILE" --file <revised-body.md> --matrix <condition-matrix.json>
python3 "${PLUGIN_ROOT}/scripts/update-guard.py" \
  --existing <existing-user-journey-bdd.md> --output <requested-output.md>
```

どちらかが失敗した場合は既存正本を変更しない。通った本文だけをwrite-docの`replace-existing-target`として同じパスへ渡す。

## 5. 報告する

- 更新した正本の絶対パス
- 追加・変更・削除した場面と、その根拠
- 反証して維持した境界
- ユースケース、UX、domain、data model、実装、テストへ返した事項
- 未決と、確定に必要な情報

新規資料を作った場合、または既存正本以外を変更した場合は完了と報告しない。
