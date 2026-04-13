# WorldGossip 最適設計と採用判断

作成日: 2026-04-14 JST  
ステータス: Final  
役割: この文書は WorldGossip の最終採用構成を定義する意思決定文書である。企画思想は `project-concept.md`、実装仕様は `worldgossip-technical-design.md` を参照する。

## 1. 最終結論

WorldGossip の最適解は、`収集と編集の運用設計は現行案を継承しつつ、検索と判定の中核だけを少額課金で強化する` ハイブリッド構成である。

最終採用構成は次の通り。

- 収集: `Agent Reach` の `twitter search` と `twitter tweet`
- アプリ: `Python 3.12` + `FastAPI`
- DB: `Supabase Postgres`
- semantic retrieval: `pgvector`
- lexical retrieval: `PGroonga`
- 言語判定: `lingua-py`
- embeddings: OpenAI `text-embedding-3-large` with `dimensions=1024`
- final judge: OpenAI `gpt-5.4-nano` with Batch API
- review UI: FastAPI 内蔵
- publish: `twitter-cli` with human approval

## 2. なぜこの形が最適か

WorldGossip の価値は、単なる多言語意味検索ではなく、次の一連の流れにある。

- 会話が起きそうな投稿を集める
- 文脈を壊さずに組み合わせる
- 温度感と危険度を調整する
- 問いかけ付きで編集する
- 投稿後の反応から次回を改善する

このため、`無料ローカル実行だけに寄せた構成` では検索品質が弱くなりやすく、`検索だけ最適化した構成` では運用の本質を取りこぼす。  
必要なのは、`編集ワークフローを残したまま、検索と判定だけを強くする構成` である。

## 3. 何を継承し、何を置き換えるか

### 3.1 継承するもの

- `Agent Reach` による discovery と deep-read の 2 段収集
- query profile と evidence ledger
- `FastAPI` ベースの review UI
- human-in-the-loop の公開フロー
- reply / quote / like を次回スコアに返す運用

### 3.2 置き換えるもの

- 埋め込み主系を `sentence-transformers` から OpenAI embeddings に置き換える
- `PostgreSQL + pgvector` 単体構成を `Supabase + pgvector + PGroonga` に置き換える
- 翻訳保存中心の設計を、`レビュー補助グロスのみ` の設計に置き換える
- `Detoxify` 中心の safety 補助を、`ルール + judge + reviewer` の 3 段階に置き換える

## 4. 採用するもの

### 4.1 コア採用

- `Agent Reach`
- `FastAPI`
- `Supabase Postgres`
- `pgvector`
- `PGroonga`
- `lingua-py`
- `text-embedding-3-large` with `dimensions=1024`
- `gpt-5.4-nano`
- `twitter-cli`

### 4.2 補助採用

- `Windows Task Scheduler` / `cron`
- `Supabase Cron`
  - 初期は必須にしない
  - 後から app webhook 起動用に追加できる

### 4.3 採用するが主役にしないもの

- `sentence-transformers`
  - 比較評価用または fallback 用にだけ残す

## 5. 採用しないもの

初期のコア構成からは次を外す。

- `argos-translate`
- `CTranslate2`
- `Detoxify`
- `Qdrant`
- `n8n`
- `Postiz`
- Supabase Edge Functions 主導の多言語処理オーケストレーション

## 6. 外した理由

### 6.1 `sentence-transformers` を主系にしない理由

無料で魅力はあるが、WorldGossip のように `短文` `多言語` `文化差` `軽いニュアンス差` が重要な用途では、初期品質で OpenAI embeddings の優位が出やすい。

### 6.2 翻訳全件保存をしない理由

検索の主軸を翻訳に置くと、banter や温度差の角が丸まりやすい。  
WorldGossip は原文の空気感が重要なため、翻訳は review 補助に限定する。

### 6.3 `Detoxify` を外す理由

多言語の軽い banter と本気の敵意をきれいに分けるには弱く、誤検出時の運用コストが高い。  
WorldGossip では `topic exclusion + risky pattern + reviewer judgement` の方が筋が良い。

### 6.4 Edge Functions 主導にしない理由

`Agent Reach` と `twitter-cli` は Python 側のジョブに載せる方が自然である。  
Supabase 側に責務を寄せすぎると、収集、判定、公開の責務が分断される。

## 7. 最終アーキテクチャ

```text
Agent Reach
  -> FastAPI worker
      -> normalize and tag
      -> embed
      -> pair
      -> judge
      -> review queue
      -> publish trigger
  -> Supabase Postgres
      -> posts
      -> post_embeddings
      -> candidate_pairs
      -> review_items
      -> publish_jobs
      -> published_post_metrics
  -> OpenAI API
      -> text-embedding-3-large (1024 dims)
      -> gpt-5.4-nano Batch
  -> twitter-cli
```

## 8. 設計原則

### 8.1 LLM に検索させない

検索は `embeddings + vector similarity + lexical anchor` で行い、LLM は最終判定に限定する。

### 8.2 翻訳を検索の主軸にしない

原文を主役にし、レビュー時だけ短い補助グロスを作る。

### 8.3 収集は広く、判定は狭く

- `search` で広く拾う
- shortlist 後に `tweet` deep-read
- top 候補だけ judge

### 8.4 公開前に必ず人間が見る

WorldGossip の価値は微妙な温度調整にあるため、完全自動投稿は採らない。

### 8.5 provenance を捨てない

query profile、run id、evidence path、review 履歴を残し、改善サイクルに使う。

## 9. 収集戦略

### 9.1 初期スコープ

- source は X/Twitter に限定する
- 主戦場は `ja` と `en`
- `ko` `zh` `es` `fr` は補助レーンとする
- 国軸は `日本` を中心に始める

### 9.2 強い query family

- 日本人が海外に素朴な質問を投げる型
- 英語圏が日本について open question を投げる型
- 食、菓子、価格差、生活用品の比較型
- 日仏、日台、日韓の好意 + 温度差型
- 自動翻訳越しの多国籍交流型

## 10. 検索戦略

### 10.1 semantic retrieval

- OpenAI embeddings を生成
- `pgvector` で近傍検索
- 時間窓は直近 7 日を優先

### 10.2 lexical retrieval

- `PGroonga` で国名、デモニム、文化語、ネット語を拾う
- semantic だけでは落ちやすい字面アンカーを補う

### 10.3 final judge

`gpt-5.4-nano` は次だけを返す。

- `keep`
- `match_type`
- `safety`
- `confidence`
- `editorial_angle`
- `reason_ja`
- `reason_en`

## 11. データ設計の方針

初期は次の 8 テーブルで十分である。

- `query_profiles`
- `collection_runs`
- `posts`
- `post_embeddings`
- `candidate_pairs`
- `review_items`
- `publish_jobs`
- `published_post_metrics`

`source_posts`、`post_annotations`、`post_translations` のような細分化は初期には過剰であり、`posts` へ集約した方が運用と実装が軽い。

## 12. 投稿生成の方針

投稿文は初期はテンプレートベースでよい。  
LLM に本文生成まで任せると、WorldGossip に必要な `軽い熱量` と `危険回避` の両立が難しくなる。

LLM は `候補判定と review 補助説明` までに限定し、本文は reviewer が最終調整する。

## 13. コスト方針

### 13.1 固定コスト

- `Supabase Pro` を前提とする

### 13.2 変動コスト

- embeddings
- judge batch

### 13.3 抑制ルール

- embeddings は新規 post にだけ打つ
- judge は top 10 前後にだけかける
- deep-read は shortlist 後にだけ回す
- 翻訳全件保存をやめる

## 14. リスクと対策

### 14.1 X 側仕様変動

- `twitter-cli` は常に manual gate 前提で使う
- 失敗時は UI に draft を残し、手動投稿へフォールバックする

### 14.2 deep-read のノイズ混入

- root id と root author を保持する
- root author reply を優先する
- recommendation noise を除外する

### 14.3 日韓や政治史への接続

- hard exclusion と safety penalty を強く掛ける
- reviewer 必須で扱う

## 15. 最終判断

WorldGossip に最適なのは、`現行の編集思想を維持しつつ、検索と判定だけを少額課金で強化する構成` である。

要点は次の 3 つである。

- 収集と編集フローは現行案を土台にする
- 検索品質は `Supabase + pgvector + PGroonga + OpenAI embeddings` に寄せる
- LLM は `judge と review 補助` にだけ使う

これにより、無料構成の弱点だった `多言語検索精度` と `レビュー前ノイズ` を大きく改善しながら、  
WorldGossip の本質である `会話を起こす編集プロジェクト` を壊さずに前進できる。

## 16. 参考リンク

- OpenAI `text-embedding-3-large`: https://developers.openai.com/api/docs/models/text-embedding-3-large
- OpenAI embeddings guide: https://platform.openai.com/docs/guides/embeddings
- OpenAI Batch API: https://platform.openai.com/docs/guides/batch
- OpenAI pricing: https://openai.com/api/pricing
- Supabase `pgvector`: https://supabase.com/docs/guides/database/extensions/pgvector
- Supabase vector indexes: https://supabase.com/docs/guides/ai/vector-indexes
- Supabase `PGroonga`: https://supabase.com/docs/guides/database/extensions/pgroonga
- Supabase scheduling: https://supabase.com/docs/guides/functions/schedule-functions
- Supabase billing: https://supabase.com/docs/guides/platform/billing-on-supabase
