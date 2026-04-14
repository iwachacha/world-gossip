# WorldGossip Agent Reach Coexistence Implementation

Date: 2026-04-15 JST

## Conclusion

WorldGossip should keep using `agent-reach` for discovery and evidence capture.
Precision improvements should live inside this repository as a host-owned Twitter/X filter layer.

This is the intended shape of coexistence:

`agent-reach twitter search` -> `WorldGossip Twitter precision layer` -> `DB ingest`

## Why coexistence is the right shape

`agent-reach` is intentionally thin.
That is good for:

- stable collection entrypoints
- evidence ledgers
- transport-level diagnostics
- reusable research tooling

It is not the right place to own WorldGossip-specific policy such as:

- root-post-only gating
- low-traction rejection
- news / brand broadcast rejection
- cross-country conversation-fit filtering

## In-project implementation added now

- policy config: [twitter_precision_policy.yml](/c:/WorldGossip/config/twitter_precision_policy.yml)
- package entrypoint: [__init__.py](/c:/WorldGossip/src/worldgossip_twitter/__init__.py)
- candidate model: [models.py](/c:/WorldGossip/src/worldgossip_twitter/models.py)
- policy loader: [policy.py](/c:/WorldGossip/src/worldgossip_twitter/policy.py)
- filter logic: [filters.py](/c:/WorldGossip/src/worldgossip_twitter/filters.py)
- Agent Reach bridge: [agent_reach_bridge.py](/c:/WorldGossip/src/worldgossip_twitter/agent_reach_bridge.py)
- focused tests: [test_worldgossip_twitter_filters.py](/c:/WorldGossip/tests/test_worldgossip_twitter_filters.py)

## Ownership boundary

`agent-reach` continues to own:

- search execution
- normalized collection envelopes
- raw artifact retention
- ledger append / merge / summarize

WorldGossip now owns:

- pre-DB noise gate
- project thresholds
- explicit keep/drop reasons
- future root/reply metadata use when upstream exposes it

## Immediate next step

The next implementation slice should read actual `agent-reach` search output from the runtime job,
convert it through `agent_reach_bridge.py`,
and run the current gate automatically before `posts` and `post_observations` are persisted.
