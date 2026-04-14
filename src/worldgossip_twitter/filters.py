"""Twitter/X pre-DB noise gates for WorldGossip."""

from __future__ import annotations

from dataclasses import dataclass

from .heuristics import infer_country_anchor, infer_cross_country_seed
from .models import PrecisionPolicy, SearchPost


@dataclass(frozen=True)
class FilterDecision:
    """Decision emitted by the pre-DB gate."""

    keep: bool
    reasons: tuple[str, ...]


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def is_reply_like(post: SearchPost) -> bool:
    """Return True when the post looks like a reply.

    Prefer explicit metadata when present. Text fallback keeps the current host
    behavior usable even while the upstream collector remains thin.
    """

    if post.in_reply_to_tweet_id:
        return True
    if post.conversation_id and post.conversation_id != post.id:
        return True
    return _normalize_text(post.text).startswith("@")


def is_link_stub(post: SearchPost, policy: PrecisionPolicy) -> bool:
    text = _normalize_text(post.text)
    lowered = text.lower()
    if any(phrase.lower() in lowered for phrase in policy.link_stub_phrases):
        return True
    if post.urls and len(text) <= 80:
        return True
    return False


def is_broadcast_like(post: SearchPost, policy: PrecisionPolicy) -> bool:
    handle = (post.author_screen_name or "").lower()
    text = _normalize_text(post.text)
    lowered = text.lower()
    has_question_signal = any(token in lowered for token in ("?", "how", "what", "where", "why"))
    if any(token in handle for token in policy.broadcast_handle_tokens) and post.urls:
        return True
    if post.urls and not has_question_signal:
        return True
    return False


def is_identity_validation_prompt(post: SearchPost, policy: PrecisionPolicy) -> bool:
    text = _normalize_text(post.text).lower()
    return any(phrase.lower() in text for phrase in policy.identity_validation_phrases)


def is_travel_promo_like(post: SearchPost, policy: PrecisionPolicy) -> bool:
    handle = (post.author_screen_name or "").lower()
    text = _normalize_text(post.text).lower()
    if any(token.lower() in handle for token in policy.travel_handle_tokens):
        return True
    return any(phrase.lower() in text for phrase in policy.travel_promo_phrases)


def is_low_traction(post: SearchPost, policy: PrecisionPolicy) -> bool:
    return post.metrics.views < policy.min_views_floor


def is_weak_conversation(post: SearchPost, policy: PrecisionPolicy) -> bool:
    return (
        post.metrics.replies < policy.weak_conversation_replies_lt
        and post.metrics.quotes < policy.weak_conversation_quotes_lt
    )


def apply_pre_db_noise_gate(post: SearchPost, policy: PrecisionPolicy) -> FilterDecision:
    """Apply the host-owned pre-DB gate before persistence."""

    reasons: list[str] = []

    if policy.discard_retweets and post.is_retweet:
        reasons.append("retweet")
    if policy.discard_reply_like_posts and is_reply_like(post):
        reasons.append("reply_like")
    if policy.discard_link_stub_posts and is_link_stub(post, policy):
        reasons.append("link_stub")
    if policy.discard_external_news_or_brand_broadcast_posts and is_broadcast_like(post, policy):
        reasons.append("broadcast_like")
    if is_identity_validation_prompt(post, policy):
        reasons.append("identity_validation")
    if is_travel_promo_like(post, policy):
        reasons.append("travel_promo")
    if is_low_traction(post, policy):
        reasons.append("low_views")
    if policy.discard_weak_conversation_posts and is_weak_conversation(post, policy):
        reasons.append("weak_conversation")
    if policy.require_country_anchor_after_normalization and not infer_country_anchor(post, policy):
        reasons.append("missing_country_anchor")
    if policy.require_cross_country_seed and not infer_cross_country_seed(post, policy):
        reasons.append("missing_cross_country_seed")

    return FilterDecision(keep=not reasons, reasons=tuple(reasons))
