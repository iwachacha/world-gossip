"""Portfolio-aware query profile selection for Agent Reach runs."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .profiles import QueryBatchRules, QueryPortfolioTargets, QueryProfile, load_query_profile_config


CLUSTER_COUNTRIES: dict[str, frozenset[str]] = {
    "east_asia": frozenset({"kr", "tw"}),
    "southeast_asia": frozenset({"th", "sg", "ph", "id", "vn", "in"}),
    "europe": frozenset({"fr", "de", "it", "es", "nl", "se", "pt"}),
    "latam": frozenset({"mx", "br", "ar", "cl", "co", "pe"}),
    "anglosphere": frozenset({"us", "gb", "au", "ca", "ie", "nz"}),
}


@dataclass
class QuerySelectionState:
    """Rolling selection history used to reduce repeated bias across runs."""

    total_runs: int = 0
    profile_counts: dict[str, int] = field(default_factory=dict)
    role_counts: dict[str, int] = field(default_factory=dict)
    language_lane_counts: dict[str, int] = field(default_factory=dict)
    topic_bucket_counts: dict[str, int] = field(default_factory=dict)
    cluster_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "total_runs": self.total_runs,
            "profile_counts": self.profile_counts,
            "role_counts": self.role_counts,
            "language_lane_counts": self.language_lane_counts,
            "topic_bucket_counts": self.topic_bucket_counts,
            "cluster_counts": self.cluster_counts,
        }


@dataclass(frozen=True)
class QuerySelectionDecision:
    """Selected profile plus machine-readable scoring hints."""

    profile: QueryProfile
    score: float
    score_breakdown: dict[str, float]
    clusters: tuple[str, ...]


@dataclass(frozen=True)
class QuerySelectionPlan:
    """Auto-selection output returned to the runner."""

    decisions: tuple[QuerySelectionDecision, ...]
    role_targets: dict[str, int]
    language_lane_targets: dict[str, int]
    batch_rules: QueryBatchRules

    @property
    def profiles(self) -> tuple[QueryProfile, ...]:
        return tuple(decision.profile for decision in self.decisions)

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_profiles": [
                {
                    "id": decision.profile.id,
                    "priority": decision.profile.priority,
                    "lane": decision.profile.lane,
                    "portfolio_role": decision.profile.portfolio_role,
                    "language_lane": decision.profile.language_lane,
                    "topic_bucket": decision.profile.topic_bucket,
                    "motif": decision.profile.motif,
                    "country_scope": list(decision.profile.country_scope),
                    "clusters": list(decision.clusters),
                    "score": round(decision.score, 3),
                    "score_breakdown": {
                        key: round(value, 3) for key, value in sorted(decision.score_breakdown.items())
                    },
                }
                for decision in self.decisions
            ],
            "role_targets": self.role_targets,
            "language_lane_targets": self.language_lane_targets,
            "batch_rules": {
                "max_same_topic_bucket": self.batch_rules.max_same_topic_bucket,
                "min_distinct_topic_buckets": self.batch_rules.min_distinct_topic_buckets,
                "min_distinct_archetypes": self.batch_rules.min_distinct_archetypes,
                "require_frontier_profile": self.batch_rules.require_frontier_profile,
                "min_non_jp_profiles": self.batch_rules.min_non_jp_profiles,
                "min_local_bridge_profiles": self.batch_rules.min_local_bridge_profiles,
                "min_object_anchor_profiles": self.batch_rules.min_object_anchor_profiles,
                "max_jp_scoped_share": self.batch_rules.max_jp_scoped_share,
            },
        }


def load_profile_selection_state(path: str | Path) -> QuerySelectionState:
    """Load selection history from disk or return an empty state."""

    state_path = Path(path)
    if not state_path.exists():
        return QuerySelectionState()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return QuerySelectionState(
        total_runs=int(payload.get("total_runs") or 0),
        profile_counts={str(key): int(value) for key, value in (payload.get("profile_counts") or {}).items()},
        role_counts={str(key): int(value) for key, value in (payload.get("role_counts") or {}).items()},
        language_lane_counts={
            str(key): int(value) for key, value in (payload.get("language_lane_counts") or {}).items()
        },
        topic_bucket_counts={
            str(key): int(value) for key, value in (payload.get("topic_bucket_counts") or {}).items()
        },
        cluster_counts={str(key): int(value) for key, value in (payload.get("cluster_counts") or {}).items()},
    )


def save_profile_selection_state(path: str | Path, state: QuerySelectionState) -> None:
    """Persist selection history as UTF-8 JSON."""

    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def infer_profile_clusters(profile: QueryProfile) -> tuple[str, ...]:
    """Infer region clusters from the profile's non-JP country scope."""

    scope = set(profile.country_scope) - {"jp"}
    return tuple(
        cluster_name
        for cluster_name, countries in CLUSTER_COUNTRIES.items()
        if scope & countries
    )


def record_profile_selection(state: QuerySelectionState, profiles: list[QueryProfile] | tuple[QueryProfile, ...]) -> QuerySelectionState:
    """Return updated state after one successful profile batch."""

    profile_counts = dict(state.profile_counts)
    role_counts = dict(state.role_counts)
    language_lane_counts = dict(state.language_lane_counts)
    topic_bucket_counts = dict(state.topic_bucket_counts)
    cluster_counts = dict(state.cluster_counts)

    for profile in profiles:
        profile_counts[profile.id] = profile_counts.get(profile.id, 0) + 1
        if profile.portfolio_role:
            role_counts[profile.portfolio_role] = role_counts.get(profile.portfolio_role, 0) + 1
        if profile.language_lane:
            language_lane_counts[profile.language_lane] = language_lane_counts.get(profile.language_lane, 0) + 1
        if profile.topic_bucket:
            topic_bucket_counts[profile.topic_bucket] = topic_bucket_counts.get(profile.topic_bucket, 0) + 1
        for cluster in infer_profile_clusters(profile):
            cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

    return QuerySelectionState(
        total_runs=state.total_runs + 1,
        profile_counts=profile_counts,
        role_counts=role_counts,
        language_lane_counts=language_lane_counts,
        topic_bucket_counts=topic_bucket_counts,
        cluster_counts=cluster_counts,
    )


def _allocate_targets(limit: int, mix: dict[str, float], available_labels: set[str]) -> dict[str, int]:
    weighted_labels = {
        label: weight
        for label, weight in mix.items()
        if label in available_labels and weight > 0
    }
    if limit <= 0 or not weighted_labels:
        return {}

    total_weight = sum(weighted_labels.values())
    raw_targets = {
        label: (limit * weight / total_weight)
        for label, weight in weighted_labels.items()
    }
    targets = {label: int(math.floor(value)) for label, value in raw_targets.items()}
    remainder = limit - sum(targets.values())
    fractional_order = sorted(
        weighted_labels,
        key=lambda label: (raw_targets[label] - targets[label], weighted_labels[label], label),
        reverse=True,
    )
    for label in fractional_order[:remainder]:
        targets[label] += 1
    return targets


def _underused_bonus(label: str, counts: dict[str, int], universe: set[str], weight: float) -> float:
    if not label or label not in universe:
        return 0.0
    max_seen = max((counts.get(item, 0) for item in universe), default=0)
    return max(0.0, float(max_seen - counts.get(label, 0))) * weight


def _selected_archetypes(selected: list[QueryProfile]) -> set[str]:
    return {tag for profile in selected for tag in profile.archetype_tags}


def _has_jp_scope(profile: QueryProfile) -> bool:
    return "jp" in profile.country_scope


def _is_non_jp_profile(profile: QueryProfile) -> bool:
    return "jp" not in profile.country_scope


def _score_candidate(
    candidate: QueryProfile,
    *,
    selected: list[QueryProfile],
    state: QuerySelectionState,
    targets: QueryPortfolioTargets,
    role_targets: dict[str, int],
    language_lane_targets: dict[str, int],
    all_topics: set[str],
    all_language_lanes: set[str],
    all_roles: set[str],
    preferred_clusters: set[str],
    limit: int,
) -> tuple[float, dict[str, float], tuple[str, ...]]:
    batch_rules = targets.batch_rules
    topic_counts = Counter(profile.topic_bucket for profile in selected if profile.topic_bucket)
    role_counts = Counter(profile.portfolio_role for profile in selected if profile.portfolio_role)
    lane_counts = Counter(profile.language_lane for profile in selected if profile.language_lane)
    selected_archetypes = _selected_archetypes(selected)
    selected_non_jp = sum(1 for profile in selected if _is_non_jp_profile(profile))
    selected_local_bridge = sum(1 for profile in selected if profile.language_lane == "local_bridge")
    selected_object_anchor = sum(1 for profile in selected if profile.motif == "object_anchor_banter")
    selected_jp_scoped = sum(1 for profile in selected if _has_jp_scope(profile))
    clusters = infer_profile_clusters(candidate)
    selected_clusters = {cluster for profile in selected for cluster in infer_profile_clusters(profile)}

    score_breakdown: dict[str, float] = {}
    score_breakdown["priority"] = float(candidate.priority) * 10.0

    if candidate.portfolio_role and role_targets:
        target = role_targets.get(candidate.portfolio_role, 0)
        current = role_counts.get(candidate.portfolio_role, 0)
        if current < target:
            score_breakdown["role_target_gap"] = float(target - current) * 45.0
        else:
            score_breakdown["role_target_overflow"] = -float(current - target + 1) * 45.0

    if candidate.language_lane and language_lane_targets:
        target = language_lane_targets.get(candidate.language_lane, 0)
        current = lane_counts.get(candidate.language_lane, 0)
        if current < target:
            score_breakdown["language_lane_gap"] = float(target - current) * 60.0
        else:
            score_breakdown["language_lane_overflow"] = -float(current - target + 1) * 75.0

    if candidate.topic_bucket:
        current_topic_count = topic_counts.get(candidate.topic_bucket, 0)
        if current_topic_count == 0:
            score_breakdown["new_topic_bucket"] = 55.0
        if current_topic_count >= batch_rules.max_same_topic_bucket:
            score_breakdown["topic_cap_penalty"] = -250.0
        score_breakdown["topic_underused_history"] = _underused_bonus(
            candidate.topic_bucket,
            state.topic_bucket_counts,
            all_topics,
            weight=2.5,
        )

    new_archetypes = [tag for tag in candidate.archetype_tags if tag not in selected_archetypes]
    if new_archetypes:
        score_breakdown["new_archetype"] = float(min(len(new_archetypes), 2)) * 30.0
    if len({profile.topic_bucket for profile in selected if profile.topic_bucket}) < batch_rules.min_distinct_topic_buckets:
        if candidate.topic_bucket and topic_counts.get(candidate.topic_bucket, 0) == 0:
            score_breakdown["topic_diversity_need"] = 22.0
    if len(selected_archetypes) < batch_rules.min_distinct_archetypes and new_archetypes:
        score_breakdown["archetype_diversity_need"] = 18.0

    if batch_rules.min_non_jp_profiles and _is_non_jp_profile(candidate) and selected_non_jp < batch_rules.min_non_jp_profiles:
        score_breakdown["non_jp_floor"] = 80.0
    if batch_rules.min_local_bridge_profiles and candidate.language_lane == "local_bridge" and selected_local_bridge < batch_rules.min_local_bridge_profiles:
        score_breakdown["local_bridge_floor"] = 70.0
    if batch_rules.min_object_anchor_profiles and candidate.motif == "object_anchor_banter" and selected_object_anchor < batch_rules.min_object_anchor_profiles:
        score_breakdown["object_anchor_floor"] = 75.0

    future_jp_scoped = selected_jp_scoped + (1 if _has_jp_scope(candidate) else 0)
    future_selected = len(selected) + 1
    jp_share = future_jp_scoped / future_selected if future_selected else 1.0
    if _has_jp_scope(candidate) and jp_share > batch_rules.max_jp_scoped_share:
        score_breakdown["jp_share_penalty"] = -(jp_share - batch_rules.max_jp_scoped_share) * 250.0
    elif not _has_jp_scope(candidate):
        score_breakdown["non_jp_bonus"] = 28.0

    profile_count = state.profile_counts.get(candidate.id, 0)
    score_breakdown["profile_novelty"] = max(0.0, 30.0 - float(profile_count) * 6.0)
    if candidate.portfolio_role:
        score_breakdown["role_underused_history"] = _underused_bonus(
            candidate.portfolio_role,
            state.role_counts,
            all_roles,
            weight=3.5,
        )
    if candidate.language_lane:
        score_breakdown["language_underused_history"] = _underused_bonus(
            candidate.language_lane,
            state.language_lane_counts,
            all_language_lanes,
            weight=3.0,
        )

    if clusters:
        cluster_bonus = 0.0
        cluster_universe = preferred_clusters or set(clusters)
        for cluster in clusters:
            if cluster in preferred_clusters and cluster not in selected_clusters:
                cluster_bonus += 20.0
            cluster_bonus += _underused_bonus(cluster, state.cluster_counts, cluster_universe, weight=2.0)
        score_breakdown["cluster_rotation"] = cluster_bonus

    if candidate.motif == "object_anchor_banter":
        score_breakdown["banter_bonus"] = 20.0
    if candidate.language_lane == "ja_seed":
        score_breakdown["ja_seed_balance"] = 18.0
    if candidate.language_lane == "local_bridge":
        score_breakdown["local_bridge_balance"] = 20.0
    if len(selected) + 1 == limit and batch_rules.require_frontier_profile:
        has_frontier = any(profile.portfolio_role == "frontier" for profile in selected)
        if not has_frontier and candidate.portfolio_role == "frontier":
            score_breakdown["frontier_floor"] = 120.0
        elif not has_frontier:
            score_breakdown["frontier_miss_penalty"] = -180.0

    return sum(score_breakdown.values()), score_breakdown, clusters


def _select_best_candidate(
    remaining: list[QueryProfile],
    *,
    selected: list[QueryProfile],
    state: QuerySelectionState,
    targets: QueryPortfolioTargets,
    role_targets: dict[str, int],
    language_lane_targets: dict[str, int],
    all_topics: set[str],
    all_language_lanes: set[str],
    all_roles: set[str],
    preferred_clusters: set[str],
    limit: int,
) -> QuerySelectionDecision:
    ranked: list[QuerySelectionDecision] = []
    for candidate in remaining:
        score, breakdown, clusters = _score_candidate(
            candidate,
            selected=selected,
            state=state,
            targets=targets,
            role_targets=role_targets,
            language_lane_targets=language_lane_targets,
            all_topics=all_topics,
            all_language_lanes=all_language_lanes,
            all_roles=all_roles,
            preferred_clusters=preferred_clusters,
            limit=limit,
        )
        ranked.append(
            QuerySelectionDecision(
                profile=candidate,
                score=score,
                score_breakdown=breakdown,
                clusters=clusters,
            )
        )
    ranked.sort(
        key=lambda decision: (
            decision.score,
            decision.profile.priority,
            decision.profile.portfolio_role == "frontier",
            decision.profile.language_lane == "local_bridge",
            decision.profile.id,
        ),
        reverse=True,
    )
    return ranked[0]


def select_query_profiles(
    profile_path: str | Path,
    *,
    limit: int,
    state: QuerySelectionState | None = None,
    include_guarded: bool = False,
) -> QuerySelectionPlan:
    """Select a portfolio-balanced set of enabled profiles for one run."""

    config = load_query_profile_config(profile_path)
    portfolio_targets = config.portfolio_targets
    candidates = [
        profile
        for profile in config.profiles.values()
        if profile.enabled and (include_guarded or profile.portfolio_role != "guarded")
    ]
    candidates.sort(key=lambda profile: (profile.priority, profile.id), reverse=True)

    effective_limit = min(max(limit, 0), len(candidates))
    if effective_limit <= 0:
        return QuerySelectionPlan(
            decisions=(),
            role_targets={},
            language_lane_targets={},
            batch_rules=portfolio_targets.batch_rules,
        )

    all_topics = {profile.topic_bucket for profile in candidates if profile.topic_bucket}
    all_language_lanes = {profile.language_lane for profile in candidates if profile.language_lane}
    all_roles = {profile.portfolio_role for profile in candidates if profile.portfolio_role}
    preferred_clusters = set(portfolio_targets.preferred_clusters)
    role_targets = _allocate_targets(effective_limit, portfolio_targets.exploration_mix, all_roles)
    language_lane_targets = _allocate_targets(
        effective_limit,
        portfolio_targets.language_lane_mix,
        all_language_lanes,
    )

    selection_state = state or QuerySelectionState()
    selected: list[QueryProfile] = []
    decisions: list[QuerySelectionDecision] = []
    remaining = list(candidates)
    while remaining and len(selected) < effective_limit:
        decision = _select_best_candidate(
            remaining,
            selected=selected,
            state=selection_state,
            targets=portfolio_targets,
            role_targets=role_targets,
            language_lane_targets=language_lane_targets,
            all_topics=all_topics,
            all_language_lanes=all_language_lanes,
            all_roles=all_roles,
            preferred_clusters=preferred_clusters,
            limit=effective_limit,
        )
        decisions.append(decision)
        selected.append(decision.profile)
        remaining = [profile for profile in remaining if profile.id != decision.profile.id]

    return QuerySelectionPlan(
        decisions=tuple(decisions),
        role_targets=role_targets,
        language_lane_targets=language_lane_targets,
        batch_rules=portfolio_targets.batch_rules,
    )
