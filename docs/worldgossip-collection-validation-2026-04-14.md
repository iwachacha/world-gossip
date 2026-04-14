# WorldGossip 収集検証レポート 2026-04-14 Round 1

作成日: 2026-04-14 JST  
run_id: `worldgossip-collect-20260414-round1`  
対象: `twitter search` discovery と `twitter tweet` deep-read による初回実収集検証

## 1. 概要

今回の目的は 2 つだった。

- 収集基盤のたたき台が実データで機能するかを検証する
- 大量に拾った投稿から、どうやって WorldGossip 向けの高品質候補を抽出するかを具体化する

結果として、`food / convenience / appreciation / bilateral AMA` は強く、`why / foreigner / people-reference` を広く含む family は政治・対立に流れやすいことが明確になった。

## 2. 実行サマリ

- discovery query 数: `9`
- discovery item 数: `160`
- unique candidate 数: `146`
- deep-read 対象 thread 数: `8`
- 主使用 channel: `twitter`
- 主使用 operation: `search`, `tweet`

discovery query:

- `ja_people_reference_live`
- `ja_us_open_question_hot`
- `en_jp_food_bridge`
- `en_jp_open_question_hot_v2`
- `ja_overseas_daily_life_v1`
- `en_jp_country_reaction_v1`
- `en_jp_surprise_daily_v2`
- `en_jp_food_quality_v3`
- `en_jp_ama_travel_v2`

## 3. 勝ち筋

### 3.1 強かった family

- `food / snack / convenience`
  - もっとも安定して project-fit 候補を出した
  - 低リスクで、reply から別国側の体験談やおすすめが増えやすい
- `bilateral AMA / ask me anything`
  - 交流の起点として非常に強い
  - 単なる質問箱ではなく、`相手国について答える + 相手にも聞き返す` 型が特に強い
- `appreciation prompt`
  - view は中規模でも reply 密度が高い
  - 相互理解や軽い議論に育ちやすい
- `surprise prompt`
  - discovery 入口として有効
  - keep するには `views` より `reply density` を重く見る必要がある
- `cross-country story`
  - 数は少ないが、当たると非常に強い
  - 文化交流の文脈が自然に立つ

### 3.2 弱かった family

- `why / なぜ` に寄りすぎた広い open question
  - 政治、移民、歴史、基地問題に流れやすい
- `people-reference`
  - 特定国への感情やナショナリズムを拾いやすい
- `misunderstanding correction`
  - 政治・歴史への接続リスクが高い
- `country banter`
  - ideologically charged な投稿を拾いやすい

## 4. 高適合候補

### 4.1 `food / convenience`

- `TheJoe746`  
  `https://x.com/TheJoe746/status/2042993558932574580`  
  `188,824 views / 201 replies / 58 quotes`  
  アメリカ側の fast food 話題から、日本側 reply で食文化の相互紹介が自然に発生した。`reply の質` まで含めて非常に強い。

- `GloryDoge`  
  `https://x.com/GloryDoge/status/2042053905237033069`  
  `13,830 views / 81 replies / 7 quotes`  
  views は中規模だが、`what should I buy?` 型で reply が伸び、商品推薦と文化説明が生まれた。`live_conversation` の良い見本。

- `TapRootsFood`  
  `https://x.com/TapRootsFood/status/2043024895680926110`  
  `29,685 views / 45 replies / 9 quotes`  
  日本食材への関心から、調味料・米・食文化の話へ伸びる。意味的マッチングの素材としても強い。

### 4.2 `AMA / appreciation`

- `BenGrahamUK`  
  `https://x.com/BenGrahamUK/status/2041701287620751741`  
  `31,174 views / 100 replies / 13 quotes`  
  Britain/Japan AMA の完成度が高い。`相手にも質問を返す` ため、片側説明で終わらない。

- `Green_k100`  
  `https://x.com/Green_k100/status/2043488022822260954`  
  `11,203 views / 147 replies / 10 quotes`  
  `Japan do you like when foreigners compliment your culture?` は低 views でも会話密度が非常に高い。日本側から性格・文化説明が多く返ってきた。

- `Green_k100`  
  `https://x.com/Green_k100/status/2043694329760260262`  
  `5,396 views / 159 replies / 13 quotes`  
  `Japan what is one thing you like about America?` はさらに密度が高い。`バズより交流` に強い archetype。

### 4.3 `story / memory`

- `PalmerLuckey`  
  `https://x.com/PalmerLuckey/status/2043076300286628204`  
  `147,044 views / 54 replies / 10 quotes`  
  日本人カウボーイ Hank Sasaki の話から、日米文化交流の物語が自然に立ち上がった。数は少ないが強い family。

### 4.4 `high views but lower density`

- `ZubyMusic`  
  `https://x.com/ZubyMusic/status/2042618211615805470`  
  `1,124,135 views / 32 replies / 11 quotes`  
  discovery 入口としては非常に有効。ただし `views` の割に会話密度は高くなく、keep 判断は別軸が必要。

## 5. 危険投稿の典型

- `May_Roma`  
  `https://x.com/May_Roma/status/2043488347625038252`  
  `341,439 views / 213 replies / 73 quotes`  
  数値だけ見ると優秀だが、基地・政治文脈で WorldGossip の初期方針とは合わない。

- `mattariver3`  
  `https://x.com/mattariver3/status/2042120332589592663`  
  `560,401 views / 61 replies / 35 quotes`  
  anti-foreigner 文脈。`views` は強いが keep してはいけない。

- `yamanakanobody`  
  `https://x.com/yamanakanobody/status/2043550375131971651`  
  `185,271 views / 165 replies / 40 quotes`  
  people-reference family が nationalist drift しやすいことを示す例。

## 6. 抽出ルール

初期抽出は次の順で行うのがよい。

1. hard block  
   `politics / war / immigration / base / election / xenophobia / severe discrimination` を除外する
2. theme fit  
   `food / convenience / culture / travel / daily life / appreciation / AMA / surprise` のどれかを要求する
3. lane score  
   `views` と `replies` を分けて見る
4. deep-read  
   strong candidate だけ `tweet` deep-read し、reply の雰囲気を確認する

初期の keep 優先信号:

- `replies` が多い
- `quotes` が多い
- `views` が十分ある
- 同一投稿が複数 family で再発見される
- root と reply の両方に cross-country 文脈がある

初期の downrank 信号:

- 公式ブランド投稿
- 報道やニュースリンク主体
- `foreigners / why / politics` で広く引っかかっただけの投稿
- root は良さそうでも reply が対立化している投稿

## 7. スコア方針

初期 host score は、単純な `viral sort` ではなく次の合成がよい。

- `buzz_score`
  - `log(views)`
  - `likes`
- `conversation_score`
  - `replies`
  - `quotes`
  - `reply_density = replies / views`
  - `quote_density = quotes / views`
- `fit_score`
  - family 妥当性
  - food / convenience / appreciation / AMA への一致
- `overlap_score`
  - 複数 query family からの再発見
- `safety_penalty`
  - hard block topic
  - nationalist drift
  - ideology drift
  - one-way mockery

重要なのは、`views 単独では keep しない` こと。

## 8. 設計反映

この round 1 を受けて採用する方針:

- 主力 family は `food / convenience / appreciation / bilateral AMA / surprise prompt`
- `ja_us_open_question_hot` は guarded
- `ja_people_reference_live` は guarded
- `ja_misunderstanding_fix_live` は guarded
- `en_country_banter_live` は broad 運用をやめ、`appreciation prompt` に置き換える
- deep-read は `top views` ではなく `theme fit + density + overlap` で決める

## 9. 次の実装

- `query_profiles.yml` を proven / guarded で再編する
- host 側 shortlist score に `multi_family_overlap` を追加する
- `brand / news / recommendation item` downrank を入れる
- `post_observations` を使って `reply_velocity` と `re-discovery rate` を計算する
