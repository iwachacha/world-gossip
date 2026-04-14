"""Bridge Agent Reach Twitter results into WorldGossip search candidates."""

from __future__ import annotations

from collections.abc import Iterable

from .models import SearchPost, TweetMetrics


def _as_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(str(value) for value in values if value)


def _engagement(item: dict) -> TweetMetrics:
    payload = item.get("engagement") or {}
    return TweetMetrics(
        likes=int(payload.get("likes") or 0),
        retweets=int(payload.get("retweets") or 0),
        replies=int(payload.get("replies") or 0),
        quotes=int(payload.get("quotes") or 0),
        views=int(payload.get("views") or 0),
        bookmarks=int(payload.get("bookmarks") or 0),
    )


def from_agent_reach_item(
    item: dict,
    *,
    query_id: str | None = None,
    requested_query: str | None = None,
) -> SearchPost:
    """Convert one Agent Reach Twitter normalized item into a SearchPost."""

    extras = item.get("extras") or {}
    urls = extras.get("urls") or []

    return SearchPost(
        id=str(item.get("id") or item.get("source_item_id") or ""),
        text=str(item.get("text") or ""),
        author_screen_name=str(item.get("author") or ""),
        author_name=str(extras.get("author_name") or ""),
        lang=str(extras.get("lang") or ""),
        urls=_as_tuple(urls),
        metrics=_engagement(item),
        is_retweet=bool(extras.get("is_retweet", False)),
        quoted_tweet_id=((extras.get("quoted_tweet") or {}).get("id") if isinstance(extras.get("quoted_tweet"), dict) else None),
        query_id=query_id,
        requested_query=requested_query,
    )


def iter_posts_from_collection_result(
    result: dict,
    *,
    query_id: str | None = None,
    requested_query: str | None = None,
) -> list[SearchPost]:
    """Extract Twitter post candidates from one CollectionResult envelope."""

    if result.get("channel") != "twitter":
        return []
    items = result.get("items") or []
    if not isinstance(items, list):
        return []

    posts: list[SearchPost] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("kind") != "post":
            continue
        posts.append(
            from_agent_reach_item(
                item,
                query_id=query_id,
                requested_query=requested_query,
            )
        )
    return posts


def iter_posts_from_ledger_record(record: dict) -> list[SearchPost]:
    """Extract SearchPost items from one Agent Reach ledger record."""

    result = record.get("result") or {}
    if not isinstance(result, dict):
        return []
    return iter_posts_from_collection_result(
        result,
        query_id=record.get("query_id"),
        requested_query=record.get("input"),
    )


def iter_posts_from_ledger(records: Iterable[dict]) -> list[SearchPost]:
    """Flatten multiple Agent Reach ledger records into SearchPost items."""

    posts: list[SearchPost] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        posts.extend(iter_posts_from_ledger_record(record))
    return posts
