# WorldGossip Noise Check 2026-04-15

作成日: 2026-04-15 JST  
対象: root-only 方針にしたあとでも、Agent Reach `twitter search` の結果に DB へ入れるべきでないノイズが混ざるかを確認する

## 1. 結論

結論として、`twitter search` の結果をそのまま DB へ入れるのは危険である。  
root-only 方針にしても、次のノイズがまだ多く混ざった。

- reply-like post
- link stub
- news / media / brand broadcast post
- 低ビューの弱い post
- 国名は入っているが、WorldGossip の会話起点として弱い post

そのため、DB 保存前に pre-DB noise gate を必須にする。

## 2. 実測条件

2026-04-15 JST に、次の 5 query を `twitter search` で小さく再採取した。

- `en_jp_convenience_snack_question_live`
- `en_jp_infrastructure_reaction_hot`
- `en_jp_language_learning_prompt_live`
- `en_global_rollcall_conversation_live`
- `ja_fr_tw_interest_bridge`

期間:

- `since=2026-04-08`
- `until=2026-04-15`

artifact:

- [food.json](/c:/WorldGossip/.agent-reach/noise-check/food.json)
- [infra.json](/c:/WorldGossip/.agent-reach/noise-check/infra.json)
- [language.json](/c:/WorldGossip/.agent-reach/noise-check/language.json)
- [rollcall.json](/c:/WorldGossip/.agent-reach/noise-check/rollcall.json)
- [ja-bridge.json](/c:/WorldGossip/.agent-reach/noise-check/ja-bridge.json)

比較用:

- [language-no-replies.json](/c:/WorldGossip/.agent-reach/noise-check/language-no-replies.json)
- [ja-bridge-no-replies.json](/c:/WorldGossip/.agent-reach/noise-check/ja-bridge-no-replies.json)

## 3. 集計

代表 5 query / 40 item の簡易集計:

- `reply_like`: `8 / 40`
- `link_stub`: `10 / 40`
- `weak_conversation` (`replies < 5` かつ `quotes < 2`): `22 / 40`
- `low_views` (`views < 5000`): `19 / 40`

ここでいう `reply_like` は、本文または title が `@` で始まる post を指す。

## 4. 実際に見えたノイズ

### 4.1 reply-like post が search に混ざる

代表例:

- `@VTCCHokie81 ...` by `learning_yohei`
- `@HustleBitch_ ...` by `atensnut`
- `@AiPinfu2003 ...` by `DadsSeasonings`

重要点:

- `twitter search` だけでは root post と reply post が混ざる
- `-filter:replies` を付けた再実測でも reply-like post が残った
- つまり query だけでは防げず、host 側で必ず除外する必要がある

### 4.2 brand / promo / media broadcast が強く混ざる

代表例:

- `takiko_lawson`
- `SnackReel`
- `SCMPNews`
- `themainichi`
- `MetroUK`

重要点:

- country anchor や topic keyword を満たしていても、broadcast 系は WorldGossip の会話起点になりにくい
- 特に `詳細はこちら` 型や URL 主体の投稿は DB 候補に不要

### 4.3 低ビュー・会話弱い post がかなり多い

代表例:

- `views=50`, `79`, `216`, `542`
- `replies=0`, `quotes=0` が多数

重要点:

- profile や lane の中間候補としても弱すぎるものが search には多く混ざる
- 少なくとも `views < 5000` は DB 候補に残す価値が薄い

### 4.4 blocked terms だけでは drift を止められない

代表例:

- `ArthurLCLR` の anti-China 方向の post
- `sharenewsjapan1` の対立誘発系 post

重要点:

- query の `-政治 -戦争` だけでは、文化比較を装った grievance / nationalist drift を防げない
- 正規化後に cross-country seed と safety を host 側で再判定する必要がある

## 5. 追加確認

`-filter:replies` を入れた再実測:

- [language-no-replies.json](/c:/WorldGossip/.agent-reach/noise-check/language-no-replies.json)
- [ja-bridge-no-replies.json](/c:/WorldGossip/.agent-reach/noise-check/ja-bridge-no-replies.json)

観察結果:

- reply-like post が依然として残った
- したがって `twitter search` の query だけで root-only を保証する設計は採用しない

## 5.1 責任分界

今回のノイズは、主として `WorldGossip` 側の候補採用条件がまだ甘いことと、`X/Twitter search` 面そのものが root-only を保証しないことに起因する。  
`Agent Reach` 自体が独自に reply や brand post を生成しているわけではない。

確認できたこと:

- `agent_reach.adapters.twitter.TwitterAdapter.search()` は `twitter-cli` の `search` を実行し、その `raw.data` をほぼそのまま `items` に正規化している
- `agent-reach collect --channel twitter --operation search ...` の返り値には `raw` が含まれ、ノイズはこの `raw` 時点ですでに存在する
- 2026-04-15 JST に同一 query を `twitter search ... --json` と `agent-reach collect ... --json` で別々に叩くと、どちらも reply-like / low-quality / media-brand 系が混ざった
- しかも 2 回の呼び出しで返る ID 群が揺れたため、問題は `Agent Reach` の deterministic な変換より `X search` 側の不安定さに近い

ただし、`Agent Reach` / `twitter-cli` 側にも二次的な制約はある。

- `search` item に `is_reply` `in_reply_to_status_id` `conversation_id` のような root 判定用フィールドが露出していない
- そのため host 側では現在 `@` 始まりなどの coarse heuristic で pre-DB gate するしかない

したがって現時点の整理は次のとおり。

- ノイズを DB に入れてしまう責任は host 側設計の問題
- そのノイズを query だけで消しきれない原因は `X/Twitter search` 面の問題
- `Agent Reach` を fork する理由があるとすれば、検索品質そのものより `reply/root 判定メタデータを露出したい` 場合

## 6. 採用方針

DB 保存前に、少なくとも次を落とす。

- `@` 始まりの reply-like post
- `詳細はこちら`、URL 主体、極端に短い本文の link stub
- 外部リンク主体で、質問・比較・roll-call・説明導線のない news / brand broadcast post
- `views < 5000` の low-traction post
- 正規化後に country anchor と cross-country seed の両方が弱い post

## 7. 設計反映

この結果を受けて、次を更新した。

- [worldgossip-technical-design.md](/c:/WorldGossip/docs/worldgossip-technical-design.md)
- [worldgossip-collection-design.md](/c:/WorldGossip/docs/worldgossip-collection-design.md)
- [worldgossip-agent-reach-db-persistence-design-2026-04-15.md](/c:/WorldGossip/docs/worldgossip-agent-reach-db-persistence-design-2026-04-15.md)
- [collection_lanes.yml](/c:/WorldGossip/config/collection_lanes.yml)
- [query_profiles.yml](/c:/WorldGossip/config/query_profiles.yml)
