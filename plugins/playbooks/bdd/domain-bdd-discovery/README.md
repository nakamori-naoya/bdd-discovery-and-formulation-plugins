# domain-bdd-discovery

**コアドメインの業務知識と代表的な振る舞いを共通理解にし、BDDを含む正本を1本作る。** 洗い出す・線を引く・詰める・振る舞いを記録する・書くを、この順で通す。

**作りを全部やめても残るものだけを残す。** 画面・保存・境界のやりとり・手順の組み立ては正本へ入れない。

正本は`output_format: markdown`に固定する。呼び出し先のdoc-render設定がHTMLでも、BDD playbookの資料成果物はMarkdownで保存する。

## 工程

| # | 工程 | 何を確定させるか |
|---|---|---|
| 1 | 洗い出し | 業務で起きる事実と、その確からしさ |
| 2 | 線引き | どこまでが業務の話か。そのうちどこがコアか |
| 3 | 問い詰め | コアの内側の曖昧さ。決めたことと未決 |
| 4 | 振る舞い記録 | 事前状態・業務イベント・判断・次状態と代表BDD |
| 5 | 束ね | 事実・線引き・決定・振る舞いを1つの素材へ |
| 6 | 資料化 | `domain-rule`の型でBDDを含む正本を保存する |

**1が終わる前に2へ進まない。** 何が起きるのかを知らないまま線を引くと、知っている範囲だけがコアになる。

素材の役は[references/roles.md](references/roles.md)を正本とする。

## 必要なもの

このrepository外では、次のpluginがインストール済みである必要がある。欠けていたら停止し、黙って劣化した結果を出さない。

- `grill@grill`
- `write-doc@write-doc`

## 設定

同梱の `playbook.yml` が既定。`<repo>/.harness-plugins/domain-bdd-discovery.config.yml` を置くと**丸ごと差し替わる**（混ぜない）。

```yaml
version: 1
name: domain-bdd-discovery
output_format: markdown
contract:
  material_roles: [業務イベント, 担い手, 常に守られること, 移り変わり, 業務ルール, 拒む理由, 未決]
  confidence: [confirmed, assumed, unknown]
  behavior_slice: [業務目的, 起点役割, 協働役割, 事前状態, 業務イベント, 条件, 業務判断, 判断権者, 結果, 次状態, 引継ぎ, 後続イベント]
requirements:
  exclude_implementation: true    # 実装の関心を落とす工程を外せなくする
out_dir: domain
steps: [...]                      # 上書きすると丸ごと差し替わる
```

**`exclude_implementation: true` のまま、線引きの工程を落とせない。** `implementation_excluded` を作る工程が無ければ、解決の時点で止まる。真偽値以外を書いても止まる。

**役の名前を減らすと、その役は本文に置かれなくなる。** 減らすのは、その観点を捨てると決めたときだけにする。

## 使うもの

| コマンド | 必要な場面 |
|---|---|
| `bash` | 工程の解決と素材の束ね |
| `jq` / `yq` v4系 | playbook の検証と読み取り |
| `git` | repository root の判定（無ければカレントを root として扱う） |

## 中身

| 場所 | 役割 |
|---|---|
| `playbook.yml` | 何を、どの順で呼ぶか。役の契約と出力先 |
| `scripts/prepare.sh` | playbook root を検証し、解決済みYAMLの一時パスを返す |
| `scripts/resolve.sh` | 設定を1件選び、工程の順序と依存を検証する |
| `scripts/map.py` | コアの振る舞い断面と代表BDDを記録する |
| `scripts/material.sh` | 事実・線引き・決定・振る舞いを1つの素材へ束ねる |
| `references/roles.md` | 素材の役の定義 |
| `SKILL.md` | 入口と、工程間で守ること |
