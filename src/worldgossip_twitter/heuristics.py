"""Heuristics that fill the gap while Agent Reach remains a thin collector."""

from __future__ import annotations

from .models import PrecisionPolicy, SearchPost


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split()).strip().lower()


def infer_country_anchor(post: SearchPost, policy: PrecisionPolicy) -> bool:
    """Return whether the post itself appears anchored to countries or regions."""

    if post.country_anchor_present is not None:
        return post.country_anchor_present

    haystacks = [
        _normalize_text(post.text),
        _normalize_text(post.requested_query or ""),
    ]
    return any(term.lower() in haystack for haystack in haystacks for term in policy.country_anchor_terms)


def infer_cross_country_seed(post: SearchPost, policy: PrecisionPolicy) -> bool:
    """Return whether the post appears likely to invite cross-country conversation."""

    if post.cross_country_seed_present is not None:
        return post.cross_country_seed_present

    text = _normalize_text(post.text)
    if any(term.lower() in text for term in policy.cross_country_seed_terms):
        return True
    if "?" in (post.text or "") and any(
        term.lower() in text for term in policy.conversation_question_terms
    ):
        return True
    return False
