"""Query profile loading and gate helpers for WorldGossip."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class QueryGatePolicy:
    """Per-query threshold gate applied after generic pre-DB filtering."""

    min_views: int = 0
    min_replies: int = 0
    min_quotes: int = 0


@dataclass(frozen=True)
class QueryProfile:
    """Subset of query profile metadata relevant to candidate evaluation."""

    id: str
    enabled: bool
    lane: str = ""
    maturity: str = ""
    priority: int = 0
    portfolio_role: str = ""
    language_lane: str = ""
    motif: str = ""
    topic_bucket: str = ""
    archetype_tags: tuple[str, ...] = ()
    language_scope: tuple[str, ...] = ()
    country_scope: tuple[str, ...] = ()
    window_hours: int = 168
    discovery_limit: int = 16
    query_template: str = ""
    gate_policy: QueryGatePolicy = field(default_factory=QueryGatePolicy)


@dataclass(frozen=True)
class QueryBatchRules:
    """Portfolio constraints used during automatic profile selection."""

    max_same_topic_bucket: int = 2
    min_distinct_topic_buckets: int = 1
    min_distinct_archetypes: int = 1
    require_frontier_profile: bool = False
    min_non_jp_profiles: int = 0
    min_local_bridge_profiles: int = 0
    min_object_anchor_profiles: int = 0
    max_jp_scoped_share: float = 1.0


@dataclass(frozen=True)
class QueryPortfolioTargets:
    """Soft portfolio targets used to keep collection balanced."""

    exploration_mix: dict[str, float] = field(default_factory=dict)
    language_lane_mix: dict[str, float] = field(default_factory=dict)
    preferred_clusters: tuple[str, ...] = ()
    batch_rules: QueryBatchRules = field(default_factory=QueryBatchRules)


@dataclass(frozen=True)
class QueryProfileConfig:
    """Typed config payload loaded from `query_profiles.yml`."""

    profiles: dict[str, QueryProfile]
    portfolio_targets: QueryPortfolioTargets = field(default_factory=QueryPortfolioTargets)


def _as_tuple(raw_value: Any) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return ()
    return tuple(str(item).strip() for item in raw_value if str(item).strip())


def _load_payload(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def load_query_profile_config(path: str | Path) -> QueryProfileConfig:
    """Load typed query profile config plus portfolio targets."""

    payload = _load_payload(path)
    raw_profiles = payload.get("profiles") or []
    profiles: dict[str, QueryProfile] = {}

    for raw_profile in raw_profiles:
        if not isinstance(raw_profile, dict):
            continue
        profile_id = str(raw_profile.get("id") or "").strip()
        if not profile_id:
            continue
        gate = raw_profile.get("gate_policy") or {}
        profiles[profile_id] = QueryProfile(
            id=profile_id,
            enabled=bool(raw_profile.get("enabled", False)),
            lane=str(raw_profile.get("lane") or ""),
            maturity=str(raw_profile.get("maturity") or ""),
            priority=int(raw_profile.get("priority") or 0),
            portfolio_role=str(raw_profile.get("portfolio_role") or ""),
            language_lane=str(raw_profile.get("language_lane") or ""),
            motif=str(raw_profile.get("motif") or ""),
            topic_bucket=str(raw_profile.get("topic_bucket") or ""),
            archetype_tags=_as_tuple(raw_profile.get("archetype_tags")),
            language_scope=_as_tuple(raw_profile.get("language_scope")),
            country_scope=_as_tuple(raw_profile.get("country_scope")),
            window_hours=int(raw_profile.get("window_hours") or 168),
            discovery_limit=int(raw_profile.get("discovery_limit") or 16),
            query_template=str(raw_profile.get("query_template") or ""),
            gate_policy=QueryGatePolicy(
                min_views=int(gate.get("min_views") or 0),
                min_replies=int(gate.get("min_replies") or 0),
                min_quotes=int(gate.get("min_quotes") or 0),
            ),
        )

    portfolio_targets_raw = payload.get("portfolio_targets") or {}
    batch_rules_raw = portfolio_targets_raw.get("batch_rules") or {}
    region_rotation_raw = portfolio_targets_raw.get("region_rotation") or {}
    portfolio_targets = QueryPortfolioTargets(
        exploration_mix={
            str(key): float(value)
            for key, value in (portfolio_targets_raw.get("exploration_mix") or {}).items()
        },
        language_lane_mix={
            str(key): float(value)
            for key, value in (portfolio_targets_raw.get("language_lane_mix") or {}).items()
        },
        preferred_clusters=_as_tuple(region_rotation_raw.get("preferred_clusters")),
        batch_rules=QueryBatchRules(
            max_same_topic_bucket=int(batch_rules_raw.get("max_same_topic_bucket") or 2),
            min_distinct_topic_buckets=int(batch_rules_raw.get("min_distinct_topic_buckets") or 1),
            min_distinct_archetypes=int(batch_rules_raw.get("min_distinct_archetypes") or 1),
            require_frontier_profile=bool(batch_rules_raw.get("require_frontier_profile", False)),
            min_non_jp_profiles=int(batch_rules_raw.get("min_non_jp_profiles") or 0),
            min_local_bridge_profiles=int(batch_rules_raw.get("min_local_bridge_profiles") or 0),
            min_object_anchor_profiles=int(batch_rules_raw.get("min_object_anchor_profiles") or 0),
            max_jp_scoped_share=float(batch_rules_raw.get("max_jp_scoped_share") or 1.0),
        ),
    )
    return QueryProfileConfig(profiles=profiles, portfolio_targets=portfolio_targets)


def load_query_profiles(path: str | Path) -> dict[str, QueryProfile]:
    """Load query profiles keyed by profile id."""

    return load_query_profile_config(path).profiles
