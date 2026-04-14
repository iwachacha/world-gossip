# WorldGossip 収集検証レポート 2026-04-14 Round 2 Affinity Validation

作成日: 2026-04-14 JST  
run_id: `worldgossip-collect-20260414-round2-affinity-validation-v2`  
対象期間: discovery は主に `2026-04-07` から `2026-04-15`、profile の lane に応じて一部 `2026-04-11` / `2026-04-12` 開始  
主目的: `light_affinity_prompt` と国クラスター拡張の設計変更を、最新の実データで再検証する

関連 artifact:

- evidence ledger: [.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/evidence.jsonl](../.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/evidence.jsonl)
- discovery analysis: [.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/analysis-summary.json](../.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/analysis-summary.json)
- deep-read summary: [.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/deep-summary.json](../.agent-reach/worldgossip-collect-20260414-round2-affinity-validation-v2/deep-summary.json)

## 1. Coverage

- discovery query: `15`
- seen items: `238`
- unique candidate: `231`
- duplicate candidate (`multi_family_overlap >= 2`): `4`
- deep-read: `16`
- primary channel: `twitter search`
- deep-read channel: `twitter tweet`

今回の discovery は、重点検証 12 profile に加えて、`Europe / LatAm / Southeast Asia` の direct phrase 補助 query を 3 本だけ追加した。  
`items_seen` は目標レンジ (`180-300`) に収まり、`deep-read` も目標レンジ (`10-16`) を満たした。

## 2. 結論

今回の設計修正は `部分的には妥当` だが、`light_affinity_prompt` を 1 つの運用形で扱う前提は弱かった。

結論を短く言うと次の通り。

- `light_affinity_prompt` 自体は有効
  - ただし強かったのは `mutual_appreciation_question` と `local_life_affinity / shared_commonality`
- `country expansion` は nominal coverage は増やしたが、quality を保った diversity にはまだつながっていない
  - `multi_family_overlap` は `4` 件しかなく、`East Asia` へ強く偏った
- `Europe / LatAm` の generic 英語 affinity query は、`live_conversation` としては弱い
  - `bridge_candidate` か `exploration` として扱うべき
- `Southeast Asia` は英語の直接 prompt より、現地語の生活実感ポストの方が強い
- `food` 以外では `hobby` と `infrastructure` が明確に伸びた
  - ただし `infrastructure` は `hot_trend` というより `broad_appeal + bridgeability` 型だった

## 3. 主要所見

### 3.1 `light_affinity_prompt` は 2 つの mode に分けるべき

#### 1. `mutual_appreciation_question`

成功例:

- `Green_k100`
  - `https://x.com/Green_k100/status/2043694329760260262`
  - `8,395 views / 198 replies / 13 quotes`
  - `Japan what is one thing you like about America?`

この型は、強い議論がなくても `reply density` と `light_exchange_bonus` が両立した。  
reply には日本語・英語が混ざり、`自由`, `前進する精神`, `好きなところも嫌いなところも多い` のような軽い温度差が自然に出た。

#### 2. `local_life_affinity / shared_commonality`

成功例:

- `Kerymai_`
  - `https://x.com/Kerymai_/status/2043209687445954673`
  - `693,320 views / 83 replies / 71 quotes`
  - タイで暮らしたい外国人の話から、生活幸福度や人の気質を語る thread
- `estem_info`
  - `https://x.com/estem_info/status/2042847530715877763`
  - `481,680 views / 15 replies / 50 quotes`
  - 韓国の「冷麺始めました」、おばあちゃんの空き缶裁縫箱、猫を溺愛する父など、世界共通性を語る post

この型は `conversation_density` 自体は高くないが、`views`, `likes`, semantic match のしやすさが高い。  
WorldGossip 的には `bridge_candidate` として非常に価値がある。

### 3.2 generic な `one thing I love about <country>` は弱い

失敗例:

- `williameijer`
  - `https://x.com/williameijer/status/2043030688752980173`
  - `26,047 views / 11 replies / 739 likes`
  - `One thing I like about the French is how blunt they are`
- `hodophiliac`
  - `https://x.com/hodophiliac/status/2043151449274847736`
  - `99 views / 0 replies`
  - `One thing I love about Japanese society is how they brutally enforce social norms`

Europe は `likes` がある例も見えたが、reply が薄く、しかも `national trait` への固定観念や ideology に寄りやすかった。  
LatAm はさらに弱く、英語 query の direct phrase 補助でも `1` 件しか追加で取れなかった。

### 3.3 クラスター拡張は as-is では偏る

heuristic な cluster keyword hit は次の通りだった。

- `East Asia`: `105`
- `Europe`: `57`
- `LatAm`: `14`
- `Southeast Asia`: `8`

`East Asia` が圧倒的に強く、`LatAm` と `Southeast Asia` は探索不足というより、現在の query 設計では質のある surface が薄い。  
特に `en_latam_affinity_prompt_live` は `max_views 736 / max_replies 3 / median_views 16` とほぼ不成立だった。

## 4. クラスター別 findings

### 4.1 East Asia

有望パターン:

- `mutual_appreciation_question`
  - `Japan what is one thing you like about America?`
- `compliment modesty exchange`
  - `Japan do you like when foreigners compliment your culture?`
- `shared_commonality`
  - 韓国・世界の共通生活感覚をつなぐ post

失敗パターン:

- `foreigners compliment your culture`
  - 交流にはなるが、`日本を褒めると日本人は喜ぶ` という一方向 self-congratulation に寄りやすい

評価:

- `light_affinity_prompt` は East Asia では成立
- ただし generic praise より `相手国が答えられる質問` が必要

### 4.2 Southeast Asia

有望パターン:

- `local_life_affinity`
  - タイで暮らしたい理由、タイ人の気質、生活幸福度の説明

失敗パターン:

- 英語 direct phrase
  - `What do you like about Thailand?` は `8 views / 0 replies`

評価:

- Southeast Asia は `英語 affinity prompt` ではなく、現地語の生活実感ポストを拾って semantic match 候補に回す方が強い

### 4.3 Europe

有望パターン:

- `likes` はあるが会話密度は薄い `national trait affinity`

失敗パターン:

- generic national trait praise
- sports / betting / unrelated topical chatter

評価:

- Europe の generic affinity は `live_conversation` として弱い
- 次は `citylife`, `language`, `service`, `daily_life` など concrete object を入れるべき

### 4.4 LatAm

有望パターン:

- 今回は明確な有望例を持ち帰れなかった

失敗パターン:

- 英語の direct phrase affinity
- beauty / identity / politics 混入

評価:

- `en_latam_affinity_prompt_live` は current shape ではほぼ失敗
- `es` / `pt` 主体か、`Japan x LatAm` の concrete bridge に切り替える必要がある

## 5. profile audit

### 5.1 重点検証 profile

- `en_asia_affinity_prompt_live`
  - `partial pass`
  - archetype 自体は有効だが query が広すぎた
  - `mutual_appreciation_question` に寄せて keep
- `en_europe_affinity_prompt_live`
  - `fail as live_conversation`
  - bridge probe へ降格が妥当
- `en_latam_affinity_prompt_live`
  - `fail`
  - 英語のみでは薄すぎるため `exploration` へ降格が妥当
- `ja_asia_affinity_prompt_explore`
  - `pass`
  - 東アジアだけでなく Southeast Asia の local-life affinity を持ち帰れた
- `en_jp_infrastructure_reaction_hot`
  - `partial pass`
  - broad appeal はあるが hot density が弱いので lane mismatch
- `en_jp_language_learning_prompt_live`
  - `fail current template`
  - broad learning/translation 語が広すぎる
- `en_jp_customs_microculture_explore`
  - `fail current template`
  - complaint / manners meta に流れやすい
- `en_jp_hobby_bridge_explore`
  - `pass`
  - food 以外の frontier で最も良かった

### 5.2 control profile

- `en_jp_appreciation_prompt_live`
  - archetype は still strong
  - ただし query が broad すぎて generic America discourse を大量混入
- `en_jp_country_exchange_ama_live`
  - valid control
  - recall は低いが overlap で効いた
- `en_jp_food_bridge`
  - strongest control
  - ただし `food が強い` ではなく `recommendation_request` が強い
- `en_translation_bridge_live`
  - conversation engine としては弱い
  - ただし bridgeability source としては残す価値がある

## 6. deep-read で見えたこと

### 6.1 broad_appeal + cross-country friendliness の好例

- `FiredUpCoug`
  - `Japanese breakfast` を尋ねる food question
  - 日本語 reply が写真付きで集まり、英語で追加質問が返る
- `GloryDoge`
  - `7-11 in Japan, which snack should I buy?`
  - 日本語 reply と英語 self-reply が自然に交差した
- `indietrucker`
  - `campfire` という concrete object が説明を呼び、文化差比較が敵対化しない

### 6.2 semantic match 素材として強いもの

- `estem_info`
  - shared commonality の塊で、別国の類似 post と組みやすい
- `Kerymai_`
  - 「なぜここに住みたいのか」という local-life affinity で、別国の mirror post を探しやすい
- `Mengu09`
  - `coin -> metro info point` は infrastructure / public ethics の micro-observation として matchable

### 6.3 failure deep-read で確認できた drift

- `alexathallow`
  - `Sad day to be an American`
  - appreciation query から宗教・政治論争を回収してしまった
- `TheLaurenChen`
  - `My favorite part of Japanese culture is actually the shame`
  - 片方向の mockery に近く、WorldGossip fit が低い
- `hodophiliac`
  - `love about Japanese society is how they brutally enforce social norms`
  - affinity を装った anti-individuality praise で guarded が妥当

## 7. 新しく guarded にすべきパターン

- `generic_country_trait_affinity`
  - `French are blunt`, `Japanese enforce social norms` のような雑な国民性 praise
- `self_congratulatory_compliment_prompt`
  - `外国人に褒められると嬉しい？` 自体は使えるが、reply が national pride 自慢に寄ると弱い
- `generic_us_uk_affection_without_exchange`
  - appreciation query で generic domestic politics や religion を拾う
- `targeted reply deep-read normalization blind spot`
  - reply URL に `tweet` deep-read を当てても親 thread root に正規化されることがある

## 8. 実施した改善

- `config/query_profiles.yml`
  - `en_jp_appreciation_prompt_live` を bilateral prompt 寄りに tighten
  - `en_asia_affinity_prompt_live` を direct mutual appreciation phrasing に寄せた
  - `en_europe_affinity_prompt_live` を `bridge_candidate` へ降格
  - `en_latam_affinity_prompt_live` を `exploration` へ降格
  - `en_jp_infrastructure_reaction_hot` を `bridge_candidate` 寄りに再配置
  - `en_jp_language_learning_prompt_live` を narrow prompt に書き換え
  - `en_jp_customs_microculture_explore` を positive micro-observation に寄せた
  - `en_jp_hobby_bridge_explore` の priority を上げた
- `docs/worldgossip-collection-design.md`
  - `light_affinity_prompt` を `mutual_appreciation_question` と `local_life_affinity / shared_commonality` に分けて記述
  - `tweet` deep-read が親 thread root に正規化されるケースを保存要件に反映

## 9. 次ラウンドで増やすべきもの

- `es/pt` 主体の `LatAm x local_life_affinity`
- `Southeast Asia x local-language citylife/service`
- `Europe x concrete object anchor`
  - `service`, `city routine`, `language`, `small public etiquette`
- `shared_commonality x daily life universals`
- `hobby x restriction / etiquette / rule`
- `mutual_appreciation_question x non-JP pair`

## 10. 最終評価

今回の設計修正で一番正しかったのは、`軽い好意表明も採用対象にする` という方針そのものだった。  
実際に強かったのは `強い議論` ではなく、`相手が答えやすい軽質問`, `暮らしの良さ`, `世界の共通性`, `趣味や小さな制約` を起点にした会話だった。

一方で、設計の修正だけでは足りず、次の 3 点はさらに直す必要がある。

1. `light_affinity_prompt` を一枚岩として扱わない  
2. `Europe / LatAm` を generic 英語 query のまま `live_conversation` に置かない  
3. `appreciation_prompt` を broad affection term だけで回さない

つまり、`light_affinity` は当たりだったが、`どの cluster でも同じ query の広げ方で当たる` という仮説は外れた。  
今後は `archetype は共通化し、query surface と lane は cluster ごとに変える` 方針が必要である。
