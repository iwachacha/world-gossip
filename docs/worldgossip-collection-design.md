# WorldGossip 収集設計書

作成日: 2026-04-14 JST  
ステータス: Updated with round2 affinity validation and diversification pass (2026-04-15)  
役割: この文書は WorldGossip における `どう投稿を継続収集するか` の実装・運用設計を定義する。企画思想は `project-concept.md`、全体設計は `worldgossip-technical-design.md` を参照する。

## 1. 目的

WorldGossip の収集基盤は、単に「関連投稿を見つける」だけでは足りない。  
必要なのは、`常にトレンドとバズを追いながら、会話が起きやすい投稿を、鮮度・速度・質のバランスを取りつつ継続的に確保すること` である。

この設計の目的は次の 4 つである。

- WorldGossip 向け高適合投稿を継続的に自動収集できるようにする
- `バズ` と `会話性` と `安全性` を分けて評価できるようにする
- query family を増やしても運用が破綻しない仕組みにする
- 収集結果を次の query 改善へ返せるようにする

## 2. Agent Reach 収集ブリーフ

調査ブリーフ
- 目的: WorldGossip 向けの X/Twitter 投稿を継続的かつ高鮮度で収集し、国際交流、比較、軽い議論、小競り合いが起きやすい投稿群を安定供給するための収集基盤を確立する。
- 対象: 日本と他国の文化、生活、好み、誤解、比較、open question、軽い banter、スラング、言葉遊び、低 stakes な笑いを扱う公開 X/Twitter の root post。返信本文、quote 本文、thread 文脈そのものは対象にしない。
- 期待成果物: 実行可能な継続収集設計。query family、収集レーン、single-post / paired-post の使い分け、スケジュール、shortlist 条件、root post refresh 条件、保存項目、改善指標を含む運用仕様。
- 鮮度要件: 実運用では常に実行時点の最新投稿を優先する。特に `hot_trend` レーンは直近 0-6 時間、`live_conversation` は直近 24 時間、`bridge_candidate` は直近 7 日を主窓とする。
- 含める範囲: discovery query 設計、言語別 query family、single-post completion 判定、トレンド追従方法、engagement ベースの host 側フィルタ、root post の `views / replies / quotes` を使った会話性評価、run metadata、evidence 保存、継続改善ループ。
- 除外範囲: 政治、戦争、宗教、排外主義、深刻な差別、スポーツ対立、センシティブ事件、一次収集と無関係な投稿生成ロジック、公開本文の詳細なコピーライティング。
- 地域・言語: 出力は日本語。収集は `ja` と `en` を主軸にし、`ko` `zh` `es` `fr` `pt` を補助とする。初期国軸は日本、アメリカ、韓国、台湾、フランス、ドイツ、東南アジア、中南米の一部。初期運用は日本中心でよいが、中長期の主戦場は `en` とし、`en_hub` の回転率を最も高く保つ。
- 重視ソース: `twitter search` を discovery の主軸にし、必要な場合だけ `twitter tweet` を root post refresh に使う。evidence ledger と host 側 metadata を必須で残す。
- 禁止ソース: `web` や他 SNS への拡張、出所不明の転載、AI 生成ミラー、政治・歴史論争を主題とする投稿群。
- 証拠厳密度: standard。run id、lane、query id、source role、evidence path を明記し、最終判断は host 側で行う。
- 調査スケール: broad
- 前提と仮定: Agent Reach による X/Twitter の read-only collection は PoC で成立確認済みとする。impressions 系の検索条件は不安定とみなし、viral 判定は query ではなく取得後フィルタを主に信頼する。完全自動公開は行わず、収集は review 前提の編集システム向けに最適化する。

## 3. 収集原則

### 3.1 収集は広く、判定は狭く

- discovery は広く拾う
- shortlist 後に必要な場合だけ root post refresh を行う
- review 前に絞り込みを重ねる

### 3.2 バズと会話性を分けて見る

単に `views` が高いだけでは不十分である。  
WorldGossip では次を分けて評価する。

- バズ: `views`, `likes`
- 会話性: `replies`, `quotes`, `reply_velocity`
- 国際性: 多言語 reply、他国言及、cross-country interest
- 安全性: topic risk、歴史論争化しやすさ、片方向の嘲笑

### 3.3 鮮度レーンを分ける

`トレンド追跡` と `マッチ候補探索` は時間窓も目的も異なるため、同じ収集ジョブにしない。

### 3.4 query は family 化し、運用で育てる

単発 query の追加ではなく、`query family -> profile -> lane` の形で管理する。

### 3.4.1 profile は `型` で管理する

今後の query 拡張は、単なる `国追加` ではなく、少なくとも次の 5 軸で profile を持つ。

- `country_pairs`
  - どの国ペア、国クラスターの橋を狙うか
- `language_lane`
  - `en_hub`, `ja_seed`, `local_bridge`
- `motif`
  - `mutual_question`, `local_life_affinity`, `localization_compare`, `slang_wordplay`, `price_probe`, `object_anchor_banter`
- `topic_pack`
  - `food_localization`, `home_costs`, `language_play`, `city_service`, `shared_daily_life`
- `risk_tier`
  - `low`, `medium`, `guarded`
- `assembly_mode`
  - `single_post`, `paired_post`, `hybrid`

この形にすると、たとえば `JP -> US / en_hub / slang_wordplay / language_play / guarded` のように profile を比較でき、国を増やしてもゼロから query 設計をやり直さずに済む。

### 3.4.2 収集対象は `pair 候補` に固定しない

WorldGossip の収集は、最初から `2 投稿をマッチングする前提` に固定しない。  
実運用で扱う editorial unit は次の 3 種類とする。

- `single_post`
  - 1 投稿の中で多国籍会話がすでに始まっている
- `paired_post`
  - 2 投稿を並べることで価値が立ち上がる
- `hybrid`
  - 単体でも成立するが、別投稿と合わせるとさらに強くなる

収集フェーズでは、この 3 つを広く拾い、review 直前でどの unit にするかを決める。

### 3.5 実収集で見えた初期勝ち筋と偏り

2026-04-14 の Agent Reach 実収集 (`worldgossip-collect-20260414-round1`) では、次の `archetype x topic` が明確に強かった。

- `recommendation request x food / snack / convenience`
- `bilateral exchange / AMA x daily life / culture`
- `appreciation prompt x culture / personality / daily life`
- `surprise prompt x travel / service / infrastructure`
- `story seed x cross-country memory`

逆に次は drift が強く、初期自動運用の主力にしない。

- `why / なぜ` に寄りすぎた広い open question
- `people-reference` を広く含む query
- `misunderstanding correction` のうち政治・歴史に触れやすいもの
- `country banter` のうち ideology に接続しやすいもの

ただし、これは `food が普遍的に最強` という意味ではない。  
round1 は seed 自体が `food / appreciation` に寄っており、結果もそのバイアスを含む。  
以後は `強いテーマを複製する` のではなく、`強い会話アーキタイプを別テーマへ展開する` ことを運用原則にする。  
詳細な検証結果は [worldgossip-collection-validation-2026-04-14.md](worldgossip-collection-validation-2026-04-14.md) を参照する。

### 3.6 勝ち筋は `archetype` と `topic` を分離して保存する

WorldGossip の収集知見は、次の 3 層で保存する。

- `archetype`
  - 会話の起点構造。例: `appreciation_prompt`, `bilateral_exchange`, `recommendation_request`
- `topic_bucket`
  - 話題領域。例: `food`, `daily_life`, `infrastructure`, `language`, `customs`, `story`, `humor`
- `profile`
  - 実際の query 実装。`archetype x topic x language_scope` の具体形

この分離により、`food で当たった` をそのまま再生産せず、`recommendation_request が強い` なら `language` や `infrastructure` に横展開できる。  
学習の正本は [worldgossip-research-journal.md](worldgossip-research-journal.md) に蓄積する。

### 3.7 収集はポートフォリオとして運用する

profile は勝率だけでなく、ポートフォリオ上の役割で持つ。

- `staple`
  - 安定して project-fit が高い主力。量を取るが、上限を設ける
- `archetype_expansion`
  - 強い archetype を別 topic へ広げる検証枠
- `frontier`
  - 未確立テーマや未確立言語圏の探索枠
- `rotation`
  - 強いが偏りやすいテーマの待機枠
- `guarded`
  - drift が確認されており、明示再有効化まで自動運用しない枠

また、言語レーン自体もポートフォリオとして配分する。

- `en_hub`
  - 中長期の主戦場。英語圏でそのまま会話が立つ候補を集める
- `ja_seed`
  - 初期の日本中心運用を支える。日英 reply が立つ種として残す
- `local_bridge`
  - `es`, `fr`, `pt` などで country coverage を広げ、のちの英語 editorial 素材を厚くする

当面の目安は `en_hub 55% / ja_seed 30% / local_bridge 15%` とする。

### 3.8 軽い好意表明も採用対象にする

WorldGossip では、必ずしも `強い議論テーマ` を内包している必要はない。  
次の条件を満たすなら、`○○国のこういうところ好き` のような軽い内容も採用対象にする。

- 一定の `views` または `likes` があり、人目に触れている
- reply が少なくても、別国ユーザーが乗りやすい余白がある
- 原文がポジティブで、国際交流の起点として使いやすい
- 政治、差別、歴史論争に接続しにくい

つまり、`議論密度` だけでなく `広く好かれやすい軽交流価値` も見る。

round2 の実収集では、`light_affinity_prompt` は 1 つの振る舞いではなく、少なくとも次の 2 つに分かれることが確認できた。

- `mutual_appreciation_question`
  - `○○のどこが好き？` `○○は△△のどこが好き？` のように、相手国が答えやすい形で問いを置く型
  - `live_conversation` に乗りやすく、reply と mixed-language 交流が立ち上がりやすい
- `local_life_affinity / shared_commonality`
  - `この国で暮らしたい理由` `世界のどこでも似ている営み` のように、軽い好意や共通性を静かに共有する型
  - reply は薄くても `views` `likes` と semantic match のしやすさが高く、`bridge_candidate` として有望

逆に、英語の generic な `one thing I love about <country>` を広い国クラスターにそのまま投げると、fandom、ステレオタイプ、ideology、無関係な固有名詞混入が増えやすい。Europe / LatAm は特にこの傾向が強く、`live_conversation` ではなく `bridge_candidate` か `exploration` として扱う方が安定する。

### 3.9 しょうもない議論は `object anchor` 付きで開く

WorldGossip では、スラング、言い回し、軽い言葉遊び、少しお下品な日常語のような `大人が国を超えて妙に盛り上がる題材` も有望である。  
ただし、これを generic な国民性 banter として開くと drift が非常に強い。

そのため、banter 系は次の条件を満たす場合だけ profile 化する。

- `what do you call this` `why do you call it that` のように質問が具体的
- `chips / crisps`, `fries`, `toilet`, `euphemism`, `slang`, `phrase` のような具体物か具体語に anchored されている
- `race`, `blood`, `civilized`, `foreigners` のような identity discourse に近い語を強く除外する
- 初期は `guarded` で持ち、deep-read 前提で扱う

`国を茶化す` のではなく、`語や物を起点にした low-stakes banter` に限定するのが重要である。

### 3.10 テーマ固定より `会話トリガー` を優先する

初期の検証では `food`, `appreciation`, `AMA` が見えやすかったが、これは seed bias の影響も受けている。  
したがって、今後の運用では `強いテーマの複製` より、次のような `会話トリガーの再利用` を優先する。

- 各国の人が答えやすい問いが置かれている
- 具体語や具体物があり reply が例示で埋まりやすい
- 単体で roll call になっている
- 軽い笑い、言葉遊び、しょうもない disagreement が起きる
- semantic match にも single-post completion にも転べる

topic bucket や topic pack は `硬い分類体系` ではなく、運用上のガードレールである。  
コンセプトに合う会話が立っているなら、テーマ名に縛られず拾う。

## 4. 収集レーン

### 4.1 `hot_trend`

- 目的: 直近で急伸しているバズ投稿を素早く捕まえる
- 窓: `0-6h`
- cadence: `30-60 分`
- 重視指標:
  - `views`
  - `likes`
  - `reply_velocity`
  - `quote_velocity`
- 向く query:
  - open question
  - 文化驚き
  - 生活用品、価格差、料理比較

### 4.2 `live_conversation`

- 目的: すでに reply / quote が立ち上がっている会話型投稿を拾う
- 窓: `6-24h`
- cadence: `2 時間`
- 重視指標:
  - `replies`
  - `quotes`
  - mixed-language reply
  - thread の会話品質

### 4.3 `bridge_candidate`

- 目的: 即時バズではなくても、別国投稿と意味的に組み合わせやすい素材や、単体で後から編集価値が立つ素材を集める
- 窓: `1-7d`
- cadence: `6-12 時間`
- 重視指標:
  - 国タグ
  - culture word
  - semantic bridge になりやすい題材

### 4.4 `exploration`

- 目的: 新しい国、言語、テーマ、query family を試す
- 窓: `1-7d`
- cadence: `1 日 1-2 回`
- 重視指標:
  - 新規性
  - ノイズ率
  - shortlist 率

### 4.5 `recheck`

- 目的: 強い query family を別窓で再走査し、見逃しを補う
- 窓: `6-24h`, `24-72h`
- cadence: `1 日 2 回`
- 重視指標:
  - missed hit の回収
  - velocity の追跡

## 5. query family 設計

### 5.1 `open_question_cross_country`

- 典型: 「アメリカ人に質問があります」「なぜ日本ではこうなの？」
- 強い理由:
  - reply が増えやすい
  - 自分語りが始まりやすい
  - 国際交流の導線になりやすい
- 主戦言語:
  - `ja`
  - `en`

### 5.2 `admiration_surprise`

- 典型: 他国文化への驚き、称賛、感心
- 強い理由:
  - 安全寄り
  - 投稿の導入にしやすい
  - 観光、生活、食のテーマへ広げやすい

### 5.3 `temperature_gap_comparison`

- 典型: 同じ題材への国ごとの温度差
- 強い理由:
  - WorldGossip の編集価値が高い
  - 意味マッチングと相性が良い

### 5.4 `misunderstanding_correction`

- 典型: 「実はそうではない」「誤解されがちな日本」
- 強い理由:
  - 会話が深まりやすい
  - reply に体験談が増えやすい
- 注意:
  - 歴史論争やナショナル感情に接続しやすい場合がある

### 5.5 `food_price_daily_life`

- 典型: 食、菓子、BBQ、価格差、便利グッズ
- 強い理由:
  - reply が伸びやすい
  - 安全性が高い
  - 国際比較の軸が明確

### 5.6 `translation_babel_bridge`

- 典型: 自動翻訳経由で多国籍 reply が集まる投稿
- 強い理由:
  - WorldGossip の世界観に合う
  - 多国籍交流の可視化に向く
- 注意:
  - 政治や思想へ飛びやすいので safety 強化が必要

### 5.7 `friendly_banter`

- 典型: 軽い挑発、国ごとの pride、茶化し
- 強い理由:
  - エンタメ性が高い
  - 比較軸が自然に立つ
- 注意:
  - 片方向の嘲笑や排外表現へ寄ると即除外
  - 今後は `country trait` より `object anchor` を優先する
  - `slang`, `word choice`, `chips / crisps`, `toilet euphemism` のような concrete banter のみ guarded で試す

### 5.8 `appreciation_prompt`

- 典型: 「日本のどこが好き？」「アメリカのどこが好き？」「褒められると嬉しい？」
- 強い理由:
  - 低 views でも reply 密度が高い
  - 双方向会話に育ちやすい
  - `food`, `daily life`, `culture`, `personality` に自然展開しやすい
- 注意:
  - 一方向の self-congratulation に寄るものは弱い

### 5.9 `light_affinity_prompt`

- 典型: 「○○国のこういうところ好き」「この国のこういう日常好き」「one thing I love about ...」
- 強い理由:
  - 重い論点がなくても広く反応されやすい
  - quote や軽い reply で国際交流が生まれやすい
  - 後段の semantic match で別国の類似好意投稿と組みやすい
- 向く topic:
  - `culture`, `daily_life`, `service`, `citylife`, `language`, `hobby`
- 注意:
  - 単なる内輪自慢や一方向 praise account になっていないかを見る
  - country anchor が弱い generic positivity は除く
  - `mutual_appreciation_question` の形で相手国が答えやすいと強いが、generic な `one thing I love about <country>` は noise とステレオタイプに埋もれやすい
  - `foreigners compliment your culture` `proud of your country` は self-congratulation や nationalist drift に寄る場合があるので guarded review を掛ける
  - Europe / LatAm は英語の国名直打ちだけでは薄くなりやすく、具体物アンカーか現地語補助を前提にする

### 5.10 `slang_wordplay_compare`

- 典型: 「これ英語で何て言うの？」「そのスラングどういう意味？」「国によって言い方違う？」 
- 強い理由:
  - 英語圏 audience にそのまま刺さりやすい
  - 回答が具体例になりやすく、reply が積みやすい
  - translation bridge と違って ideology へ飛びにくい
- 注意:
  - fandom や内輪 meme に寄りすぎると WorldGossip fit が落ちる
  - slur、歴史、宗教、地政学に近い語は除外する

### 5.11 `localization_compare`

- 典型: 「日本版の KitKat」「国ごとに違う McDonald's」「同じチェーンなのに味やパッケージが違う」
- 強い理由:
  - 共有ブランドがあるため reply が入りやすい
  - generic 国民性比較より安全
  - `food` だけでなく `daily_life` としても広げやすい
- 注意:
  - brand 公式や広告だけで終わる投稿は downrank する

### 5.12 `price_probe`

- 典型: 「これそっちではいくら？」「キッチン用品や日用品の価格差」「その値段で何が買える？」
- 強い理由:
  - 安全性が比較的高い
  - 生活コスト差から家、食、買い物の会話へ広がる
  - 英語圏の参加者が自国価格を書き込みやすい
- 注意:
  - politics, wages, immigration 論争へつながる語を避ける

### 5.13 `self_contained_multinational_thread`

- 典型: 「Where are you from and what do you call this?」「各国のみんな朝ごはん何食べる？」のような roll call 型
- 強い理由:
  - 1 投稿だけで多国籍会話が完結しうる
  - pair 前提でなくても WorldGossip fit が高い
  - 後から `paired_post` に転用する余地もある
- 注意:
  - 問いが broad すぎると generic chatter に埋もれる
  - 具体物、具体語、具体習慣で anchor する

### 5.14 `low_stakes_humor_wordplay`

- 典型: スラング、ダジャレ、婉曲表現、少し下品な言い回しの比較
- 強い理由:
  - 英語圏 audience に直で刺さりやすい
  - `うちではこう言う` が自然発生しやすい
  - 言語比較でありながら、説明 reply と笑い reply の両方が立つ
- 注意:
  - slur、宗教、歴史、差別に接続する語は除外する
  - 下品さは許容しても、攻撃性は許容しない

## 6. query profile スキーマ

`query_profiles` には最低でも次を持たせる。

- `id`
- `name`
- `lane`
- `priority`
- `channel`
- `operation`
- `query_template`
- `language_scope`
- `country_scope`
- `intent_tags_json`
- `archetype_tags`
- `topic_bucket`
- `country_pairs`
- `language_lane`
- `motif`
- `topic_pack`
- `risk_tier`
- `editorial_modes`
- `maturity`
- `portfolio_role`
- `expected_reply_driver`
- `target_reply_min`
- `exclude_pack`
- `window_hours`
- `cadence_minutes`
- `discovery_limit`
- `deep_read_budget`
- `gate_policy_json`
- `exclusions_json`
- `enabled`

### 6.1 推奨 YAML 例

```yaml
id: ja_us_open_question_hot
name: ja -> us open question hot
lane: hot_trend
priority: 100
channel: twitter
operation: search
editorial_modes: ["single_post", "paired_post"]
country_pairs: ["jp_us"]
language_lane: "ja_seed"
motif: "mutual_question"
topic_pack: "shared_daily_life"
risk_tier: "guarded"
expected_reply_driver: "direct_answers"
target_reply_min: 80
exclude_pack: ["core_safe"]
query_template: '("アメリカ人" OR "アメリカ") ("質問" OR "どうして" OR "なぜ") ("日本" OR "日本人") lang:ja -政治 -戦争 -移民 -選挙'
language_scope: ["ja"]
country_scope: ["jp", "us"]
intent_tags_json: ["open_question", "conversation_start", "cross_country"]
window_hours: 6
cadence_minutes: 30
discovery_limit: 20
deep_read_budget: 3
gate_policy_json:
  min_views: 80000
  min_replies: 80
  min_quotes: 10
  require_country_anchor: true
exclusions_json:
  blocked_topics: ["politics", "war", "religion", "xenophobia"]
  blocked_terms: ["参政権", "北朝鮮", "選挙"]
enabled: true
```

## 7. host 側の二段ゲート

### 7.0 pre-DB noise gate

2026-04-15 JST の root-only 実測では、代表 5 query / 40 item の中に次が目立って混ざった。

- `@` 始まりの reply-like post
- `詳細はこちら` や短文リンクだけの link stub
- news / media / official / promo 系の broadcast post
- `views < 5000` の低 traction post
- 国アンカーはあるが cross-country conversation seed がない post

したがって、DB 保存前に少なくとも次を掛ける。

- `text` または `title` が `@` で始まる post は破棄する
- `詳細はこちら`、URL 主体、極端に短い本文の post は破棄する
- 外部リンク主体で、質問・比較・roll-call・説明導線のない news / brand broadcast post は破棄する
- `views < 5000` は lane に関係なく破棄する
- 正規化後に country anchor と cross-country seed の両方が弱い post は破棄する

### 7.1 discovery gate

query で完全に絞り込まず、取得後に host 側で次を見る。

- hard exclusion topic に当たらないか
- 国アンカーがあるか
- `motif` と `topic_pack` が root post に現れているか
- 単体で reply 欄が完結している `self-contained` 候補か
- culture / comparison / question のどれかを含むか
- lane ごとの最低指標を満たすか

### 7.2 shortlist gate

lane ごとに閾値を変える。

#### `hot_trend`

- `views >= 150000`
  または
- `replies >= 200`
  または
- `reply_velocity >= 25 / hour`

#### `live_conversation`

- `replies >= 120`
  または
- `quotes >= 40`
  または
- mixed-language reply が十分ある

#### `bridge_candidate`

- `views >= 30000`
  または
- `replies >= 40`
  または
- semantic bridge スコアが高い

#### `single_post` 補助条件

- `replies` や `quotes` に複数国の参加が見える
  または
- roll call / explanation / playful comparison のいずれかで thread が自己完結している

また、lane 閾値に加えて profile ごとの `target_reply_min` と `expected_reply_driver` を見る。

- `mutual_question`
  - direct answer が連続しているか
- `local_life_affinity`
  - 例示 reply や quote が付いているか
- `slang_wordplay`
  - 言い換え例、各国例、訂正 reply が立っているか
- `object_anchor_banter`
  - 茶化しではなく playful vote と補足説明が中心か
- `self_contained_roll_call`
  - 投稿単体の中で多国籍参加が成立しているか

### 7.3 diversity gate

同じテーマや国ペアばかりにならないよう、`portfolio gate` を掛ける。

- 同一 `topic_bucket` は日次 shortlist の `25%`、1 バッチ deep-read の `2 件` を上限とする
- 1 バッチ shortlist では `4` 以上の `topic_bucket` と `3` 以上の `archetype` を含める
- 毎日少なくとも `1` 本は `frontier` profile から shortlist する
- `ja -> en` 以外の profile を毎週必ず回し、1 言語圏に固定しない
- `language_lane` は `en_hub 55% / ja_seed 30% / local_bridge 15%` を目安に維持する
- `food` は強い staple として残すが、`food を増やすこと` 自体は成功条件にしない
- cap 超過時は、同 bucket の次点候補を落とし、未充足 bucket に `portfolio_gap_bonus` を配る

### 7.4 実運用スコア

shortlist は単一閾値ではなく lane score で見る。

- `archetype_fit`
  - `recommendation_request`, `bilateral_exchange`, `appreciation_prompt`, `light_affinity_prompt`, `story_seed`, `surprise_prompt`
- `topic_fit`
  - `food`, `daily_life`, `culture`, `travel`, `infrastructure`, `language`, `customs`, `story`, `humor`
- `conversation_density`
  - `replies / views`
  - `quotes / views`
- `broad_appeal`
  - `views`
  - `likes`
  - 軽い好意表明でも広く刺さっているか
- `multi_family_overlap`
  - 異なる profile からの再発見回数
- `freshness`
  - `published_at` と `observed_at` の差
- `bridgeability`
  - 別国投稿と意味的に組めるか
- `self_contained_bonus`
  - single-post のまま公開価値が成立しているか
- `reply_driver_fit`
  - profile の `expected_reply_driver` に合う reply 形が立っているか
- `topic_diversity_bonus`
  - 同 run 内で不足している `topic_bucket` に補正を掛ける
- `portfolio_gap_bonus`
  - `frontier` または未探索 bucket の候補を押し上げる
- `light_exchange_bonus`
  - 強い議論でなくても、別国ユーザーが反応しやすい余白を評価する
- `safety_penalty`
  - 政治、移民、戦争、基地、歴史論争、片方向の嘲笑

初期重みの考え方:

- `views` は話題性指標として使うが、単独 keep 条件にしない
- `conversation_density` と `archetype_fit` を `views` より重く扱う
- `topic_fit` は必要だが、単独で強い加点にしすぎない
- `light_affinity_prompt` では `broad_appeal` と `light_exchange_bonus` を厚めに見る
- `light_affinity_prompt` でも、具体物アンカーや相互質問のある候補を generic 国民性 praise より優先する
- `multi_family_overlap >= 2` は強い加点にする
- `portfolio_gap_bonus` で未探索 bucket を毎回必ず混ぜる
- brand 公式、報道、recommendation item は減点する

## 8. root refresh ポリシー

責任分界:

- ここは `WorldGossip` host 側の filter layer として持つ
- `Agent Reach` は search transport と artifact 保持を担う薄い層として扱う
- ただし将来 `reply/root 判定 metadata` を増やしたくなった場合は、`Agent Reach` か `twitter-cli` を project 内へ取り込んで拡張する余地がある
- 初期 policy は [twitter_precision_policy.yml](/c:/WorldGossip/config/twitter_precision_policy.yml) を正本にし、実装は [filters.py](/c:/WorldGossip/src/worldgossip_twitter/filters.py) に寄せる

### 8.1 root refresh 対象

`tweet` は次にだけ当てる。

- lane 上位候補
- `views` `replies` `quotes` の公開メトリクスを再確認したい候補
- search で `engagement_complete=false` だった候補

### 8.2 root refresh で保存するもの

- root post
- root id
- 最新 engagement snapshot
- media completeness
- requested root URL

### 8.3 discard ルール

少なくとも次を行う。

- 入力は root URL に限定する
- `tweet` の返り値に複数 item が含まれても `requested root id` と一致する root post 以外はすべて破棄する
- reply、quote、thread item、recommendation noise は保存しない
- recommendation item は editorial unit 生成対象から除外する
- brand 公式や報道リンク主体の item は discovery 参考扱いにする

## 9. `post_observations` の必要性

継続収集では、同じ post が別 run、別 lane、別 query から何度も見つかる。  
そのため `posts` だけでは足りず、観測履歴を別に持つ必要がある。

`post_observations` に持つべき項目:

- `id`
- `post_id`
- `collection_run_id`
- `query_profile_id`
- `lane`
- `source_role`
- `observed_at`
- `result_rank`
- `engagement_json`
- `raw_item_path`
- `is_shortlist_candidate`

`source_role` は少なくとも次を持つ。

- `search_result`
- `root_refresh`

これにより、次が可能になる。

- 見逃しの補足
- query family ごとの再発見率測定
- root engagement の再観測
- 同じ post の時間変化の追跡

## 10. スケジュールと予算

### 10.1 推奨 cadence

- `hot_trend`: 30-60 分ごと
- `live_conversation`: 2 時間ごと
- `bridge_candidate`: 6-12 時間ごと
- `exploration`: 1 日 1-2 回
- `recheck`: 1 日 2 回

### 10.2 実行予算の考え方

初期は `query 本数` より `lane ごとの候補密度` を重視する。

- 強い family は高頻度、低本数で回す
- 弱い family は低頻度、比較目的で回す
- deep-read 予算は `lane ごとの上位 2-5 件` に制限する

## 11. 継続改善ループ

### 11.1 profile 単位で見る指標

- discovery hit rate
- shortlist rate
- deep-read success rate
- topic bucket share
- archetype coverage
- frontier success rate
- multi-family hit rate
- danger hit rate
- judge keep rate
- review approve rate
- publish rate
- published post performance

### 11.2 retire / promote 条件

- 7 日以上 shortlist 率が低い profile は保留
- approve rate が高い profile は cadence を上げる
- ノイズ率が高い profile は exclusion を見直す
- 強い archetype が `2` 以上の topic bucket で通ったら派生 profile を増やす
- 同一 topic bucket が cap 超過を続けるなら cadence を下げるか `rotation` に落とす
- `frontier` profile は即 retire せず、まず query の狭化か topic の切り替えを試す
- `danger hit rate` が高い profile は guarded へ落とす

## 12. 実装タスク

### Phase 1

- `worldgossip-technical-design.md` に合わせて `post_observations` を追加
- `query_profiles` に lane 系フィールドを追加
- lane scheduler を実装
- discovery gate と shortlist gate を実装
- `multi_family_overlap` を計算して shortlist score に入れる

### Phase 2

- reply velocity と quote velocity を計算
- diversity gate を追加
- query family ごとの profile health 集計を追加
- `topic_bucket` と `archetype_tags` を shortlist 集計に含める

### Phase 3

- profile auto-retire / auto-promote 提案
- weak lane の exploration 自動生成補助
- research journal 更新フローを運用に組み込む

## 13. 最終方針

WorldGossip の収集基盤は、`query を増やす` こと自体が目的ではない。  
目指すのは、`強い会話型バズを早く見つけるレーン`、`単体で完結する多国籍会話を拾うレーン`、`意味マッチ候補を厚くするレーン`、`新しい勝ち筋を探すレーン` を同時に運用し、継続的に高品質な投稿素材を供給することである。

そのための中核は次の 5 点である。

- lane ベースで収集を分ける
- query family で増やす
- host 側の二段ゲートで絞る
- `post_observations` で観測履歴を残す
- run 結果を次の query 改善に返す
- `強いテーマ` ではなく `強い会話アーキタイプ` を学習する
- `ペア前提` に固定せず `single_post / paired_post / hybrid` を使い分ける
- `強い議論` だけでなく `広く好かれる軽交流投稿` も扱う
- `きれいな文化比較` だけでなく `スラング・ダジャレ・しょうもない議論` も low-stakes に扱う
- research journal に汎用知見と偏り記録を残す
## 14. 2026-04-15 Precision Addendum

- validated run:
  - `22` enabled query profiles
  - `172` seen posts
  - `169` unique post ids
  - `4` kept after dedupe plus full gating
- bulk collection is now a four-step precision pipeline:
  - query shaping
  - generic pre-DB gate
  - profile-aware threshold gate
  - DB persist
- generic pre-DB gate is responsible for removing:
  - reply-like roots
  - weak-conversation roots
  - link stubs
  - broadcast-like roots
  - travel / destination / relocation prompts
  - identity-validation prompts
- profile-aware threshold gate is responsible for removing:
  - `WorldGossip-fit but too small` roots
  - roots below the profile's `min_views / min_replies / min_quotes`
- dedupe rule:
  - candidate evaluation and DB ingest both dedupe on `post_id`
  - multi-query matches remain metadata, not separate ingest rows
- collection artifact rule:
  - Twitter/X search snippets should use at least `560` chars
  - shorter snippets created false `missing_cross_country_seed`
- bulk-safe disabled profiles remain:
  - `en_europe_affinity_prompt_live`
  - `en_latam_affinity_prompt_live`
  - `en_translation_bridge_live`
