# WorldGossip Precision Eval 2026-04-15 Batch2

Date: 2026-04-15 JST

## Run

- command:
  - `uv run python -m worldgossip_twitter.agent_reach_eval_runner --output-dir .agent-reach/precision-eval-2026-04-15-batch2 --max-profiles 22 --limit-cap 10 --until 2026-04-15`
- collection mode:
  - `twitter search`
  - `item-text-mode=snippet`
  - `item-text-max-chars=560`
  - `raw-mode=minimal`
- policy inputs:
  - `config/twitter_precision_policy.yml`
  - `config/query_profiles.yml`

## Result

- `22` records
- `172` posts seen
- `169` unique post ids after dedupe
- `4` kept
- `165` dropped
- keep rate: `0.0237`

## Key Finding

The current host-side precision layer is now strong enough to protect DB ingest during broad collection.

Validated layers:

1. Query shaping removes part of the drift before collection.
2. Generic pre-DB gate removes reply-like roots, weak-conversation roots, link stubs, and broadcast/travel noise.
3. Profile-aware thresholds remove posts that are concept-shaped but still too small or too shallow for WorldGossip.
4. Post-id dedupe prevents the same root post from being counted or ingested multiple times across multiple query profiles.

## Main Drop Reasons

- `below_profile_gate: 145`
- `low_views: 118`
- `weak_conversation: 118`
- `missing_cross_country_seed: 128`
- `reply_like: 51`
- `broadcast_like: 7`
- `travel_promo: 2`
- `link_stub: 1`

Interpretation:

- The bulk of the remaining search surface is still low-traction or weak-conversation noise.
- The precision problem is no longer "reply contamination gets into DB."
- The remaining precision work is mainly about recall on good roots, especially in frontier and local-language lanes.

## Kept Set Review

The surviving kept examples were:

- explicit bilateral appreciation prompt with strong traction
- Japanese-origin wordplay / translation observation with large public discussion
- Japanese-origin US-vs-Japan daily-life analysis with strong engagement
- Japanese-origin cross-country invitation about talking across national boundaries

One borderline survivor from the previous run, a personal `move to Japan` advice post, is now dropped by the new travel / relocation guard.

## What Changed

- search snippets increased from `280` to `560` characters
  - reason: `280` chars truncated some valid question tails and caused false `missing_cross_country_seed`
- added profile-aware gate from `query_profiles.yml`
  - `min_views`
  - `min_replies`
  - `min_quotes`
- added concept guards for:
  - `compliment your culture` style identity-validation prompts
  - travel / destination / relocation planning prompts
- added local-language anchor / seed vocabulary for:
  - Portuguese
  - Spanish
  - French

## Operational Decision

Bulk collection is now safe to run under these rules:

- save raw Agent Reach artifacts first
- bridge to `SearchPost`
- dedupe by `post_id`
- apply generic pre-DB gate
- apply profile-aware thresholds
- only then persist to DB

The current disabled profiles should remain disabled until rewritten:

- `en_europe_affinity_prompt_live`
- `en_latam_affinity_prompt_live`
- `en_translation_bridge_live`

## Remaining Gaps

- frontier English profiles still produce many valid-looking questions with insufficient views
- PT / ES / FR lanes are no longer failing on missing anchors, but still need stronger query phrasing to find high-traction roots
- some proven food / convenience prompts still surface many sub-20k roots, so recall exists but shortlist quality stays low

## Next Step

Focus the next iteration on recall, not safety:

- strengthen high-traction food-question query shapes
- add more local-language question lexicon for PT / ES / FR
- test object-anchored infrastructure / price prompts against the same profile-aware gate
