# WorldGossip Agent Reach X/Twitter PoC

作成日: 2026-04-14 JST

## 前提

今回の PoC では、Agent Reach に対して長い自然言語プロンプトを直接渡すのではなく、次の 3 層に分けて設計した。

1. `調査ブリーフ`
2. `調査実行プラン`
3. `query profiles`

Agent Reach は薄い read-only collection 面なので、この形の方が再現性と調整性が高い。

## 調査ブリーフ

- 目的: WorldGossip で想定する「各国の人が他国や文化について語り、リプライ欄で交流や軽い議論が起きそうな X/Twitter 投稿」を Agent Reach で問題なく収集できるかを PoC として検証する。
- 対象: 2026-01-01 から 2026-04-14 までの公開 X/Twitter 投稿のうち、日本と他国の文化・印象・比較・誤解・好意・軽い banter を扱う高反応投稿。
- 期待成果物: 収集 evidence ledger、discovery query ごとの取得結果、数十万以上の view を持つ適合投稿の例、shortlist に対する `tweet` 深掘り結果、query 改善知見。
- 鮮度要件: 2026-04-14 JST 時点で public X/Twitter 上から取得できること。ニュース速報性よりも「今この運用で取れるか」を重視するため、対象期間は 2026-01-01 から 2026-04-15 までの bounded window とする。
- 含める範囲: 日本と他国の比較、国民性や文化への反応、相互好意、温度差、軽いツッコミ、返信が増えやすい open question、quote/reply が発生しているバズ投稿。
- 除外範囲: 戦争、政治、宗教、排外主義、参政権、移民論争、犯罪扇動、北朝鮮ミサイル、スポーツ大会由来の話題。
- 地域・言語: 初回 PoC は `ja` と `en` を主軸にしつつ、reply や quoted tweet に `ko` `zh` が混ざることは許容する。
- 重視ソース: `twitter search` を discovery、`twitter tweet` を shortlist deep read として使う。
- 禁止ソース: 初回 PoC では `web` や他 SNS へ拡張しない。
- 証拠厳密度: `run-id` `intent` `query-id` `source-role` を付け、`--save-dir` で shard 保存したうえで ledger 化する。
- 調査スケール: `broad_with_ledger` 相当。ただし channel は `twitter` のみに絞る。
- 前提と仮定: impressions の直接 filter は安定しない可能性があるため、discovery では broad に拾い、取得後に `engagement.views` `likes` `replies` を使って host 側で絞る前提にした。

## 調査実行プラン

- 目的: WorldGossip 向けの高反応 X/Twitter 投稿が Agent Reach で実務的に収集できるか、discovery と deep read の 2 段で確認する。
- 対象: 日本と他国の文化・印象・比較・反応差を扱う公開 X/Twitter 投稿。
- 鮮度要件: 2026-04-14 JST 時点で再現可能であること。検索 window は 2026-01-01 から 2026-04-15 とする。
- 実行モード: `broad_with_ledger`
- 発見フェーズ: `twitter search` を 4 クエリ、各 `--limit 8` で実行する。query は `en_culture_curiosity` `en_country_banter` `ja_country_reaction` `ja_people_reference` の 4 本に固定する。
- 成果物サイズ予算: discovery は `raw_mode=none` `item_text_mode=snippet` `item_text_max_chars=240` を使い、軽い handoff に留める。
- 証拠の残し方: `--save-dir .agent-reach/worldgossip-twitter-poc-20260414/shards` で保存し、`ledger merge` で `evidence.jsonl` に統合する。summary は `ledger summarize` で確認する。
- 候補選別ゲート: `plan candidates --by normalized_url --limit 20` で URL 重複を軽く潰したうえで、host 側で `engagement.views >= 300000` を第一候補、`replies >= 300` を会話性補助指標として使う。
- 深掘り予算: `tweet` deep read は 4 件まで。高 view かつ WorldGossip の方向性に合うものだけを follow-up する。
- 最終まとめ境界: 取得した全件を要約せず、discovery 成功可否、ノイズ傾向、深掘り成功可否、適合サンプルだけをまとめる。
- 停止条件: discovery 4 本で high-fit 候補が 3 件以上取れ、`tweet` deep read が 1 件以上成功した時点で PoC 成功とみなす。足りなければ query を追加で再調整する。
- 前提と仮定: `twitter search` は query 内の `min_faves` が厳密に効かない可能性があるため、query より取得後フィルタの方を信用する。`tweet` は doctor 未 probe でも、実地確認で判断する。

## Query Profiles

### 1. `en_culture_curiosity`

- 狙い: 海外ユーザーが日本の文化・生活・食・清潔さなどに驚く、褒める、疑問を投げる投稿。
- query:

```text
("Japan" OR "Japanese") (culture OR people OR food OR customs OR tourists) ("love" OR "amazing" OR "why" OR "different" OR "weird") lang:en -missile -summit -president -government -war -WBC -baseball -election
```

### 2. `en_country_banter`

- 狙い: 英語圏から見た国比較、軽い banter、温度差、相互印象。
- query:

```text
("Japan" OR "Japanese") ("American" OR "Korean" OR "Taiwanese" OR "French" OR "German") ("better" OR "different" OR "vs" OR "why" OR "love") lang:en -missile -summit -president -government -war -WBC -baseball -election
```

### 3. `ja_country_reaction`

- 狙い: 日本語圏での「日本と他国のズレ」「他国から見た日本」「国と言語の温度差」。
- query:

```text
("アメリカ" OR "韓国" OR "台湾" OR "フランス" OR "ドイツ") ("日本" OR "日本人") ("好き" OR "驚いた" OR "違う" OR "なんで" OR "面白い") lang:ja -政治 -参政権 -移民 -犯罪 -戦争 -北朝鮮 -野球 -選挙
```

### 4. `ja_people_reference`

- 狙い: 国籍名や人の視点を含み、reply が発生しやすい問いや印象の投稿。
- query:

```text
("アメリカ人" OR "韓国人" OR "台湾人" OR "フランス人" OR "ドイツ人") ("日本" OR "日本人") ("好き" OR "友人" OR "驚いた" OR "面白い" OR "どうして") lang:ja -政治 -参政権 -移民 -犯罪 -戦争 -北朝鮮 -野球 -選挙
```

## 実行結果

### Readiness

- 2026-04-14 JST 時点で `agent-reach doctor --json --probe` は `twitter search` と `twitter user` の live success を返した。
- `twitter tweet` は doctor では未 probe だったが、実地で成功した。

### Discovery Summary

- run id: `worldgossip-twitter-poc-20260414`
- discovery records: 4
- discovery items seen: 32
- unique post candidates: 29
- errors: 0

### Deep Read Summary

- `tweet` deep read: 4 件成功
- `tweet` follow-up では `engagement_complete=true` `media_complete=true` が返り、reply/quoted tweet を含めて取得できた

## 取得できた高適合サンプル

### 1. 韓国女性から日本女性への投稿

- URL: `https://x.com/youtu_03/status/2041028665522450487`
- 投稿日: 2026-04-06
- 言語: `ja` 本文 + `ko` 引用
- views: `10,443,306`
- 方向性: 国際交流、軽い warning、reply が自然に増える

### 2. 「アメリカ人はなぜ日本が好きなの？」という日本語投稿

- URL: `https://x.com/yamanakanobody/status/2039279687256642034`
- 投稿日: 2026-04-01
- 言語: `ja` 本文、reply 側に `en`
- views: `2,369,866`
- replies: `5,908`
- 方向性: まさに WorldGossip の会話起点型

### 3. 台湾で日本語がどの程度通じるかを修正する投稿

- URL: `https://x.com/Gairaku_tw/status/2042080222879871473`
- 投稿日: 2026-04-09
- 言語: `ja` 本文、reply 側に `zh`
- views: `1,205,317`
- 方向性: 誤解修正、温度差、言語ギャップ

### 4. 「なぜ日本にはこういう便利なものがあるのか」という英語投稿

- URL: `https://x.com/lost_nomad__/status/2042282458670928044`
- 投稿日: 2026-04-09
- 言語: `en`
- views: `1,019,155`
- replies: `497`
- 方向性: 自国比較、生活文化、reply が伸びる open question

## 実務上の知見

### 1. `search` だけで views は取れる

Discovery 段階の `twitter search` でも `engagement.views` は取れた。
そのため「数十万以上のインプレッションを持つ投稿を拾えるか」の一次判定は search だけで可能。

### 2. `min_faves` は信用しすぎない

query に高い `min_faves` を入れても、低 like 投稿が混ざった。
したがって、viral 条件は query で保証するより、取得後に `views` `likes` `replies` で再選別する方が安定する。

### 3. `tweet` deep read は shortlist 後に使うのが最適

`tweet` では `engagement_complete=true` になり、reply や quoted tweet まで取れた。
したがって最適手法は次の 2 段構えである。

1. `search` で広く discovery
2. shortlist URL にだけ `tweet` を当てる

### 4. 日本語 query は generic な `外国人` を避ける

`外国人` `韓国` `中国` のような generic で強い語を入れると、排外・政治・安全保障話題が混ざりやすい。
WorldGossip 向けには次を優先した方が良い。

- 国籍名
- 文化語
- 好意・驚き・比較・質問
- 返信が起きそうな open question

### 5. host 側の二次フィルタが必須

Agent Reach は read-only collection なので、最終的な適合判定は host 側で行う前提が正しい。
最低でも次の二次フィルタを推奨する。

- `views >= 300000`
- 政治・戦争・宗教・排外主義 regex 除外
- `replies >= 100` を会話性の補助指標にする
- `tweet` deep read 後に reply の雰囲気を確認する

## 成果物パス

- shards: [shards](/c:/WorldGossip/.agent-reach/worldgossip-twitter-poc-20260414/shards)
- merged ledger: [evidence.jsonl](/c:/WorldGossip/.agent-reach/worldgossip-twitter-poc-20260414/evidence.jsonl)

