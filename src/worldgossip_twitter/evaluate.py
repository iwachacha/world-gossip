"""Evaluate Agent Reach Twitter collection output against the WorldGossip gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from . import apply_pre_db_noise_gate, iter_posts_from_ledger_record, load_precision_policy
from .models import SearchPost
from .profiles import QueryProfile, load_query_profiles


@dataclass
class CandidateAggregate:
    """Deduped post plus the set of query profiles that surfaced it."""

    post: SearchPost
    query_ids: set[str] = field(default_factory=set)


def _best_profile_gate(post: SearchPost, profiles: dict[str, QueryProfile], query_ids: set[str]) -> tuple[bool, str | None]:
    matched_profiles = [profiles[query_id] for query_id in sorted(query_ids) if query_id in profiles]
    if not matched_profiles:
        return True, None

    for profile in matched_profiles:
        gate = profile.gate_policy
        if (
            post.metrics.views >= gate.min_views
            and post.metrics.replies >= gate.min_replies
            and post.metrics.quotes >= gate.min_quotes
        ):
            return True, None

    return False, "below_profile_gate"


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def evaluate_ledger(
    ledger_path: Path,
    policy_path: Path,
    profile_path: Path = Path("config/query_profiles.yml"),
) -> dict:
    """Return a machine-readable evaluation summary for one ledger."""

    policy = load_precision_policy(policy_path)
    profiles = load_query_profiles(profile_path)
    records = _load_jsonl(ledger_path)

    total_posts = 0
    kept_posts = 0
    drop_reasons: Counter[str] = Counter()
    by_query: dict[str, dict[str, object]] = defaultdict(lambda: {"seen": 0, "kept": 0, "drop_reasons": Counter()})
    kept_examples: list[dict[str, object]] = []
    dropped_examples: list[dict[str, object]] = []
    deduped_candidates: dict[str, CandidateAggregate] = {}

    for record in records:
        for post in iter_posts_from_ledger_record(record):
            total_posts += 1
            query_id = post.query_id or "unknown"
            query_bucket = by_query[query_id]
            query_bucket["seen"] = int(query_bucket["seen"]) + 1
            aggregate = deduped_candidates.setdefault(post.id, CandidateAggregate(post=post))
            aggregate.query_ids.add(query_id)

    for aggregate in deduped_candidates.values():
        post = aggregate.post
        matched_query_ids = sorted(aggregate.query_ids)
        decision = apply_pre_db_noise_gate(post, policy)
        profile_keep, profile_reason = _best_profile_gate(post, profiles, aggregate.query_ids)
        reasons = list(decision.reasons)
        if not profile_keep and profile_reason:
            reasons.append(profile_reason)

        if not reasons:
            kept_posts += 1
            for query_id in matched_query_ids:
                by_query[query_id]["kept"] = int(by_query[query_id]["kept"]) + 1
            if len(kept_examples) < 12:
                kept_examples.append(
                    {
                        "query_ids": matched_query_ids,
                        "post_id": post.id,
                        "author": post.author_screen_name,
                        "views": post.metrics.views,
                        "replies": post.metrics.replies,
                        "quotes": post.metrics.quotes,
                        "text": post.text[:280],
                    }
                )
            continue

        for reason in reasons:
            drop_reasons[reason] += 1
        for query_id in matched_query_ids:
            query_bucket = by_query[query_id]
            for reason in reasons:
                query_bucket["drop_reasons"][reason] += 1
        if len(dropped_examples) < 20:
            dropped_examples.append(
                {
                    "query_ids": matched_query_ids,
                    "post_id": post.id,
                    "author": post.author_screen_name,
                    "views": post.metrics.views,
                    "replies": post.metrics.replies,
                    "quotes": post.metrics.quotes,
                    "reasons": reasons,
                    "text": post.text[:280],
                }
            )

    serializable_queries: dict[str, dict[str, object]] = {}
    for query_id, bucket in by_query.items():
        serializable_queries[query_id] = {
            "seen": bucket["seen"],
            "kept": bucket["kept"],
            "keep_rate": round((bucket["kept"] / bucket["seen"]), 4) if bucket["seen"] else 0.0,
            "drop_reasons": dict(bucket["drop_reasons"]),
        }

    return {
        "ledger_path": str(ledger_path),
        "policy_path": str(policy_path),
        "profile_path": str(profile_path),
        "total_records": len(records),
        "total_posts_seen": total_posts,
        "unique_posts_seen": len(deduped_candidates),
        "kept_posts": kept_posts,
        "dropped_posts": len(deduped_candidates) - kept_posts,
        "keep_rate": round((kept_posts / len(deduped_candidates)), 4) if deduped_candidates else 0.0,
        "drop_reasons": dict(drop_reasons),
        "queries": serializable_queries,
        "kept_examples": kept_examples,
        "dropped_examples": dropped_examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Agent Reach Twitter ledger with the WorldGossip gate.")
    parser.add_argument("--ledger", required=True, help="Path to merged Agent Reach evidence JSONL")
    parser.add_argument(
        "--policy",
        default="config/twitter_precision_policy.yml",
        help="Path to the WorldGossip Twitter precision policy YAML",
    )
    parser.add_argument(
        "--profiles",
        default="config/query_profiles.yml",
        help="Path to the WorldGossip query profiles YAML",
    )
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    args = parser.parse_args()

    summary = evaluate_ledger(Path(args.ledger), Path(args.policy), Path(args.profiles))
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
