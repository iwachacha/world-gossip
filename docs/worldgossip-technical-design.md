# WorldGossip 技術設計書

作成日: 2026-04-14 JST  
ステータス: Revised for flexible editorial units (2026-04-15)
役割: この文書は WorldGossip の実装仕様を定義する正本である。企画思想は `project-concept.md`、採用判断は `worldgossip-optimal-design.md`、収集詳細は `worldgossip-collection-design.md` を参照する。

## 1. スコープ

この設計書は、WorldGossip の MVP から初期本番までを対象とする。  
対象は `X/Twitter 上の公開投稿を収集し、会話が起きやすい editorial unit を抽出し、人間レビュー後に公開する編集支援システム` である。

ここでいう editorial unit は次の 3 種類を持つ。

- `single_post`
  - 1 投稿だけで多国籍会話の起点になっているもの
- `paired_post`
  - 2 投稿を並べることで温度差や共通点が立つもの
- `hybrid`
  - 単体でも成立し、並置しても強くなるもの

初期は次を前提とする。

- source は X/Twitter のみ
- 主戦場は `ja` と `en`
- 国軸は `日本` を中心に始める
- 公開は human-in-the-loop
- 投稿本文はテンプレートベース

## 2. 非目標

初期段階では次を目標にしない。

- 全世界全言語の同時対応
- 完全自動投稿
- ニュース、政治、歴史論争の取り扱い
- 全件翻訳保存
- 汎用ワークフロー基盤の導入
- 専用ベクトル DB の導入

## 3. 最終採用スタック

### 3.1 コア

- 言語: `Python 3.12`
- アプリ: `FastAPI`
- 収集: `Agent Reach`
- DB: `Supabase Postgres`
- vector search: `pgvector`
- lexical search: `PGroonga`
- 言語判定: `lingua-py`
- embeddings: OpenAI `text-embedding-3-large` with `dimensions=1024`
- final judge: OpenAI `gpt-5.4-nano` with Batch API
- publish: `twitter-cli`

### 3.2 ジョブ実行

- 開発: `Windows Task Scheduler`
- 本番初期: `cron`
- 後日追加可能: `Supabase Cron`

## 4. システム構成

### 4.1 論理構成

1. `collector`
   - `Agent Reach` を使い `twitter search` を実行する
   - shortlist 後に `twitter tweet` deep-read を実行する
2. `ingestor`
   - 取得結果を正規化し、`posts` へ upsert する
3. `normalizer`
   - 言語、国タグ、文化語、会話フック、危険語を付与する
4. `embedder`
   - 新規 post に embeddings を生成する
5. `assembler`
   - single-post 候補の抽出と pair 候補の組成を統合し、候補 editorial unit を作る
6. `judge`
   - 上位候補だけを `gpt-5.4-nano` で最終判定する
7. `review-ui`
   - reviewer が候補を確認し、問いと本文を編集する
8. `publisher`
   - 承認済み draft に対し `twitter-cli post` を実行する
9. `observer`
   - 公開後の反応を保存し、次回スコアへ返す

### 4.2 物理構成

```text
app/
  FastAPI
  review UI
  internal API

jobs/
  collect-search
  ingest-posts
  normalize-and-tag
  embed-posts
  assemble-candidates
  deep-read-shortlist
  judge-units
  observe-feedback

db/
  Supabase Postgres
  post_observations
  pgvector
  PGroonga
```

初期は Redis、Celery、n8n、Qdrant を持たない。

## 5. 処理フロー

### 5.1 全体フロー

1. `collect-search`
2. `ingest-posts`
3. `normalize-and-tag`
4. `embed-posts`
5. `assemble-candidates`
6. `deep-read-shortlist`
7. `judge-units`
8. `review-and-publish`
9. `observe-feedback`

### 5.2 `collect-search`

- `query_profiles` に基づき `Agent Reach twitter search` を実行する
- evidence は run 単位で保存する
- 取得後に host 側で `views` `replies` `quotes` を二次評価する
- 収集は `hot_trend` `live_conversation` `bridge_candidate` `exploration` `recheck` の lane 単位で回す

初期の強い query family は固定テーマとして凍結せず、次のような `会話トリガー` を優先して広く持つ。

- answerable question
- self-contained multinational roll call
- slang / wordplay / euphemism
- localization compare
- price / household probe
- low-stakes banter with object anchors
- translation relay

### 5.3 `ingest-posts`

- 取得 item を `posts` に upsert する
- raw payload 全体は DB に持たず、必要最小限だけ JSON として持つ
- evidence ledger への path を保持する
- 一意キーは `(source_platform, source_post_id)` とする
- 同時に `post_observations` に `どの run / lane / query で見つかったか` を記録する

### 5.4 `normalize-and-tag`

次を軽量処理で付与する。

- 言語判定
- body normalization
- 国名、デモニム、文化語の抽出
- topic flag
- safety flag
- tone label
- interaction style label
- conversation hooks

ここでは高価な推論は使わず、`lingua-py + 辞書 + ルール` を基本とする。

### 5.5 `embed-posts`

- `post_embeddings` 未生成の post にだけ embeddings を打つ
- モデルは `text-embedding-3-large`
- `dimensions=1024` を指定する
- embedding 対象は原文ベースとする

### 5.6 `assemble-candidates`

候補生成は 2 レールで行う。

- `single-post candidates`
  - reply density
  - mixed-language participation
  - self-contained roll call
  - explanation thread
  - low-stakes humor / wordplay
- `paired-post candidates`
  - vector candidates
  - lexical candidates

この 2 レールを統合し、`candidate_units` を作る。
`candidate_units` は `assembly_mode` により `single_post` / `paired_post` / `hybrid` を表現する。

### 5.7 `deep-read-shortlist`

- `editorial_score` 上位候補にだけ `twitter tweet` deep-read を当てる
- root id と root author を保持する
- root author reply を優先して取り込む
- recommendation noise を除外する
- deep-read で取得した root / reply / quote も必要に応じて `posts` と `post_observations` に取り込む

### 5.8 `judge-units`

- 上位 10 件前後だけを `gpt-5.4-nano` へ送る
- Batch API を優先する
- 出力は JSON 固定とする

### 5.9 `review-and-publish`

- reviewer が候補を確認する
- 必要なら angle、問い、本文を修正する
- 承認後にだけ `publish_jobs` を作る
- `twitter-cli post` は手動承認後の明示実行に限定する

### 5.10 `observe-feedback`

- reply / quote / like を保存する
- 良かった角度、荒れた角度、参加率の高い問いを分析する
- query と scoring の再調整に使う

## 6. データモデル

初期は 9 テーブルで運用する。

### 6.1 `query_profiles`

収集 query 定義。

初期値は [query_profiles.yml](/c:/WorldGossip/config/query_profiles.yml:1) と [collection_lanes.yml](/c:/WorldGossip/config/collection_lanes.yml:1) を seed として管理する。

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
- `editorial_modes`
- `country_pairs`
- `language_lane`
- `motif`
- `topic_pack`
- `risk_tier`
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

### 6.2 `collection_runs`

収集実行履歴。

- `id`
- `query_profile_id`
- `lane`
- `run_id`
- `started_at`
- `finished_at`
- `window_start`
- `window_end`
- `status`
- `item_count`
- `candidate_count`
- `deep_read_count`
- `ledger_path`
- `error_json`

### 6.3 `posts`

原投稿と軽い注釈を持つ中核テーブル。

- `id`
- `source_platform`
- `source_post_id`
- `canonical_url`
- `author_handle`
- `author_name`
- `posted_at`
- `collected_at`
- `first_seen_at`
- `last_seen_at`
- `body_raw`
- `body_norm`
- `lang`
- `language_confidence`
- `country_tags`
- `target_country_tags`
- `culture_tags`
- `tone_label`
- `interaction_style_label`
- `topic_flags`
- `safety_flags`
- `conversation_hooks_json`
- `engagement_json`
- `evidence_path`
- `is_active`

一意制約:

- `(source_platform, source_post_id)`

### 6.4 `post_embeddings`

- `post_id`
- `model_name`
- `dims`
- `embedding`
- `created_at`

一意制約:

- `(post_id, model_name)`

### 6.5 `post_observations`

継続収集時の観測履歴。

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
- `deep_read_root`
- `deep_read_reply`
- `deep_read_quote`
- `deep_read_noise`

### 6.6 `candidate_units`

- `id`
- `assembly_mode`
- `primary_post_id`
- `secondary_post_id`
- `retrieval_source`
- `semantic_score`
- `lexical_anchor_score`
- `self_contained_score`
- `cross_country_score`
- `freshness_score`
- `conversation_signal_score`
- `language_mix_bonus`
- `novelty_score`
- `safety_penalty`
- `retrieval_score`
- `editorial_score`
- `llm_keep`
- `llm_unit_type`
- `llm_safety`
- `llm_confidence`
- `llm_editorial_angle`
- `llm_reason_ja`
- `llm_reason_en`
- `status`
- `created_at`

`secondary_post_id` は `single_post` の場合 `NULL` を許容する。

一意制約:

- `single_post`: `(assembly_mode, primary_post_id)`
- `paired_post`: `(least(primary_post_id, secondary_post_id), greatest(primary_post_id, secondary_post_id))`

### 6.7 `review_items`

- `id`
- `candidate_unit_id`
- `review_status`
- `reviewer`
- `assembly_mode`
- `angle_label`
- `interaction_goal`
- `opening_question`
- `draft_body`
- `review_notes`
- `created_at`
- `updated_at`

### 6.8 `publish_jobs`

- `id`
- `review_item_id`
- `publish_status`
- `publish_channel`
- `draft_body`
- `opening_question`
- `attempted_at`
- `published_post_id`
- `failure_reason`

### 6.9 `published_post_metrics`

- `id`
- `publish_job_id`
- `captured_at`
- `reply_count`
- `quote_count`
- `like_count`
- `bookmark_count`
- `notes_json`

## 7. インデックス設計

### 7.1 `posts`

- `posted_at desc`
- `lang`
- `GIN(country_tags)`
- `GIN(target_country_tags)`
- `PGroonga(body_norm)`

### 7.2 `post_embeddings`

- HNSW cosine index on `embedding`

### 7.3 `post_observations`

- `post_id`
- `collection_run_id`
- `query_profile_id`
- `observed_at desc`
- `lane`
- `source_role`

### 7.4 `candidate_units`

- `status`
- `editorial_score desc`
- `created_at desc`

## 8. 候補探索設計

### 8.1 single-post candidate retrieval

基本条件:

- 直近 7 日を優先
- mixed-language reply や multi-country participation を加点する
- `post_observations` から freshness と velocity を補助特徴として取る
- `what do you call this` `where are you from and` `how do you say` のような roll-call / explanation / humor hook を拾う

### 8.2 paired-post retrieval

基本条件:

- 同一 post は除外
- 直近 7 日を優先
- 同一言語のみの候補は優先度を下げる
- 異なる国言及や target 国の噛み合いを優先する
- `post_observations` から freshness と velocity を補助特徴として取る

初期取得数:

- vector top-k: `80`
- lexical top-k: `30`

### 8.3 lexical retrieval

`PGroonga` では次のような字面アンカーを拾う。

- 国名
- 国民名
- 略称
- 文化語
- ミーム語
- 言い回し、俗語、wordplay anchor

### 8.4 retrieval score

```text
retrieval_score =
  0.55 * semantic_score
+ 0.20 * lexical_anchor_score
+ 0.15 * country_relation_score
+ 0.10 * freshness_score
```

### 8.5 editorial score

```text
editorial_score =
  0.70 * retrieval_score
+ 0.15 * conversation_signal_score
+ 0.10 * language_mix_bonus
+ 0.05 * novelty_score
- 0.10 * safety_penalty
```

`conversation_signal_score` には `replies` `quotes` `open question 性` `self-contained completion` に加え、`post_observations` から計算した `reply_velocity` と `quote_velocity` を補助特徴として入れる。

### 8.6 初期閾値

- `editorial_score >= 0.80`: judge 対象の強候補
- `0.72 <= editorial_score < 0.80`: judge 対象の保留候補
- `< 0.72`: 破棄

200 件レビュー後に再調整する。

## 9. LLM judge 設計

### 9.1 目的

`gpt-5.4-nano` は候補 editorial unit の `最終 keep / drop` と `review 補助説明` だけに使う。

### 9.2 入力

- primary post の原文
- secondary post の原文
- 言語情報
- 国タグ
- retrieval / editorial score
- assembly mode
- 必要に応じて deep-read で得た短い文脈

### 9.3 出力契約

```json
{
  "keep": true,
  "unit_type": "single_post",
  "safety": "low",
  "confidence": 0.86,
  "editorial_angle": "multi_country_roll_call",
  "reason_ja": "投稿単体で各国の参加を呼び込みやすく、会話の入口として完成している。",
  "reason_en": "The post works on its own because people from multiple countries can join the same conversation."
}
```

### 9.4 使わない用途

- 類似候補探索
- 全件翻訳
- 投稿本文の自動生成
- セーフティ単独判定

## 10. レビュー UI 設計

### 10.1 表示項目

- primary post の原文
- secondary post の原文
- `reason_ja` と `reason_en`
- 言語
- 国タグ
- tone / interaction style
- `editorial_score`
- lane と query profile
- 危険フラグ
- 参照元 URL
- deep-read の補足文脈

### 10.2 操作項目

- 承認
- 却下
- 保留
- angle 修正
- opening question 編集
- draft 本文編集
- 補足メモ記入

## 11. 投稿文生成

初期はテンプレートベースとする。  
生成材料は次を使う。

- `llm_editorial_angle`
- `reason_ja`
- `country_tags`
- `tone_label`
- `interaction_goal`
- `opening_question`

`single_post` の場合は、原文の自己完結性を壊さないことを優先し、無理に比較文脈を足さない。

制約:

- 勝ち負けを断定しない
- 文脈を壊す要約をしない
- ケンカを命令する文面にしない
- 危険方向に押し出さない

## 12. セーフティ設計

### 12.1 hard exclusion

次は即時除外とする。

- 戦争
- 政治
- 宗教
- 排外主義
- 深刻な差別
- 実被害を伴う事件
- 暴力煽動

### 12.2 soft risk

次は penalty と reviewer 必須対象にする。

- 日韓、中台など緊張度が高い国際話題
- 片方向の嘲笑に見える構図
- 文脈不足で誤解しやすい短文
- 返信欄が荒れやすい topic

### 12.3 最終判断

判定は 3 段階で行う。

1. 収集時 hard exclusion
2. candidate assembly 時 safety penalty
3. judge + reviewer 確認

## 13. 公開設計

### 13.1 原則

完全自動投稿はしない。

### 13.2 フロー

1. reviewer が `review_items` を承認
2. `publish_jobs` を作成
3. `twitter-cli post` を実行
4. 成功時は `published_post_id` を保存
5. 失敗時は `manual_fallback_required` にする

### 13.3 フォールバック

- post 失敗時は draft を UI に残す
- reviewer が手動で投稿できる状態を維持する

## 14. 運用設計

### 14.1 ログ

保存するもの:

- evidence ledger
- job 実行ログ
- post observation 履歴
- candidate 生成理由
- reviewer 履歴
- publish 成否
- metrics snapshot

### 14.2 冪等性

- `posts` は `(source_platform, source_post_id)` で upsert
- `post_embeddings` は `(post_id, model_name)` で upsert
- `post_observations` は `(post_id, collection_run_id, source_role, result_rank)` を重複保存しない
- `candidate_units` は `assembly_mode` に応じて unique 制約を切り替える
- `publish_jobs` は active 状態の重複を作らない

### 14.3 障害時

- collect 失敗: 次回再試行
- embed 失敗: 対象 post を pending 化
- judge 失敗: 候補を pending に戻す
- publish 失敗: manual fallback へ送る
- observe 失敗: 次回観測へ回す

## 15. 実装フェーズ

### Phase 1

- Supabase schema
- `posts`
- `post_observations`
- `post_embeddings`
- `candidate_units`
- lane scheduler
- discovery / shortlist gate
- OpenAI embeddings 接続
- PGroonga 併用 retrieval

### Phase 2

- `gpt-5.4-nano` judge
- review UI
- `review_items`
- `publish_jobs`

### Phase 3

- metrics 収集
- scoring 再調整
- query family の改善

### Phase 4

- Supabase Cron 導入
- card 画像生成
- 投稿テンプレ改善

## 16. 最終判断

WorldGossip の実装は、`FastAPI を運用中枢に置き、Supabase を検索と保存の基盤にし、OpenAI を embeddings と最終 judge に限定利用する構成` で確定する。

この構成なら、次の 3 点を両立できる。

- 会話を起こす編集品質
- 少額課金で得られる多言語検索精度
- human-in-the-loop による安全性
