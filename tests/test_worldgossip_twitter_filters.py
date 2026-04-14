import json
from pathlib import Path

from worldgossip_twitter import (
    SearchPost,
    TweetMetrics,
    apply_pre_db_noise_gate,
    from_agent_reach_item,
    infer_country_anchor,
    infer_cross_country_seed,
    iter_posts_from_ledger_record,
    load_precision_policy,
    load_query_profiles,
)
from worldgossip_twitter.evaluate import evaluate_ledger


POLICY_PATH = Path("config/twitter_precision_policy.yml")


def test_policy_loads_defaults() -> None:
    policy = load_precision_policy(POLICY_PATH)

    assert policy.root_post_only is True
    assert policy.min_views_floor == 5000
    assert "詳細はこちら" in policy.link_stub_phrases


def test_reply_like_uses_metadata_first() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="1",
        text="Thanks for the answer",
        author_screen_name="alice",
        in_reply_to_tweet_id="999",
        metrics=TweetMetrics(views=7000),
        country_anchor_present=True,
        cross_country_seed_present=True,
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is False
    assert "reply_like" in decision.reasons


def test_noise_gate_rejects_low_quality_reply_stub() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="1",
        text="@bob 詳細はこちら https://t.co/example",
        author_screen_name="smallaccount",
        urls=("https://example.com",),
        metrics=TweetMetrics(views=60),
        country_anchor_present=True,
        cross_country_seed_present=True,
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is False
    assert "reply_like" in decision.reasons
    assert "link_stub" in decision.reasons
    assert "low_views" in decision.reasons


def test_noise_gate_keeps_high_view_root_post() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="2043309710850576795",
        text="There is automatic translation now, so I want to ask people around the world: what do you grill at home?",
        author_screen_name="jun_example",
        metrics=TweetMetrics(views=1540537, replies=1246, quotes=80),
        country_anchor_present=True,
        cross_country_seed_present=True,
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is True
    assert decision.reasons == ()


def test_infer_country_anchor_and_seed_from_text() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x1",
        text="There is automatic translation now, so I want to ask people around the world: what do you grill at home in Japan?",
        author_screen_name="jun_example",
        metrics=TweetMetrics(views=10000, replies=20, quotes=5),
    )

    assert infer_country_anchor(post, policy) is True
    assert infer_cross_country_seed(post, policy) is True


def test_cross_country_seed_no_longer_uses_metrics_only_fallback() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x1b",
        text="Japan's convenience stores are on another level.",
        author_screen_name="essay_account",
        metrics=TweetMetrics(views=50000, replies=300, quotes=25),
    )

    assert infer_country_anchor(post, policy) is True
    assert infer_cross_country_seed(post, policy) is False


def test_noise_gate_drops_missing_anchor_and_seed() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x2",
        text="Beautiful morning coffee setup",
        author_screen_name="lifestyle_account",
        metrics=TweetMetrics(views=18000, replies=1, quotes=0),
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is False
    assert "weak_conversation" in decision.reasons
    assert "missing_country_anchor" in decision.reasons
    assert "missing_cross_country_seed" in decision.reasons


def test_noise_gate_drops_identity_validation_prompt() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x2b",
        text="Japan do you like when foreigners compliment your culture?",
        author_screen_name="green_account",
        metrics=TweetMetrics(views=15000, replies=120, quotes=9),
        country_anchor_present=True,
        cross_country_seed_present=True,
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is False
    assert "identity_validation" in decision.reasons


def test_noise_gate_drops_move_to_japan_planning_prompt() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x2c",
        text="Can an American move to Japan and learn Japanese? What do you think?",
        author_screen_name="planning_account",
        metrics=TweetMetrics(views=90000, replies=500, quotes=40),
        country_anchor_present=True,
        cross_country_seed_present=True,
    )

    decision = apply_pre_db_noise_gate(post, policy)

    assert decision.keep is False
    assert "travel_promo" in decision.reasons


def test_from_agent_reach_item_maps_core_fields() -> None:
    item = {
        "id": "2041126787690934455",
        "kind": "post",
        "text": "What is the appeal of raw animal proteins?",
        "author": "skindie___",
        "engagement": {
            "likes": 277,
            "retweets": 45,
            "replies": 322,
            "quotes": 38,
            "views": 35205,
            "bookmarks": 13,
        },
        "extras": {
            "author_name": "Skindie",
            "lang": "en",
            "is_retweet": False,
            "urls": [],
        },
    }

    post = from_agent_reach_item(
        item,
        query_id="en_jp_convenience_snack_question_live",
        requested_query="raw chicken japan",
    )

    assert post.id == "2041126787690934455"
    assert post.author_screen_name == "skindie___"
    assert post.metrics.views == 35205
    assert post.query_id == "en_jp_convenience_snack_question_live"


def test_iter_posts_from_ledger_record_uses_record_metadata() -> None:
    record = {
        "channel": "twitter",
        "operation": "search",
        "input": "raw chicken japan",
        "query_id": "en_jp_convenience_snack_question_live",
        "result": {
            "channel": "twitter",
            "operation": "search",
            "items": [
                {
                    "id": "2041126787690934455",
                    "kind": "post",
                    "text": "What is the appeal of raw animal proteins?",
                    "author": "skindie___",
                    "engagement": {"views": 35205},
                    "extras": {"author_name": "Skindie", "lang": "en", "urls": []},
                }
            ],
        },
    }

    posts = iter_posts_from_ledger_record(record)

    assert len(posts) == 1
    assert posts[0].query_id == "en_jp_convenience_snack_question_live"
    assert posts[0].requested_query == "raw chicken japan"


def test_query_profiles_loads_gate_thresholds() -> None:
    profiles = load_query_profiles("config/query_profiles.yml")

    assert profiles["en_jp_food_bridge"].gate_policy.min_views == 20000
    assert profiles["en_europe_affinity_prompt_live"].enabled is False


def test_infer_country_anchor_supports_local_language_queries() -> None:
    policy = load_precision_policy(POLICY_PATH)
    post = SearchPost(
        id="x3",
        text="En Japon, que te gusta mas del desayuno local?",
        author_screen_name="spanish_bridge",
        metrics=TweetMetrics(views=15000, replies=30, quotes=5),
    )

    assert infer_country_anchor(post, policy) is True
    assert infer_cross_country_seed(post, policy) is True


def test_evaluate_ledger_dedupes_posts_and_applies_profile_gate(tmp_path: Path) -> None:
    ledger_path = tmp_path / "evidence.jsonl"
    record = {
        "channel": "twitter",
        "operation": "search",
        "input": "food question japan",
        "query_id": "en_jp_food_bridge",
        "result": {
            "channel": "twitter",
            "operation": "search",
            "items": [
                {
                    "id": "2041126787690934455",
                    "kind": "post",
                    "text": "Japan what should I buy at the convenience store?",
                    "author": "prompt_account",
                    "engagement": {"views": 9000, "replies": 60, "quotes": 6},
                    "extras": {"author_name": "Prompt", "lang": "en", "urls": []},
                }
            ],
        },
    }
    duplicate = {
        **record,
        "query_id": "en_jp_food_bridge",
    }
    ledger_path.write_text(
        "\n".join((json.dumps(record), json.dumps(duplicate))),
        encoding="utf-8",
    )

    summary = evaluate_ledger(ledger_path, POLICY_PATH, Path("config/query_profiles.yml"))

    assert summary["total_posts_seen"] == 2
    assert summary["unique_posts_seen"] == 1
    assert summary["kept_posts"] == 0
    assert summary["drop_reasons"]["below_profile_gate"] == 1
