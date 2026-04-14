"""Policy loading helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import PrecisionPolicy


def load_precision_policy(path: str | Path) -> PrecisionPolicy:
    """Load the WorldGossip Twitter/X precision policy from YAML."""

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    filters = payload.get("filters") or {}
    thresholds = payload.get("thresholds") or {}

    return PrecisionPolicy(
        root_post_only=bool(filters.get("root_post_only", True)),
        discard_retweets=bool(filters.get("discard_retweets", True)),
        discard_reply_like_posts=bool(filters.get("discard_reply_like_posts", True)),
        discard_link_stub_posts=bool(filters.get("discard_link_stub_posts", True)),
        discard_external_news_or_brand_broadcast_posts=bool(
            filters.get("discard_external_news_or_brand_broadcast_posts", True)
        ),
        discard_weak_conversation_posts=bool(filters.get("discard_weak_conversation_posts", True)),
        require_country_anchor_after_normalization=bool(
            filters.get("require_country_anchor_after_normalization", True)
        ),
        require_cross_country_seed=bool(filters.get("require_cross_country_seed", True)),
        min_views_floor=int(thresholds.get("min_views_floor", 5000)),
        weak_conversation_replies_lt=int(thresholds.get("weak_conversation_replies_lt", 5)),
        weak_conversation_quotes_lt=int(thresholds.get("weak_conversation_quotes_lt", 2)),
        link_stub_phrases=tuple(payload.get("link_stub_phrases") or ()),
        broadcast_handle_tokens=tuple(payload.get("broadcast_handle_tokens") or ()),
        conversation_question_terms=tuple(payload.get("conversation_question_terms") or ()),
        identity_validation_phrases=tuple(payload.get("identity_validation_phrases") or ()),
        travel_promo_phrases=tuple(payload.get("travel_promo_phrases") or ()),
        travel_handle_tokens=tuple(payload.get("travel_handle_tokens") or ()),
        country_anchor_terms=tuple(payload.get("country_anchor_terms") or ()),
        cross_country_seed_terms=tuple(payload.get("cross_country_seed_terms") or ()),
    )
