# WorldGossip Agent Reach DB 保存設計 2026-04-15

作成日: 2026-04-15 JST  
対象: Agent Reach の実測 JSON を前提に、WorldGossip の DB 保存方式を決める

## 1. 目的

今回の目的は次の 2 つである。

- Agent Reach で実際に最終取得されるデータ構造を確認する
- その構造を `Python 3.12 + FastAPI + Supabase Postgres` の WorldGossip 実装へ、無理なく・冪等に・後から検証可能な形で保存する

この文書は既存の [worldgossip-technical-design.md](/c:/WorldGossip/docs/worldgossip-technical-design.md) と [worldgossip-collection-design.md](/c:/WorldGossip/docs/worldgossip-collection-design.md) を、実測 JSON に合わせて具体化する補助設計である。

## 2. 今回確認した実測 artifact

2026-04-15 JST に次の artifact を取得した。

- search sample: [search-food.json](/c:/WorldGossip/.agent-reach/search-food.json)
- tweet deep-read sample: [tweet-rawchicken.json](/c:/WorldGossip/.agent-reach/tweet-rawchicken.json)
- tweet deep-read full raw sample: [tweet-rawchicken-full.json](/c:/WorldGossip/.agent-reach/tweet-rawchicken-full.json)
- merged evidence ledger: [evidence.jsonl](/c:/WorldGossip/.agent-reach/evidence.jsonl)

確認時の事実:

- `agent-reach doctor --json --probe` では `twitter search` と `twitter user` が live success だった
- `twitter tweet` は doctor 未 probe のままだが、実地 collect は成功した
- ledger summarize では `records=2`, `operation_counts={search:1,tweet:1}`, `intent=query_id=source_role` は欠損なしだった

## 3. 実測した最終データ構造

### 3.1 `CollectionResult`

Agent Reach の collect 結果は、実測でも schema 定義通り次の top-level を持っていた。

```json
{
  "schema_version": "2026-04-10",
  "agent_reach_version": "1.13.0",
  "ok": true,
  "channel": "twitter",
  "operation": "search",
  "items": [],
  "raw": {},
  "meta": {},
  "error": null
}
```

重要なのは次の点である。

- `items[]` は backend 差を吸収した normalized item 配列
- `raw` は backend 生 payload か、その縮約情報
- `meta` は input, limit, duration, count, diagnostics など run 側の補助情報
- `error` は成功時 `null`、失敗時は `code/category/retryable` を持つ

### 3.2 `NormalizedItem`

今回の Twitter 実測では、各 item はほぼ次の形だった。

```json
{
  "id": "2041126787690934455",
  "kind": "post",
  "title": "...",
  "url": "https://x.com/...",
  "text": "...",
  "author": "skindie___",
  "published_at": "2026-04-06T12:12:03Z",
  "source": "twitter",
  "canonical_url": "https://x.com/...",
  "source_item_id": "2041126787690934455",
  "engagement": {
    "likes": 277,
    "retweets": 45,
    "replies": 322,
    "quotes": 38,
    "views": 35205,
    "bookmarks": 13
  },
  "media_references": [],
  "identifiers": {
    "domain": "x.com"
  },
  "extras": {
    "author_name": "Skindie",
    "verified": true,
    "metrics": { "...": 0 },
    "urls": [],
    "media": [],
    "media_references": [],
    "lang": "en",
    "is_retweet": false,
    "retweeted_by": null,
    "quoted_tweet": null,
    "score": null,
    "engagement_complete": true,
    "media_complete": true
  }
}
```

実測で確認できた保存上の重要点:

- `engagement` は item 直下に正規化済みで入る
- `extras.metrics` は `engagement` と重複気味なので DB では二重保存不要
- `extras.lang`, `extras.verified`, `extras.quoted_tweet`, `media_references` は保存価値が高い
- search では `engagement_complete=false` `media_complete=false` が返ることがある
- tweet deep-read では `engagement_complete=true` `media_complete=true` だった

### 3.3 `raw`

今回の実測では `raw` に 2 形態あった。

`raw_mode=minimal`:

```json
{
  "raw_mode": "minimal",
  "type": "dict",
  "approx_bytes": 6075,
  "keys": ["data", "ok", "schema_version"]
}
```

`raw_mode=full`:

```json
{
  "schema_version": "2026-04-10",
  "ok": true,
  "data": [
    {
      "id": "...",
      "text": "...",
      "author": {
        "id": "...",
        "name": "...",
        "screenName": "...",
        "verified": true
      },
      "metrics": { "...": 0 },
      "createdAtISO": "...",
      "media": [],
      "urls": [],
      "lang": "en"
    }
  ]
}
```

実測上の判断:

- `raw_mode=full` は author id などを拾えるが、WorldGossip MVP に必須な thread role 情報は見えなかった
- つまり `tweet` deep-read の root / reply / quote / noise を、raw だけで完全確定するのは難しい
- したがって raw は forensic / debug 用に寄せ、主保存面は normalized item を使う方がよい

### 3.4 ledger record

DB ingest の正本として一番扱いやすかったのは、単発 JSON ではなく evidence ledger の 1 行だった。

```json
{
  "schema_version": "2026-04-10",
  "record_type": "collection_result",
  "run_id": "wg-structure-20260415-search-food",
  "created_at": "2026-04-14T16:47:16Z",
  "channel": "twitter",
  "operation": "search",
  "input": "...",
  "ok": true,
  "count": 3,
  "item_ids": ["..."],
  "urls": ["..."],
  "error_code": null,
  "intent": "db_structure_probe",
  "query_id": "en_jp_convenience_snack_question_live",
  "source_role": "search_result",
  "result": { "CollectionResult": "..." }
}
```

この wrapper の利点:

- `run_id`, `intent`, `query_id`, `source_role` が result 本体と一緒に残る
- `item_ids`, `urls`, `count` が top-level にあるので summary が取りやすい
- shard でも merged ledger でも 1 行 1 record で stream ingest しやすい

## 4. 実測から見えた設計上の注意点

### 4.1 `tweet` sample は root 以外の item が混入する

今回の `twitter tweet` deep-read では、root tweet と関連 reply 以外に無関係な item が混ざった。

したがって:

- `tweet` の返り値を thread 取得面として使わない
- `tweet` は root post の engagement refresh 用に限定する
- `requested root id` と一致しない item はすべて破棄する

### 4.2 per-item role 分類は不要にする

今回の sample では、normalized item にも raw item にも `reply` `quote` `noise` の確定ラベルはなかった。

したがって最適設計は:

- source post 候補は root post のみを保存対象にする
- reply、quote、thread item は保存対象から外す
- `source_role` は run-level で `search_result` と `root_refresh` の 2 種で足りる

### 4.3 `search` と `tweet` では completeness が違う

実測では:

- `search`: `engagement_complete=false`, `media_complete=false`
- `tweet`: `engagement_complete=true`, `media_complete=true`

よって DB では:

- `posts` に保存する最新状態は、単純な last write wins ではなく completeness を考慮して merge する
- `post_observations` に観測時点の completeness を保持する

### 4.4 `twitter search` のままでは DB ノイズが多い

2026-04-15 JST の root-only noise check では、代表 5 query / 40 item に対して次が確認できた。

- `reply_like`: `8 / 40`
- `link_stub`: `10 / 40`
- `weak_conversation` (`replies < 5` かつ `quotes < 2`): `22 / 40`
- `low_views` (`views < 5000`): `19 / 40`

また、`-filter:replies` を付けた再実測でも reply-like post が残った。

### 4.5 これは host 側の問題か、Agent Reach 側の問題か

整理すると、主因は `host 側の候補採用条件` と `X/Twitter search 面の性質` であり、`Agent Reach` は主犯ではない。

確認できたこと:

- `Agent Reach` の `twitter search` は `twitter-cli search` を呼び、その `raw.data` をほぼそのまま `NormalizedItem` に写している
- `CollectionResult.raw` の時点で reply-like / brand / low-quality item がすでに含まれている
- 同一 query を 2026-04-15 JST に `twitter search --json` と `agent-reach collect --channel twitter --operation search --json` で別々に叩いても、両方で同種のノイズが出た
- 2 回の呼び出しで返る ID 群自体も揺れたため、検索面は deterministic ではない

一方で、`Agent Reach` / `twitter-cli` 側には改善余地がある。

- `search` item に `is_reply` `in_reply_to_status_id` `conversation_id` のような root 判定メタデータが露出していない
- そのため current host は `@` 始まりなどの heuristic で coarse filtering するしかない

したがって fork 判断は次のように置く。

- `DB ノイズを防ぐ` だけなら、まず host 側 pre-DB gate を強化する
- `reply/root 判定をより確実にしたい` なら、`Agent Reach` か `twitter-cli` を project に取り込み、reply 関連 metadata を追加露出する価値がある
- `search quality 自体を根本改善したい` なら、fork だけでは不十分で、query lane と host ranking の再設計が必要

したがって:

- search 結果はそのまま DB に流さない
- ingest 前に pre-DB noise gate を必須にする
- reply 除外は query だけに頼らず host 側で必ず再判定する

## 5. 最適な保存方針

結論として、WorldGossip では次の 2 層保存が最適である。

### 5.1 第 1 層: artifact 保存

`CollectionResult` と ledger は、DB 本体ではなく object storage に immutable artifact として保存する。

推奨:

- 開発: `.agent-reach/`
- 本番: `Supabase Storage` の private bucket

推奨パス:

```text
agent-reach-evidence/
  worldgossip/
    2026/04/15/<run_id>/
      shards/*.jsonl
      evidence.jsonl.gz
      manifest.json
```

ここに保存するもの:

- shard JSONL
- merged `evidence.jsonl`
- 必要なら debug 用の full raw JSON
- bytes, sha256, schema version を持つ manifest

理由:

- 収集結果は run ごとに append-only で、監査・再現・再取込に向く
- 同じ post が複数 run に出るので、Postgres に full JSON を毎回入れると膨らみやすい
- Supabase Storage は現行スタックのままで運用できる

### 5.2 第 2 層: relational projection 保存

検索・順位付け・review UI・再利用のために必要な部分だけを Postgres へ正規化して入れる。

保存先の原則:

- canonical entity は `posts`
- run ごとの観測は `post_observations`
- run summary は `collection_runs`
- full artifact は Storage の path だけ DB に持つ

この projection に入れる前に、pre-DB noise gate を通す。

## 6. 既存 schema への推奨調整

### 6.1 `collection_runs`

既存設計に加えて次を足すのがよい。

- `agent_reach_version`
- `result_schema_version`
- `artifact_path`
- `artifact_sha256`
- `artifact_bytes`
- `result_meta_json`

`result_meta_json` に入れる候補:

- `duration_ms`
- `requested_limit`
- `returned_count`
- `diagnostics`
- `raw_mode`
- `item_text_mode`

### 6.2 `posts`

既存設計に加えて次を足すのがよい。

- `author_verified`
- `media_refs_json`
- `source_meta_json`

`source_meta_json` には bounded なものだけを入れる。

推奨内容:

- `extras.lang`
- `extras.is_retweet`
- `extras.retweeted_by`
- `extras.quoted_tweet`
- `extras.urls`
- completeness の best-known state

逆に入れないもの:

- raw 全体
- `extras.metrics` の完全複製

### 6.3 `post_observations`

既存の `raw_item_path` は曖昧なので、次の形へ寄せるのがよい。

- `artifact_path`
- `record_index`
- `item_index`
- `engagement_complete`
- `media_complete`

`source_role` は初期段階では次に寄せる。

- `search_result`
- `root_refresh`

この方が root-only 方針と実測データ構造の両方に合う。

## 7. `CollectionResult` から DB への写像

### 7.1 `collection_runs`

ledger record の次を run へ入れる。

- `run_id`
- `query_id -> query_profile_id`
- `source_role` は run-level の起動種別として保持
- `channel`
- `operation`
- `count`
- `ok`
- `error_code`
- `created_at`
- `result.meta`
- `artifact_path`

### 7.2 `posts`

`result.items[]` の次を upsert する。

- `source_platform = item.source`
- `source_post_id = item.source_item_id or item.id`
- `canonical_url = item.canonical_url`
- `author_handle = item.author`
- `author_name = extras.author_name`
- `author_verified = extras.verified`
- `posted_at = item.published_at`
- `body_raw = item.text`
- `lang = extras.lang`
- `engagement_json = item.engagement`
- `media_refs_json = item.media_references`
- `source_meta_json = bounded extras subset`

### 7.3 `post_observations`

run 依存のものは observation に入れる。

- `collection_run_id`
- `query_profile_id`
- `lane`
- `source_role`
- `observed_at = record.created_at`
- `result_rank = item の配列順`
- `engagement_json = item.engagement`
- `artifact_path`
- `record_index`
- `item_index`
- `engagement_complete`
- `media_complete`

## 8. 推奨 merge ルール

`posts` upsert では次の merge を推奨する。

- `first_seen_at = least(existing, observed_at)`
- `last_seen_at = greatest(existing, observed_at)`
- `body_raw` は `NULL -> 新値`、または `新値の方が長い` 場合だけ更新
- `engagement_json` は `observed_at` が新しい方を採用
- `author_name`, `author_verified`, `media_refs_json`, `quoted_tweet` は `NULL/空 -> 新値` を優先
- completeness は `false -> true` には更新するが、`true -> false` には戻さない

## 8.1 pre-DB noise gate

`posts` と `post_observations` に入れる前に、少なくとも次を除外する。

- `@` 始まりの reply-like post
- `詳細はこちら`、URL 主体、極端に短い本文の link stub
- 外部リンク主体で、質問・比較・roll-call・説明導線のない news / brand broadcast post
- `views < 5000` の low-traction post
- 正規化後に country anchor と cross-country seed の両方が弱い post

## 9. 実装フロー

### 9.1 collect

推奨コマンド方針:

```text
agent-reach collect --json --save-dir <run shards dir> \
  --run-id <run_id> \
  --intent <intent> \
  --query-id <query_profile_id> \
  --source-role <search_result|root_refresh>
```

Twitter-only の WorldGossip では次を推奨する。

- `search`: `raw-mode=minimal`, `item-text-mode=full`
- `tweet`: `raw-mode=minimal`, `item-text-mode=full`, ただし root URL にだけ使う
- `raw-mode=full` は debug と contract 変化確認に限定

理由:

- X post 本文は比較的短く、`item-text-mode=full` のコスト増が小さい
- 一方で raw full は root-only 運用に必須ではないため、常用する意味が薄い

### 9.2 merge / validate

run 完了後:

1. `ledger merge`
2. `ledger summarize`
3. 必要なら `ledger validate`
4. merged ledger を gzip して Storage へ upload

### 9.3 ingest

ingestor は単発 JSON ではなく ledger record を読む。

理由:

- run metadata が一緒にある
- 1 行ずつ stream 処理できる
- 再取込が簡単

擬似フロー:

```text
for record in evidence.jsonl:
  upsert collection_runs
  if operation == tweet:
    keep only item.id == requested_root_id
  for each retained item in record.result.items:
    upsert posts
    insert post_observations
```

## 10. 最終判断

WorldGossip にとって最適なのは、`Agent Reach の merged ledger を ingest の正本にし、artifact は Supabase Storage、検索用 projection は Supabase Postgres に分離する方式` である。

この方式の利点は明確である。

- Agent Reach の contract 変更に追従しやすい
- 同一 post の再観測を `posts + post_observations` で自然に吸収できる
- raw の肥大化を Postgres へ持ち込まない
- run 単位の監査、再計算、再取込がしやすい
- 既存の `FastAPI + Supabase + pgvector + PGroonga` 設計と衝突しない

特に重要なのは次の 3 点である。

- DB ingest の入力は `CollectionResult` 単体ではなく ledger record にする
- `tweet` は root post refresh 用に限定し、root 以外の item は保存しない
- raw は artifact に残し、DB には bounded projection だけを入れる
