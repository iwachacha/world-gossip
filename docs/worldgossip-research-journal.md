# WorldGossip Research Journal

更新日: 2026-04-15 JST  
目的: WorldGossip の収集運用で得た知見を、`一時的に当たったテーマ` ではなく `再利用可能な会話アーキタイプ` として蓄積する。

## 1. 運用原則

- `learn structures, not just themes`
  - `food が強い` ではなく `recommendation_request が強い` のように保存する
- `topic` と `archetype` を分離する
  - 同じ archetype を別 topic に横展開して一般化する
- negative findings を残す
  - drift した family、危険な query、誤検知の傾向も資産とみなす
- bias を毎回明示する
  - どの topic bucket に偏ったか、なぜ偏ったかを run ごとに記録する
- stable rule の昇格は慎重に行う
  - 原則 2 run 以上で再現した知見を stable に上げる
  - ただし signal が極端に明確なら single-run でも tentative として記録してよい

## 2. Stable Heuristics

### 2.1 Positive

- `views` 単独では project-fit を保証しない
- `replies / views` と `quotes / views` は `views` より強い品質シグナルになりやすい
- `multi_family_overlap >= 2` は有望候補の強い補助指標になる
- `bilateral_exchange`, `appreciation_prompt`, `recommendation_request`, `story_seed` は WorldGossip と相性が良い
- 英語圏 origin の投稿でも、日本以外の国との橋渡しに展開できる余地がある
- `light_affinity_prompt` は `mutual_appreciation_question` と `local_life_affinity / shared_commonality` に分けて扱うと再利用しやすい
- `country_pairs x language_lane x motif x topic_pack x risk_tier` で profile を型管理すると、国追加より先に query family を横展開しやすい
- `slang_wordplay`, `localization_compare`, `price_probe` は英語圏 audience を取りに行きつつ safety を保ちやすい
- `single_post` で自己完結する多国籍 thread は pair 候補と別枠で first-class に扱うべき

### 2.2 Negative

- 広すぎる `why / なぜ` open question は政治・対立へ drift しやすい
- `people-reference` は感想共有より identity discourse を拾いやすい
- `country banter` は軽口に見えても ideology に接続しやすい
- brand 公式、ニュース、リンク集約投稿は discovery には useful だが publish 素材としては弱い
- 英語の generic な `one thing I love about <country>` は Europe / LatAm で薄く、ステレオタイプや無関係話題を拾いやすい
- banter は `country trait` のまま開くと危険で、`object_anchor_banter` として guarded で持つ方がよい
- broad topic taxonomy を hard rule にすると探索が痩せるので、bucket は guardrail としてだけ使う

## 3. Archetype Taxonomy

- `recommendation_request`
  - 何を買うべきか、何が好きか、どれがおすすめかを問う型
  - 現在の強い topic: `food`
  - 次の展開先: `language tools`, `transport`, `city services`, `hobby`
- `bilateral_exchange`
  - 国や文化をまたいで質問を受け付ける型
  - 現在の強い topic: `daily_life`, `culture`
  - 次の展開先: `work style`, `school life`, `city living`
- `appreciation_prompt`
  - 好きな点、感謝、褒めたい点を募る型
  - 現在の強い topic: `culture`, `daily_life`
  - 次の展開先: `language`, `service`, `hobby`
- `light_affinity_prompt`
  - 強い議論を含まなくても、「この国のこういうところ好き」で広く刺さる型
  - `mutual_appreciation_question` は会話型、`local_life_affinity / shared_commonality` は bridge 型として分けて運用する
  - 現在の有望 topic: `culture`, `daily_life`, `service`, `citylife`
  - 次の展開先: `Europe`, `LatAm`, `Southeast Asia`, `hobby`, `language`
- `surprise_prompt`
  - 意外だったこと、驚いたこと、予想外だったことを共有する型
  - 現在の強い topic: `travel`, `service`, `infrastructure`
  - 次の展開先: `home routines`, `public systems`, `digital life`
- `story_seed`
  - 思い出、体験談、ちょっとした逸話から会話が広がる型
  - 現在の強い topic: `cross-country memory`
  - 次の展開先: `music`, `school`, `friendship`, `sports viewing`
- `translation_relay`
  - 翻訳、言い回し、言語的すれ違いが会話の橋になる型
  - 現在の強い topic: `internet`, `language`
  - 次の展開先: `daily phrases`, `customs`, `work communication`
- `slang_wordplay`
  - スラング、婉曲表現、呼び方の違い、言葉遊びを比較する型
  - 現在の有望 topic: `language`
  - 次の展開先: `toilet euphemism`, `snack names`, `regional English`, `loanwords`
- `localization_compare`
  - 同じブランドや商品が国ごとにどう変わるかを見る型
  - 現在の有望 topic: `food`, `daily_life`
  - 次の展開先: `chain menu`, `packaging`, `grocery`, `mascot`, `product naming`
- `price_probe`
  - 値段や量の差から暮らしの違いを引き出す型
  - 現在の有望 topic: `daily_life`
  - 次の展開先: `groceries`, `kitchen`, `utilities`, `household goods`
- `object_anchor_banter`
  - 軽い挑発や言い争いを concrete object や concrete phrase に anchored して扱う型
  - 現在の有望 topic: `language`
  - 次の展開先: `slang`, `chips / crisps`, `fries`, `bathroom words`
- `self_contained_roll_call`
  - 1 投稿だけで各国の人が参加し始める型
  - 現在の有望 topic: `daily_life`, `language`
  - 次の展開先: `breakfast`, `slang`, `routine`, `queue`, `school lunch`

## 4. Portfolio Targets

- `food` は強いが、日次 shortlist の `25%` を超えない
- 毎週 `infrastructure`, `language`, `customs`, `story` を最低 2 本ずつ shortlist する
- 1 バッチ deep-read では `4` 以上の topic bucket と `3` 以上の archetype を含める
- 毎日少なくとも 1 本は `frontier` profile を通す
- `ja -> en` 一極化を避け、`es`, `fr`, `ja non-food`, `en non-US` の探索も継続する
- `en_hub` を主戦場として `55%` 前後確保し、`ja_seed` と `local_bridge` を補助レーンとして残す
- 週次で `East Asia`, `Southeast Asia`, `Europe`, `LatAm` の 4 クラスター以上を回す

## 5. Run Entry Template

各 run では次を記録する。

- run id / date
- coverage summary
- topic skew
- winning archetypes
- risky archetypes
- stable heuristics に昇格した知見
- profile actions: `promote`, `keep`, `rotation`, `guarded`, `retire`
- next exploration slices

## 6. Run Log

### 2026-04-14 | `worldgossip-collect-20260414-round1`

#### Coverage

- 9 discovery query
- 160 items seen
- 146 unique candidate
- 8 deep-read thread

#### Topic Skew

- `food / convenience / snack` の比率が高い
- `appreciation` と `AMA` も一定量あり、`language`, `infrastructure`, `customs` は不足
- bias の主因は seed の初期構成と proven query の偏り

#### Winning Archetypes

- `recommendation_request x food`
- `bilateral_exchange x daily_life`
- `appreciation_prompt x culture`
- `surprise_prompt x service / travel`
- `story_seed x cross-country memory`
- `light_affinity_prompt x simple country appreciation` は次ラウンドで積極検証する

#### Risky Archetypes

- `open_question x broad why`
- `people_reference x identity talk`
- `banter x country comparison`
- `misunderstanding_correction x history/politics adjacency`

#### Stable or Tentative Heuristics Added

- tentative: `views` 単独 keep をやめ、`conversation_density` を主指標にする
- tentative: `multi_family_overlap` は強い補助指標
- tentative: `food` の強さは topic 自体より `recommendation_request` archetype の強さとして扱う

#### Profile Actions

- `promote`
  - `en_jp_country_exchange_ama_live`
  - `en_jp_appreciation_prompt_live`
  - `en_jp_food_bridge`
- `keep`
  - `en_translation_bridge_live`
  - `en_jp_story_bridge_explore`
- `rotation`
  - `ja_food_price_hot`
- `guarded`
  - `ja_us_open_question_hot`
  - `ja_people_reference_live`
  - `ja_misunderstanding_fix_live`
  - `en_country_banter_live`

#### Next Exploration Slices

- `recommendation_request x language`
- `surprise_prompt x infrastructure`
- `appreciation_prompt x hobby`
- `light_affinity_prompt x Europe / LatAm / Southeast Asia`
- `bilateral_exchange x work / school / city life`
- `story_seed x music / friendship / sports viewing`

### 2026-04-14 | `worldgossip-collect-20260414-round2-affinity-validation-v2`

#### Coverage

- 15 discovery query
- 238 items seen
- 231 unique candidate
- 16 deep-read thread

#### Topic Skew

- `culture` が依然支配的だが、topic より `cluster skew` の方が深刻だった
- unique candidate 上の cluster hit は `East Asia` が圧倒的で、`Europe` は薄く、`Southeast Asia` と `LatAm` はかなり不足
- `multi_family_overlap` は `4` 件しかなく、country expansion がそのまま diversity quality に結びついていない

#### Winning Archetypes

- `mutual_appreciation_question x East Asia`
- `recommendation_request x food`
- `hobby_constraint_surprise x Japan`
- `shared_commonality x multi-country daily life`
- `local_life_affinity x Southeast Asia`

#### Risky Archetypes

- `generic_country_trait_affinity x Europe`
- `generic_english_affinity x LatAm`
- `self_congratulatory_compliment_prompt`
- `anti_individuality praise disguised as affinity`

#### Stable or Tentative Heuristics Added

- tentative: `light_affinity_prompt` は `live_conversation` と `bridge_candidate` の 2 モードに分けると扱いやすい
- tentative: `mutual_appreciation_question` は軽い内容でも `conversation_density` と `light_exchange_bonus` が両立しやすい
- tentative: `local_life_affinity / shared_commonality` は reply が薄くても semantic match と editorial pairing に強い
- tentative: Europe / LatAm の generic 英語 affinity は current profile のままでは `live_conversation` として弱い

#### Profile Actions

- `promote`
  - `en_jp_hobby_bridge_explore`
- `keep`
  - `en_asia_affinity_prompt_live`
  - `ja_asia_affinity_prompt_explore`
  - `en_jp_food_bridge`
- `rotation`
  - `en_europe_affinity_prompt_live`
  - `en_latam_affinity_prompt_live`
  - `en_jp_language_learning_prompt_live`
- `guarded`
  - `generic_country_trait_affinity`
  - `foreigners_compliment_your_culture`
  - `japanese_culture_is_shame`
  - `love_japan_because_social_norms`

#### Next Exploration Slices

- `es/pt` 主体の `LatAm x local_life_affinity`
- `Southeast Asia x local-language citylife/service`
- `Europe x concrete object anchor` (`citylife`, `language`, `service`) 
- `shared_commonality x daily life universals`
- `hobby x rule / etiquette / restriction`
- `mutual_appreciation_question x non-JP country pair`

### 2026-04-15 | `portfolio-diversification-pass-v1`

#### Coverage

- synthesis only; no new collection run
- evidence source: `round1`, `round2 affinity validation`, and operator direction for future English-speaking growth
- scope: query family rebalance, profile typing, and guarded banter design

#### Topic Skew

- current staples still lean `food`, `culture`, and `East Asia`
- `Europe` and `LatAm` remain underexplored unless queries use concrete object anchors or local-language support
- `language` is still thinner than it should be, but is now the best place to test low-stakes English-native participation

#### Winning Archetypes

- `mutual_appreciation_question x East Asia`
- `shared_commonality x daily life`
- `local_life_affinity x Southeast Asia`
- `hobby_constraint_surprise x Japan`
- tentative: `slang_wordplay x language_play`
- tentative: `localization_compare x shared brand`
- tentative: `price_probe x household daily life`

#### Risky Archetypes

- `generic_country_trait_affinity`
- `self_congratulatory_compliment_prompt`
- `country banter x nationality-first framing`
- `anti-individuality praise disguised as admiration`

#### Stable or Tentative Heuristics Added

- tentative: the next expansion axis should be `query family shape`, not raw country count
- tentative: `country_pairs x language_lane x motif x topic_pack x risk_tier` is the right management frame for future profile growth
- tentative: low-stakes banter is useful only when anchored to a concrete word, phrase, or object
- tentative: `en_hub` should become the primary lane even while early operations stay Japan-centered
- tentative: `pt` is a better Brazil bridge than English-only LatAm affinity

#### Profile Actions

- `policy`
  - `en_hub` as the default lane for new frontier families
- `keep`
  - `en_asia_affinity_prompt_live`
  - `ja_asia_affinity_prompt_explore`
  - `en_jp_hobby_bridge_explore`
- `rotation`
  - `en_europe_affinity_prompt_live` into concrete object anchors
  - `en_latam_affinity_prompt_live` into Japan-linked local-life anchors
- `guarded`
  - `en_country_banter_live`
  - all country-trait praise without an object or word anchor
- `promote`
  - `en_jp_slang_wordplay_bridge_explore`
  - `en_jp_price_probe_bridge`
  - `en_jp_localized_chain_compare_explore`
  - `pt_jp_local_life_affinity_explore`

#### Next Exploration Slices

- `slang_wordplay x en_hub x jp_us / jp_gb / jp_au`
- `object_anchor_banter x language_play x guarded`
- `price_probe x home_costs x jp_us / jp_gb / jp_ca / jp_au`
- `localization_compare x chain menu / packaging`
- `pt x jp_br x local_life_affinity`
- `Europe x city_service x concrete object anchor`

### 2026-04-15 | `flexible-conversation-trigger-pass-v1`

#### Coverage

- synthesis only; no new collection run
- scope: concept, collection design, technical design, and profile schema alignment
- motivation: avoid overfitting to pair-only publishing and to early visible topics like food / appreciation

#### Topic Skew

- current docs still reflected early `pairing` and `food / appreciation` bias more than the actual concept requires
- the biggest missing lane was `single_post` multi-country conversation
- low-stakes humor and wordplay were underrepresented despite strong concept fit

#### Winning Archetypes

- tentative: `self_contained_roll_call x daily life`
- tentative: `slang_wordplay x low_stakes_humor`
- tentative: `single_post x multilingual explanation thread`

#### Risky Archetypes

- `country banter x nationality-first framing`
- `dirty joke x direct mockery`
- `generic cultural superiority praise`

#### Stable or Tentative Heuristics Added

- tentative: editorial units should be modeled as `single_post`, `paired_post`, or `hybrid`
- tentative: a post can be WorldGossip-fit even if no matching partner is needed
- tentative: wordplay, euphemism, and slightly dirty humor are valid collection targets when the thread stays explanatory and playful
- tentative: concept and technical docs should describe flexible conversation triggers, not a frozen topic shortlist

#### Profile Actions

- `promote`
  - `en_global_rollcall_conversation_live`
  - `ja_en_wordplay_discovery_explore`
- `keep`
  - `en_jp_slang_wordplay_bridge_explore`
  - `en_jp_price_probe_bridge`
- `guarded`
  - `en_country_banter_live`
  - any nationality-first humor without an object or language anchor

#### Next Exploration Slices

- `single_post x multi-country roll call`
- `slang_wordplay x en_hub x standalone thread`
- `slightly_dirty_euphemism x explanation-first thread`
- `hybrid x single-post-first then later pairing`
