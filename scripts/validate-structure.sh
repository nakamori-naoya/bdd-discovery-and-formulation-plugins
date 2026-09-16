#!/usr/bin/env bash
# Scenario: BDD packageが6公開入口と4内部skillだけを配布し、入口のtoolが正例・反例・境界例で決まった結果を返す
#
# 正本: 両marketplace、両runtime manifest、入口の playbook.yml、shared/quality-engineering と shared/consumer-contract の複製元。
# 入力: このrepositoryの配布物と、ここで作る fixture（検査toolへは標準入力または正本pathで渡し、tool専用の一時fileは置かない）。
# 合格述語: identityと集合の一致、複製のbyte一致、外部依存の宣言形、各toolの self-test と exit code と診断。
# 意味評価として残す範囲: SKILL本文の判断規律、参照資料の内容、生成された資料の業務上の正しさ。
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PACKAGE="$ROOT/plugins/bdd-discovery-and-formulation"
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bdd-discovery-and-formulation-structure.XXXXXX") || exit 2
trap 'rm -rf "$TMP_ROOT"' EXIT
passed=0 failed=0
pass() { printf 'PASS: %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf 'FAIL: %s\n' "$1"; failed=$((failed + 1)); }
# 反例の合格述語は「toolが違反として exit 1 を返す」だけにする。exit 2（入力を読めない）や 127（未定義の関数・変数）を拒否と誤認しない。
rejects() { "$@" >/dev/null 2>&1; [ "$?" -eq 1 ]; }

for cmd in jq yq python3 bash cmp find sort diff rg; do
  command -v "$cmd" >/dev/null 2>&1 && pass "command $cmd" || fail "command $cmd が無い"
done

entries='discover-domain formulate-domain discover-data-model formulate-data-model discover-user-journey formulate-user-journey'
internals='explore-events map-user-journey write-persistence-scenarios design-data-model'

# ── marketplace と manifest の identity ──────────────────────────────────
if jq -e '.name=="bdd-discovery-and-formulation" and (.plugins|length==1) and .plugins[0].name=="bdd-discovery-and-formulation" and .plugins[0].source.path=="./plugins/bdd-discovery-and-formulation"' "$ROOT/.agents/plugins/marketplace.json" >/dev/null \
  && jq -e '.name=="bdd-discovery-and-formulation" and (.plugins|length==1) and .plugins[0].source=="./plugins/bdd-discovery-and-formulation"' "$ROOT/.claude-plugin/marketplace.json" >/dev/null; then
  pass "両marketplaceの配布境界（./plugins/bdd-discovery-and-formulation）"
else
  fail "両marketplaceの配布境界"
fi
if jq -e 'all(.plugins[]; .policy.installation=="AVAILABLE" and .policy.authentication=="ON_INSTALL" and (.category|length>0))' "$ROOT/.agents/plugins/marketplace.json" >/dev/null; then
  pass "Codex marketplaceのpolicy"
else
  fail "Codex marketplaceのpolicy"
fi
version=$(jq -r '.plugins[0].version' "$ROOT/.agents/plugins/marketplace.json")
if jq -e --arg v "$version" '.name=="bdd-discovery-and-formulation" and .version==$v' "$PACKAGE/.codex-plugin/plugin.json" "$PACKAGE/.claude-plugin/plugin.json" >/dev/null \
  && jq -e --arg v "$version" '.plugins[0].version==$v' "$ROOT/.claude-plugin/marketplace.json" >/dev/null; then
  pass "package manifest identity（version ${version}）"
else
  fail "package manifest identity"
fi
if diff <(jq -S 'del(.interface)' "$PACKAGE/.codex-plugin/plugin.json") <(jq -S 'del(.interface)' "$PACKAGE/.claude-plugin/plugin.json") >/dev/null; then
  pass "両runtime manifestはinterface以外が同一"
else
  fail "両runtime manifestの差分"
fi

# ── 公開入口と内部skillの集合 ────────────────────────────────────────────
printf '%s\n' $entries | sort > "$TMP_ROOT/expected-entries"
jq -r '.skills[] | ltrimstr("./skills/")' "$PACKAGE/.claude-plugin/plugin.json" | sort > "$TMP_ROOT/manifest-entries"
find "$PACKAGE/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort > "$TMP_ROOT/dir-entries"
diff -u "$TMP_ROOT/expected-entries" "$TMP_ROOT/manifest-entries" >/dev/null && diff -u "$TMP_ROOT/expected-entries" "$TMP_ROOT/dir-entries" >/dev/null \
  && pass "公開入口6つ = manifest skills = skills/直下" || fail "公開入口の集合"
printf '%s\n' $internals | sort > "$TMP_ROOT/expected-internals"
jq -r '.metadata.harness.internalPlugins | to_entries[] | select(.value=="./internal/"+.key) | .key' "$PACKAGE/.claude-plugin/plugin.json" | sort > "$TMP_ROOT/manifest-internals"
find "$PACKAGE/internal" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort > "$TMP_ROOT/dir-internals"
diff -u "$TMP_ROOT/expected-internals" "$TMP_ROOT/manifest-internals" >/dev/null && diff -u "$TMP_ROOT/expected-internals" "$TMP_ROOT/dir-internals" >/dev/null \
  && pass "内部skill4つ = internalPlugins = internal/直下" || fail "内部skillの集合"
if jq -e '.metadata.harness | (has("playbooks")|not) and (has("implements")|not) and (has("installationSurface")|not) and .marketplace=="bdd-discovery-and-formulation" and (.contractVersion|type=="number")' "$PACKAGE/.claude-plugin/plugin.json" >/dev/null; then
  pass "CONTRACT.mdを持たないpackageはplaybooks / implementsを宣言しない"
else
  fail "metadata.harnessの形"
fi
[ "$(find "$PACKAGE" -name CONTRACT.md | wc -l | tr -d ' ')" = "0" ] && pass "公開playbook契約（CONTRACT.md）を持たない" || fail "CONTRACT.mdがあるのにplaybooksが無い"
[ "$(find "$PACKAGE" -type d \( -name .claude-plugin -o -name .codex-plugin \) | wc -l | tr -d ' ')" = "2" ] && pass "runtime manifestはpackage rootにだけ" || fail "nested runtime manifestが残っている"
[ "$(find "$PACKAGE" -name SKILL.md | wc -l | tr -d ' ')" = "10" ] && pass "SKILL.mdは公開6本と内部4本だけ" || fail "SKILL.mdの本数"

for name in $entries $internals; do
  if [ -d "$PACKAGE/skills/$name" ]; then dir="$PACKAGE/skills/$name"; else dir="$PACKAGE/internal/$name"; fi
  declared=$(awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} NR>1 && /^name: /{sub(/^name: /,""); print; exit}' "$dir/SKILL.md")
  [ "$declared" = "$name" ] && pass "$name SKILL.md name = directory名" || fail "$name SKILL.md name ($declared)"
done

# ── 隣接 playbook.yml: 外部依存の宣言形と参照の実在 ───────────────────
for directory in $entries; do
  pb="$PACKAGE/skills/$directory"
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e --arg n "$directory" '.version==2 and .name==$n and (.requires|length>0) and all(.requires[]; (keys|sort)==["marketplace","plugin"] and .marketplace!="bdd-discovery-and-formulation" and .plugin==.marketplace)' >/dev/null; then
    pass "$directory playbook.yml name / version / requiresは外部packageだけ"
  else
    fail "$directory playbook.yml の宣言"
  fi
  if yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -e '
      . as $root |
      ([$root.requires[].plugin]) as $external |
      (all($root.steps[]; (.skill // "") as $s | ($external | index($s)) == null)) and
      (all($root.steps[]; (.playbook // null) as $b | $b == null or ($external | index($b)) != null)) and
      ([$root.steps[] | select(.playbook != null)] | length > 0) and
      ([$root.steps[] | select(.playbook == "write-doc")] | length > 0) and
      all($root.steps[] | select(.playbook == "write-doc"); (.input.document_type|type=="string") and (.input.document_type|test("^[a-z-]+$")))' >/dev/null; then
    pass "$directory 外部依存はplaybook:工程だけ、write-docのdocument_typeはliteral"
  else
    fail "$directory が外部依存をskill:で指すか、document_typeがliteralでない"
  fi
  while IFS= read -r script; do
    [ -f "$pb/$script" ] && pass "$directory steps script $script が実在" || fail "$directory steps script $script が無い"
  done < <(yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -r '.steps[] | select(.script) | .script')
  while IFS= read -r skill; do
    [ -f "$PACKAGE/internal/$skill/SKILL.md" ] && pass "$directory steps skill $skill は内部skill" || fail "$directory steps skill $skill が内部skillに無い"
  done < <(yq -o=json -I=0 '.' "$pb/playbook.yml" | jq -r '.steps[] | select(.skill) | .skill')
  [ -s "$pb/references/execution-guidance.md" ] && rg -F '[実行指示書](references/execution-guidance.md)' "$pb/SKILL.md" >/dev/null \
    && pass "$directory は実行指示書を入口から参照" || fail "$directory の実行指示書参照"
  cmp -s "$ROOT/shared/quality-engineering/scenario-premises.md" "$pb/references/scenario-premises.md" && pass "$directory 前提規律同期" || fail "$directory 前提規律同期"
  cmp -s "$ROOT/shared/quality-engineering/scenario_matrix.py" "$pb/scripts/scenario_matrix.py" && pass "$directory 条件マトリクスvalidator同期" || fail "$directory 条件マトリクスvalidator同期"
  cmp -s "$PACKAGE/skills/discover-domain/references/nested-playbook.md" "$pb/references/nested-playbook.md" && pass "$directory 入れ子の段取りの呼び方同期" || fail "$directory 入れ子の段取りの呼び方同期"
done
for internal in write-persistence-scenarios; do
  cmp -s "$ROOT/shared/quality-engineering/scenario_matrix.py" "$PACKAGE/internal/$internal/scripts/scenario_matrix.py" && pass "$internal 条件マトリクスvalidator同期" || fail "$internal 条件マトリクスvalidator同期"
done
# ── 同名 reference の byte 一致 ──────────────────────────────────────────
# 正本: shared/{domain-modeling,data-modeling,quality-engineering,consumer-contract}/*.md と、package 配下の references/ にある同名 file 群
# 入力: package 配下の *.md（SKILL.md、および入口ごとの文書である execution-guidance.md / focus.md を除く）
# 正規化: basename でグループ化し、cmp で byte 比較する。shared に同名があればそれを基準に、無ければグループ内の全 file を互いに比較する
# 合格述語: 同じ basename を持つ file はすべて byte 一致する
# 失敗時の診断: 一致しない file の path を1行ずつ出す
# 正例: 6入口の nested-playbook.md と scenario-premises.md、内部 skill の actors-and-stakeholders.md が一致する
# 反例: 旧文言のままの scenario-premises.md が内部 skill に残る
# 境界例: 別の文書は同名にしない（map-user-journey の journey-boundary.md / journey-map-structure.md / journey-concept-map.md）。入口ごとの execution-guidance.md / focus.md は入力から除く
# 意味評価として残す範囲: 複製が本当に同じ知識であるべきか、入口ごとの文書の内容が入口の目的に合うか
same_name_failed=0
while IFS= read -r base; do
  source=""
  for candidate in "$ROOT/shared/domain-modeling/$base" "$ROOT/shared/data-modeling/$base" "$ROOT/shared/quality-engineering/$base" "$ROOT/shared/consumer-contract/$base"; do
    [ -f "$candidate" ] && source="$candidate" && break
  done
  [ -n "$source" ] || source=$(find "$PACKAGE" -type f -name "$base" | sort | head -1)
  while IFS= read -r copy; do
    cmp -s "$source" "$copy" || { echo "  differs: $copy (基準: $source)"; same_name_failed=1; }
  done < <(find "$PACKAGE" -type f -name "$base")
done < <(find "$PACKAGE" -type f -name '*.md' ! -name SKILL.md ! -name execution-guidance.md ! -name focus.md -exec basename {} \; | sort | uniq -d)
[ "$same_name_failed" -eq 0 ] && pass "同名の reference（shared 複製を含む）はすべて byte 一致" || fail "同名 reference の差分"
cmp -s "$PACKAGE/skills/discover-domain/scripts/actor-coverage.py" "$PACKAGE/skills/formulate-domain/scripts/actor-coverage.py" && pass "actor-coverage.py 2入口で同一" || fail "actor-coverage.py の差分"
cmp -s "$PACKAGE/skills/discover-user-journey/scripts/scenario.py" "$PACKAGE/skills/formulate-user-journey/scripts/scenario.py" && pass "user-journey scenario.py 2入口で同一" || fail "user-journey scenario.py の差分"
cmp -s "$PACKAGE/skills/formulate-domain/scripts/update-guard.py" "$PACKAGE/skills/formulate-user-journey/scripts/update-guard.py" \
  && cmp -s "$PACKAGE/skills/formulate-domain/scripts/update-guard.py" "$PACKAGE/skills/formulate-data-model/scripts/update-guard.py" \
  && pass "update-guard.py 3入口で同一" || fail "update-guard.py の差分"

# 禁止参照形（root validatorと同じ4 token）が配布物に無い。README / docs は対象外。
if rg -n -e '\$\{\.' -e '<!-- BEGIN shared:' -e 'CLAUDE_PLUGIN_ROOT' -e 'BUNDLE_ROOT' "$PACKAGE" >/dev/null; then
  fail "禁止参照形が配布物に残っている"
else
  pass "禁止参照形なし"
fi

# 外部依存の実体を同梱していないこと。名前は playbook.yml の requires から引く。
external_plugins=$(for pb in "$PACKAGE"/skills/*/playbook.yml; do
    yq -o=json -I=0 '.' "$pb" | jq -r '.requires[] | .plugin'
  done | sort -u)
bundled=""
for name in $external_plugins; do
  if find "$PACKAGE" -type d -name "$name" | rg . >/dev/null; then bundled="${bundled} ${name}"; fi
done
[ -z "$bundled" ] && pass "外部依存の実体を同梱しない" || fail "外部pluginを同梱:${bundled}"

# ── 条件マトリクス: 正例・境界例・反例 ───────────────────────────────────
matrix_validator="$ROOT/shared/quality-engineering/scenario_matrix.py"
matrix_good="$TMP_ROOT/matrix-good.json"
cat > "$matrix_good" <<'EOF'
{"scenarios":[
  {"name":"成功","kind":"success","expected":"success","rule":"R","trigger":{"kind":"event","text":"受付が起きる"},"premises":[{"name":"A","text":"Aが成立","state":"satisfied","target":false,"source":"業務規則"}]},
  {"name":"単一失敗","kind":"single_failure","expected":"failure","rule":"R","trigger":{"kind":"action","text":"確認する"},"premises":[{"name":"A","text":"Aが成立","state":"satisfied","target":false,"source":"業務規則"},{"name":"B","text":"Bが不成立","state":"unsatisfied","target":true,"source":"業務規則"}],"note":{"rule":"R","reason":"Bに抵触"}},
  {"name":"境界","kind":"boundary","expected":"success","rule":"R","trigger":{"kind":"action","text":"判定する"},"premises":[{"name":"A","text":"Aが境界","state":"boundary","target":true,"source":"業務規則"}]},
  {"name":"組合せ","kind":"interaction","expected":"success","rule":"R","trigger":{"kind":"event","text":"同時に起きる"},"premises":[{"name":"A","text":"A","state":"satisfied","target":true,"source":"業務規則"},{"name":"B","text":"B","state":"satisfied","target":true,"source":"業務規則"}]}
]}
EOF
python3 "$matrix_validator" self-test >/dev/null && pass "scenario_matrix.py self-test（正例・反例・空stdin・不正JSON）" || fail "scenario_matrix.py self-test"
python3 "$matrix_validator" check < "$matrix_good" >/dev/null && pass "条件マトリクス代表ケース（stdin）" || fail "条件マトリクス代表ケース"
sed 's/"state":"satisfied","target":false/"state":"unsatisfied","target":false/' "$matrix_good" > "$TMP_ROOT/matrix-bad.json"
rejects python3 "$matrix_validator" check < "$TMP_ROOT/matrix-bad.json" && pass "条件マトリクスの暗黙前提を拒否（exit 1）" || fail "条件マトリクスの暗黙前提を拒否できない"
python3 "$matrix_validator" check </dev/null >/dev/null 2>&1; [ $? -eq 2 ] && pass "条件マトリクス: 空stdinはexit 2" || fail "条件マトリクス: 空stdinの終了code"

# ── domain の Gherkin検査: 量を品質gateにせず、表現契約だけを拒否する ─────
domain_formulation="$PACKAGE/skills/formulate-domain"
large_scenario="$TMP_ROOT/large-scenario.feature"
cat > "$large_scenario" <<'EOF'
Feature: 多数の結果と代表例を持つ業務規則
Scenario Outline: 必要な結果をすべて観測する
  Given <a> <b> <c> <d> <e> <f> <g> が前提である
  When 判定する
  Then 結果1を観測する
  And 結果2を観測する
  And 結果3を観測する
  And 結果4を観測する
  And 結果5を観測する
  And 結果6を観測する
  Examples:
    | a | b | c | d | e | f | g |
    | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
    | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
    | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
    | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
    | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
    | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
    | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
    | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
    | 9 | 9 | 9 | 9 | 9 | 9 | 9 |
    | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
    | 11 | 11 | 11 | 11 | 11 | 11 | 11 |
EOF
large_matrix="$TMP_ROOT/large-scenario-matrix.json"
cat > "$large_matrix" <<'EOF'
{"scenarios":[{"name":"必要な結果をすべて観測する","kind":"success","expected":"success","rule":"R","trigger":{"kind":"action","text":"判定する"},"premises":[{"name":"全条件","text":"<a> <b> <c> <d> <e> <f> <g> が前提である","state":"satisfied","target":false,"source":"業務規則"}]}]}
EOF
# fixtureはvalidate自身の一時directoryに置くが、toolへはSKILL.mdの手順と同じ形（本文はstdin、条件マトリクスは --matrix-json 引数）で渡す。
python3 "$domain_formulation/scripts/scenario.py" self-test >/dev/null && pass "domain scenario.py self-test（正例・反例・空stdin・不正JSON・引数欠落・旧引数拒否）" || fail "domain scenario.py self-test"
python3 "$domain_formulation/scripts/scenario.py" check --matrix-json "$(cat "$large_matrix")" < "$large_scenario" >/dev/null \
  && pass "step数とExamples行列数を品質gateにしない" || fail "量だけで正しいBDD構造を拒否"
broken_scenario="$TMP_ROOT/broken-large-scenario.feature"
sed 's/^  Then 結果1を観測する$/  When 結果1を観測する/' "$large_scenario" > "$broken_scenario"
rejects python3 "$domain_formulation/scripts/scenario.py" check --matrix-json "$(cat "$large_matrix")" < "$broken_scenario" \
  && pass "一つのWhenという表現契約を拒否側で検証（exit 1）" || fail "複数Whenを拒否できない"

# ── 誰が行えるかの網羅（actor-coverage.py）: self-test（正例・反例・境界例） ──
python3 "$PACKAGE/skills/discover-domain/scripts/actor-coverage.py" self-test >/dev/null \
  && pass "actor-coverage.py self-test（正例・反例・境界例）" || fail "actor-coverage.py self-test"

# ── ユーザー目的達成BDD（scenario.py）: write-docの user-journey-bdd 型の記法（Given: / And: / NOTE: Rule:）で正例を書く。
#    冒頭の段落は検査せず、場面・接続・NOTE・条件マトリクスだけ見る。
journey_discovery="$PACKAGE/skills/discover-user-journey"
good_story="$TMP_ROOT/good-user-journey-bdd.md"
cat > "$good_story" <<'EOF'
# 予約を完了する

予約者が希望する条件で予約を成立させるまでを扱う。予約者が希望条件を決めているところから始まり、成立した予約を予約者が確認できたら完了である。

## 場面 1: 希望を伝える

```gherkin
Given: 予約者が希望条件を決めている
When: 予約者が希望を伝える
Then: 希望に合う候補が示される
  And: 候補を選べる状態になる
```

**接続**: 示された候補を選べる状態になる

## 場面 2: 停止中の予約者は成立しない

```gherkin
Given: 予約者が候補を選べる
  And: 予約者は仮押さえ停止中である
When: 予約者が候補を選ぶ
Then: 予約は成立しない
  NOTE: Rule: 予約成立規則
    Source: [業務知識](../domain/予約.md#予約成立規則)
    Reason: 停止中顧客は新しい利用枠を確保できないため
```
EOF
good_matrix="$TMP_ROOT/good-user-journey-matrix.json"
cat > "$good_matrix" <<'EOF'
{"scenarios":[
  {"name":"希望を伝える","kind":"success","expected":"success","rule":"予約成立規則","trigger":{"kind":"action","text":"予約者が希望を伝える"},"premises":[{"name":"開始地点","text":"予約者が希望条件を決めている","state":"satisfied","target":false,"source":"予約資料"}]},
  {"name":"停止中の予約者は成立しない","kind":"single_failure","expected":"failure","rule":"予約成立規則","source":"[業務知識](../domain/予約.md#予約成立規則)","trigger":{"kind":"action","text":"予約者が候補を選ぶ"},"premises":[{"name":"候補を選べる","text":"予約者が候補を選べる","state":"satisfied","target":false,"source":"予約資料"},{"name":"停止中","text":"予約者は仮押さえ停止中である","state":"unsatisfied","target":true,"source":"予約成立規則"}],"note":{"rule":"予約成立規則","source":"[業務知識](../domain/予約.md#予約成立規則)","reason":"停止中顧客は新しい利用枠を確保できないため"}}
]}
EOF
python3 "$journey_discovery/scripts/scenario.py" self-test >/dev/null && pass "user-journey scenario.py self-test（正例・反例・空stdin・不正JSON・引数欠落・旧引数拒否）" || fail "user-journey scenario.py self-test"
journey_check() { python3 "$journey_discovery/scripts/scenario.py" check --matrix-json "$(cat "$2")" < "$1"; }
journey_check "$good_story" "$good_matrix" >/dev/null \
  && pass "ユーザー目的達成BDDをtemplate記法（Given: / NOTE: Rule:）で受理" || fail "ユーザー目的達成BDD正常系（template記法）"
nocolon_story="$TMP_ROOT/nocolon-user-journey-bdd.md"
sed -E 's/^(\s*)(Given|When|Then|And):\s*/\1\2 /' "$good_story" > "$nocolon_story"
journey_check "$nocolon_story" "$good_matrix" >/dev/null \
  && pass "コロン無しのGherkin記法も同じstepとして受理（境界例）" || fail "コロン無し記法"
bad_story="$TMP_ROOT/bad-user-journey-bdd.md"
sed 's/予約者が希望を伝える/予約者がAPIを呼び出す/' "$good_story" > "$bad_story"
semantic_matrix="$TMP_ROOT/semantic-user-journey-matrix.json"
sed 's/予約者が希望を伝える/予約者がAPIを呼び出す/' "$good_matrix" > "$semantic_matrix"
journey_check "$bad_story" "$semantic_matrix" >/dev/null 2>&1 \
  && pass "ユーザー目的達成BDDの語彙責務を機械判定しない" || fail "語の存在だけでユーザー目的達成BDDの意味を判定"
noconn_story="$TMP_ROOT/noconn-user-journey-bdd.md"
sed 's/^\*\*接続\*\*: .*$//' "$good_story" > "$noconn_story"
rejects journey_check "$noconn_story" "$good_matrix" && pass "場面の接続欠落を拒否（exit 1）" || fail "場面の接続欠落を拒否できない"
wrongnote_story="$TMP_ROOT/wrongnote-user-journey-bdd.md"
sed 's/^    Reason: .*$/    Reason: 違う理由/' "$good_story" > "$wrongnote_story"
rejects journey_check "$wrongnote_story" "$good_matrix" && pass "NOTE: Rule: 形のReasonと条件マトリクスの不一致を拒否（exit 1）" || fail "NOTEの不一致を拒否できない"

# ── formulation の同一パス更新（update-guard.py） ──────────────────────
existing="$TMP_ROOT/existing.md"; different="$TMP_ROOT/new.md"; cp "$good_story" "$existing"
python3 "$PACKAGE/skills/formulate-domain/scripts/update-guard.py" self-test >/dev/null && pass "update-guard.py self-test（同一実体・別path・symlink・欠落）" || fail "update-guard.py self-test"
for directory in formulate-domain formulate-user-journey formulate-data-model; do
  guard="$PACKAGE/skills/$directory/scripts/update-guard.py"
  python3 "$guard" check --existing "$existing" --output "$existing" >/dev/null && pass "$directory は同一パス更新を受理" || fail "$directory 同一パス更新"
  rejects python3 "$guard" check --existing "$existing" --output "$different" && pass "$directory は新規資料を拒否（exit 1）" || fail "$directory が新規資料を拒否できない"
done

# ── 物理設計の検査（rdb.py）: 指紋・機能根拠欄・必須欄。論理資料は正本path、物理設計本文はstdin ──
rdb="$PACKAGE/skills/formulate-data-model/scripts/rdb.py"
python3 "$rdb" self-test >/dev/null && pass "rdb.py self-test（正例・根拠欄欠落・根拠不正・local:受理・重複・空stdin・正本欠落・旧引数拒否・指紋不一致）" || fail "rdb.py self-test"
logical="$TMP_ROOT/logical.md"
printf '%s\n' '# RDB論理設計 — 予約' '## 論理テーブル定義' '### テーブル: reservation' '#### 列: id' '#### 列: slot' '#### 業務制約: 同じ利用枠に有効な予約は一つ' > "$logical"
digest=$(python3 "$rdb" fingerprint --model-file "$logical" | jq -r '.digest')
[ -n "$digest" ] && pass "rdb.py fingerprint" || fail "rdb.py fingerprint"
python3 "$rdb" fingerprint --model-file "$TMP_ROOT/missing-logical.md" >/dev/null 2>&1; [ $? -eq 2 ] && pass "rdb.py fingerprint: 正本pathの欠落はexit 2" || fail "rdb.py fingerprint: 正本欠落の終了code"
design="$TMP_ROOT/design.md"
cat > "$design" <<EOF
# RDB物理設計 — 予約
## 対象と論理設計
- 対象DBMS: PostgreSQL
- 対象バージョン: 16
- 論理モデル: logical.md
- 論理構造の指紋: sha256:$digest
## 物理制約
同じ利用枠に有効な予約は一つ を排他制約で守る
## 物理化の方針
x
## index
### index: reservation_slot_excl
- 対象: reservation(slot)
- 種類: GiST 排他
- 目的: 競合制御
- 列の順番: 単一列
- 対象Read・更新: 予約の作成
- 根拠: 対象版仕様
- 更新費用: 小
## トランザクションと分離レベル
### 分離性判断: 同時予約
- 同時に進む操作: 予約Aと予約B
- 許してはいけない結果: 同じ枠に二つの予約
- 発生し得る現象: 書き込みスキュー
- 選択する分離レベル: READ COMMITTED
- 併用する仕組み: 排他制約
- 対象バージョンでの確認: 実機
- 競合時の扱い: 中断して利用者へ返す
## パーティションと配置
なし
## 容量・性能・運用
x
## 採用するRDB機能
### 機能: 排他制約
- 採用箇所: reservation(slot)
- 利用可能な版: 9.0
- 根拠: https://www.postgresql.org/docs/16/
- 対象バージョンで確認したこと: 実機
## 物理設計の完了条件
x
## 未決
なし
## 代表的な読み取り
### Read-001: 空き枠を探す
- 利用者と目的: 予約者
- 入力・検索条件: 日付
- 結合: なし
- 並び順と上限: 開始時刻, 100
- 返す情報: slot
- 鮮度と一貫性: primary
- 想定件数: 1000
- SLO: p95 100ms
- 支えるindex: reservation_slot_excl
EOF
rdb_check() { python3 "$rdb" check --model-file "$logical" --product PostgreSQL --version 16 < "$1"; }
rdb_check "$design" >/dev/null && pass "rdb.py check 正例（stdin本文）" || fail "rdb.py check 正例"
sed '/^- 根拠: https:\/\/www.postgresql.org\/docs\/16\/$/d' "$design" > "$TMP_ROOT/design-noevidence.md"
rejects rdb_check "$TMP_ROOT/design-noevidence.md" && pass "根拠欄の無い機能を拒否（exit 1）" || fail "根拠欄の無い機能を拒否できない"
sed 's|^- 根拠: https://www.postgresql.org/docs/16/$|- 根拠: 読んだ気がする|' "$design" > "$TMP_ROOT/design-badevidence.md"
rejects rdb_check "$TMP_ROOT/design-badevidence.md" && pass "https / local: 以外の根拠を拒否（exit 1）" || fail "形の合わない根拠を拒否できない"
printf '%s\n' '#### 列: created_at' >> "$logical"
rdb_check "$design" > "$TMP_ROOT/rdb-drift.out" 2>&1; drift_code=$?
if [ "$drift_code" -eq 1 ] && rg -q '論理構造の指紋' "$TMP_ROOT/rdb-drift.out"; then
  pass "論理構造の変化を指紋不一致の診断で拒否（exit 1）"
else
  fail "論理構造の変化を指紋不一致の診断で拒否できない（exit ${drift_code}）"
fi

# ── 構文 ─────────────────────────────────────────────────────────────────
syntax_failed=0
while IFS= read -r script; do bash -n "$script" || syntax_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.sh' | sort)
[ "$syntax_failed" -eq 0 ] && pass "shell構文" || fail "shell構文"
if find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.sh' -print0 \
    | xargs -0 python3 -c '
import re, sys
pattern = re.compile(r"\$(?!\{)[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]")
found = 0
for path in sys.argv[1:]:
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            for match in pattern.finditer(line):
                print(f"{path}:{number}: {match.group(0)}")
                found = 1
sys.exit(found)
'; then
  pass "非ASCIIに接する裸の変数参照なし"
else
  fail "非ASCIIに接する裸の変数参照（\${VAR} で囲む）"
fi
python_failed=0
while IFS= read -r script; do PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile "$script" || python_failed=1; done < <(find "$ROOT/plugins" "$ROOT/scripts" "$ROOT/shared" -type f -name '*.py' | sort)
[ "$python_failed" -eq 0 ] && pass "Python構文" || fail "Python構文"

printf '\nStructure: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
