# domain-events

**業務で起きる事実を、起きた順に台帳へ残す。** 要約も設計もしない。

洗い出したものを何に使うか（資料にする／ルールへ畳む）は、このプラグインの外の話である。ここは「何が起きるのか」だけを確定させる。

## 何を返すか

`<event_dir>/<題材>.jsonl` に1行1件で積み、`render` で時系列の表にする。各件が持つのは次の7つ。

| 項目 | 意味 | 必須 |
|---|---|---|
| `name` | 起きたこと（過去形の業務語） | ○ |
| `actor` | 担い手 | ○ |
| `trigger` | 引き金（`操作` / `時間` / `外部` / `連鎖`） | ○ |
| `outcome` | 業務上どう変わったか | ○ |
| `precondition` | 起きるための前提 | — |
| `status` | 確からしさ（`confirmed` / `assumed` / `unknown`） | 既定 `assumed` |
| `source` | 誰・どこからの知識か | — |

**担い手・結果の無い事実は書けない。** 誰の行いか分からない、何が変わったか言えないものは、業務の事実として成立していない。

## 設定

`<repo>/.harness-plugins/domain-events.config.yml`（無ければ `${XDG_CONFIG_HOME:-~/.config}/harness-plugins/domain-events.config.yml`、それも無ければ同梱既定）。**1ファイルだけが選ばれ、層は混ざらない。** 選んだファイルが下のキーを全部持たなければ止まる。

```yaml
version: 1
event_dir: domain/events          # 台帳の置き場（repo root からの相対、または絶対）
instructions:
  exploration:
    directive: 業務で起きた事実を時系列に洗い出し、確かめられない箇所は未確認のまま残す
```

## 使うもの

| コマンド | 必要な場面 |
|---|---|
| `bash` | 設定の解決 |
| `jq` / `yq` v4系 | 設定の検証と読み取り |
| `python3` | 台帳の追記・表示（標準ライブラリのみ） |
| `git` | repository root の判定（無ければカレントを root として扱う） |

## 中身

| 場所 | 役割 |
|---|---|
| `scripts/prepare.sh` | plugin root を検証し、解決済みYAMLの一時パスを返す |
| `scripts/resolve.sh` | 設定を1件選び、完全性を検証して解決済みYAMLを返す |
| `scripts/event.py` | 台帳への追記・読み出し・表化。必須項目と引き金・確からしさの値をここで拒否する |
| `references/actors-and-stakeholders.md` | actorの目的・責任と、直接操作しないstakeholderの利害 |
| `references/domain-events.md` | 要求や通知と区別した、すでに起きた業務事実 |
| `references/concept-map.md` | 振る舞い・記録・仕様例の関係と、混同したときの失敗 |
| `references/grain.md` | 何を1件と数えるか（名前・粒度・引き金・確からしさ） |
| `skills/explore-events/` | 洗い出しの入口と進め方 |

保存するevent record、Event Sourcingの採否、目的指向のユースケースはこのpluginでは扱わない。必要な後続pluginが自身の指示として持つ。
