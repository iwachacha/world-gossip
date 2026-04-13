# WorldGossip Agent Reach X/Twitter Expansion

作成日: 2026-04-14 JST

## 概要

前回 PoC で Agent Reach による WorldGossip 向け X/Twitter 収集が成立することを確認できたので、今回は次の 2 点を追加検証した。

1. 国・言語・問い方のパターンを増やして discovery の再現性を広げる
2. 高適合候補を `tweet` deep-read し、reply 欄で実際にどんな国際交流や小競り合いが起きるかを確認する

結論として、収集面はかなり有望だった。特に `ja` と `en` を軸にした open question 型、食・生活・価格差・相互好意を扱う投稿は量産しやすい。一方で `ko` `zh` `pt` `id` は取れるが、政治・歴史・ノイズ混入率に差がある。

## 今回の実行サマリ

- run id: `worldgossip-twitter-expansion-20260414`
- discovery query: `13`
- deep-read: `6`
- total records: `19`
- items seen: `250`
- errors: `0`

### 追加した discovery query 群

前回 PoC の `ja` `en` 主体 query に加えて、次の地域・言語を増やした。

- 日韓台欧州の混合興味軸
- 日米の open question 軸
- 東南アジア・南米を含む英語 query
- 東南アジア・南米を含む日本語 query
- スペイン語の日本 x 中南米 query
- ポルトガル語の日本 x ブラジル query
- インドネシア語の日本 x 東南アジア query

## query ごとの手応え

### 強い

- `ja_fr_tw_de_interest`
  - 最大 `2,442,482` views
  - 多国籍・翻訳・食・オタク話題が混ざると強い
- `en_jp_us_open_question`
  - 最大 `2,001,481` views
  - 最大 `1,246` replies
  - 生活用品、価格差、アメリカへの問いかけが非常に強い
- `ko_jp_country_question`
  - 最大 `1,826,544` views
  - 日韓相互好意や誤解修正は強いが、歴史論争に寄りやすい
- `en_jp_sea_latam_open`
  - 最大 `178,131` views
  - 最大 `507` replies
  - 東南アジアも英語経由なら会話が立ちやすい
- `es_jp_latam_bridge`
  - 最大 `1,289,730` views
  - スポーツ混入はあるが、スペイン語圏で日本関連のバズは十分拾える

### 中程度

- `en_jp_kr_tw_culture`
  - 最大 `182,697` views
  - 会話は起きるが、汎用的な文化論に寄ると質がぶれやすい
- `ja_sea_latam_open`
  - 最大 `75,811` views
  - 日本語 query でも東南アジア話題は拾えるが、運用上のノイズ管理が必要
- `fr_jp_culture_question`
  - 最大 `70,570` views
  - 量は少なめだが、日仏文化比較の種はある

### 弱い・ノイズ多め

- `zh_jp_country_question`
  - 日中台香の対立話題に流れやすい
- `de_jp_culture_question`
  - 量が少なく、意味的に合う投稿の密度が低い
- `pt_jp_brazil_bridge`
  - 今回の query では低反応が多い
- `id_jp_country_question`
  - 取得自体は可能だが、今回の query では政治・雑多ノイズが残りやすい

## 高適合候補

### 1. 多国籍翻訳ハブ型

- ID: `2039995616257003798`
- URL: `https://x.com/tutitoabura/status/2039995616257003798`
- views: `2,442,491`
- 特徴:
  - アメリカ、ポルトガル、ドイツ、日本が 1 投稿内でつながる
  - 自動翻訳を介した「世界オタクの交流」という WorldGossip 的ど真ん中
  - ただし一部で政治・宗教方向の reply も混ざる

### 2. 韓国からの橋渡し型

- ID: `2043067747396128886`
- URL: `https://x.com/Muichiro_Korea/status/2043067747396128886`
- views: `1,826,760`
- replies: `391`
- 特徴:
  - 「韓国人は日本を嫌っていない」という誤解修正
  - reply 欄で日韓の相互理解と歴史論争が両方出る
  - 会話性は高いが、安全スコアは中リスク以上で扱うべき

### 3. 日米価格差の open question 型

- ID: `2043309710850576795`
- URL: `https://x.com/JUN_SAITOH_WHR/status/2043309710850576795`
- views: `1,540,537`
- replies: `1,246`
- 特徴:
  - 日本人がアメリカ人に grill の値段を質問
  - 実用品、価格差、住環境差、BBQ 文化まで広がる
  - かなり安全で reply の質も良い

### 4. 日本語から英語 reply を呼ぶ質問型

- ID: `2041220189153591667`
- URL: `https://x.com/learning_yohei/status/2041220189153591667`
- views: `107,256`
- replies: `1,182`
- 特徴:
  - 「なぜアメリカで鷲がよく出てくるのか」という素朴な文化質問
  - reply のほぼ全体が英語で返る
  - 1 reply あたりの爆発力は弱くても、交流の総量は非常に大きい

### 5. 東アジア料理比較型

- ID: `2040625279291539476`
- URL: `https://x.com/FiredUpCoug/status/2040625279291539476`
- views: `130,617`
- replies: `507`
- 特徴:
  - 「日本で最も人気のあるアジア料理は？」という質問
  - `ja` と `en` の reply が混ざり、自然に追加質問も起きる
  - 後から国別の食文化投稿と組み合わせやすい

### 6. 日仏菓子比較型

- ID: `2043045894488994111`
- URL: `https://x.com/ulala_go/status/2043045894488994111`
- views: `1,771,961`
- 特徴:
  - フランス菓子のプライドに対して、日本の菓子水準を返す構図
  - reply 欄ではバター、乳製品、甘さ、包装品質などの論点に分解される
  - banter と比較のバランスが良い

## deep-read で見えた reply 欄の質

### `dr_jun_grill_price`

- 英語だけで会話が進み、価格差、製品提案、家の広さ、庭のサイズに派生した
- 国際交流としてかなり健全で、実用品ベースなので敵意が立ちにくい
- WorldGossip の「軽い議論」に一番向いている類型

### `dr_firedup_cuisine_question`

- `ja` と `en` が混ざって返ってきた
- ただ答えるだけでなく、「日本向けにどう改変されているのか」という follow-up が自然に発生
- 文化比較と food discourse をつなぐのに向いている

### `dr_learningyohei_eagle_question`

- 日本語の問いに対して英語話者が大量に答える構図が再現された
- 返信の内容は national symbol、freedom、歴史、実物の大きさなどに分かれた
- 「日本発の素朴な質問 -> 海外 reply 大量流入」の量産パターンとして非常に有用

### `dr_ulala_france_food_quote`

- 罵倒ではなく、フランスの強みと日本の強みを分けて語る reply が多かった
- `フランス=バター・乳製品`、`日本=ケーキ・繊細さ・持ち帰り品質` のように比較軸が自然発生した
- cross-lingual matching の題材として優秀

### `dr_muichiro_korea_bridge`

- 好意的な返信も多いが、歴史問題やナショナル感情がすぐ混ざる
- 「交流は起きるが緊張度も高い」良い教材になった
- WorldGossip で使うなら `tension_balance_score` と manual review を強めに掛けるべき

### `dr_tutitoabura_translation_babel`

- 多国籍の reply が自然発生し、「次はこれを試して」「うちの国もこれ好き」と話題が広がる
- ただし翻訳越しの政治・思想方向にも接続しやすい
- 安全寄りの話題に限定した再編集が重要

## 実務上の重要知見

### 1. 英語は依然として最重要

東南アジア・南米を広げても、現時点では `lang:en` を使った cross-country query の方が WorldGossip 適合率が高い。現地語でしか出ない投稿もあるが、量産面では英語が主戦場。

### 2. 日本語 open question は reply を量産しやすい

`learning_yohei` 系や「アメリカ人に質問があります」型は、view より reply の厚みが非常に強い。今後の収集基盤では `replies >= 300` を優先条件にした shortlist も有効。

### 3. 食・価格・生活用品は安全で強い

次のテーマは収集しやすく、かつ会話が伸びやすい。

- 料理
- 菓子
- BBQ / grill / kitchen
- 生活用品
- 国ごとの好みや改変

### 4. 日韓は強いが緊張度が高い

日韓の相互好意・誤解修正は高反応になりやすい一方、歴史・領土・スポーツ煽りがすぐ出る。ここは別レーンで扱い、公開候補には safety 強化が必要。

### 5. `tweet` deep-read は thread 以外の混入がある

今回の deep-read では、複数スレッドに同じ無関係投稿が混ざった。

- `1927241476380954917`
- `2040958919728857226`

したがって `tweet` をそのまま thread 全体として信用せず、少なくとも次の host 側フィルタが必要。

- root id を必ず保持
- root author の返信を優先
- `@root_author` で始まる返信を優先
- 複数 deep-read に重複出現する item を recommendation noise とみなして除外

### 6. query 除外語だけでは不十分

`-政治` `-war` のような除外語を入れても、意味的に政治・歴史へ寄る投稿は残る。最終的には host 側で topic classifier / regex / reviewer 判断が必要。

## 次ラウンドの推奨方針

### 続けるべき query family

1. 日本人がアメリカ人や外国人に素朴な質問をする型
2. 英語話者が日本人に open question を投げる型
3. 食・菓子・BBQ・価格差・日用品の比較型
4. 日仏・日台・日韓の「好意 + 温度差」型
5. 東南アジア・南米はまず英語 query で拾い、現地語は補助に回す

### 改善したい点

1. `tweet` deep-read 用の host フィルタを実装する
2. `views` だけでなく `replies` と `quotes` を shortlist 条件に入れる
3. `ja_us_open_question` は政治ノイズをさらに落とすため、国名より `アメリカ人` `質問` `文化` `料理` などの語を優先する
4. `pt` `id` は query 再設計が必要で、英語経由の方が当面は効率的

## 成果物パス

- expansion ledger: [evidence.jsonl](/c:/WorldGossip/.agent-reach/worldgossip-twitter-expansion-20260414/evidence.jsonl)
- expansion shards: [shards](/c:/WorldGossip/.agent-reach/worldgossip-twitter-expansion-20260414/shards)
- previous PoC: [worldgossip-agent-reach-twitter-poc.md](/c:/WorldGossip/docs/worldgossip-agent-reach-twitter-poc.md)
