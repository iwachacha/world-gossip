"""Core contracts for the WorldGossip Twitter/X precision layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TweetMetrics:
    """Public engagement counters captured during discovery or refresh."""

    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    views: int = 0
    bookmarks: int = 0


@dataclass(frozen=True)
class SearchPost:
    """Twitter/X candidate retained before DB ingest.

    The shape intentionally keeps room for raw X-specific metadata that a generic
    collector may not expose yet. Until upstream surfaces improve, text-based
    fallbacks remain part of the filter layer.
    """

    id: str
    text: str
    author_screen_name: str
    author_name: str = ""
    lang: str = ""
    urls: tuple[str, ...] = ()
    metrics: TweetMetrics = field(default_factory=TweetMetrics)
    is_retweet: bool = False
    conversation_id: str | None = None
    in_reply_to_tweet_id: str | None = None
    in_reply_to_screen_name: str | None = None
    quoted_tweet_id: str | None = None
    country_anchor_present: bool | None = None
    cross_country_seed_present: bool | None = None
    query_id: str | None = None
    requested_query: str | None = None


@dataclass(frozen=True)
class PrecisionPolicy:
    """Host-owned pre-DB filtering policy."""

    root_post_only: bool = True
    discard_retweets: bool = True
    discard_reply_like_posts: bool = True
    discard_link_stub_posts: bool = True
    discard_external_news_or_brand_broadcast_posts: bool = True
    discard_weak_conversation_posts: bool = True
    require_country_anchor_after_normalization: bool = True
    require_cross_country_seed: bool = True
    min_views_floor: int = 5000
    weak_conversation_replies_lt: int = 5
    weak_conversation_quotes_lt: int = 2
    link_stub_phrases: tuple[str, ...] = ()
    broadcast_handle_tokens: tuple[str, ...] = ()
    conversation_question_terms: tuple[str, ...] = ()
    identity_validation_phrases: tuple[str, ...] = ()
    travel_promo_phrases: tuple[str, ...] = ()
    travel_handle_tokens: tuple[str, ...] = ()
    country_anchor_terms: tuple[str, ...] = ()
    cross_country_seed_terms: tuple[str, ...] = ()
