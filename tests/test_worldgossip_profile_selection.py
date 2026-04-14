from pathlib import Path

from worldgossip_twitter import load_query_profile_config
from worldgossip_twitter.selection import (
    QuerySelectionState,
    load_profile_selection_state,
    record_profile_selection,
    save_profile_selection_state,
    select_query_profiles,
)


PROFILE_PATH = Path("config/query_profiles.yml")


def test_profile_config_loads_portfolio_targets_and_new_profiles() -> None:
    config = load_query_profile_config(PROFILE_PATH)

    assert config.portfolio_targets.batch_rules.min_non_jp_profiles == 1
    assert config.portfolio_targets.batch_rules.min_local_bridge_profiles == 1
    assert config.portfolio_targets.batch_rules.min_object_anchor_profiles == 1
    assert config.portfolio_targets.language_lane_mix["local_bridge"] == 0.30
    assert config.profiles["en_anglosphere_word_choice_banter_live"].motif == "object_anchor_banter"
    assert "us" in config.profiles["en_anglosphere_word_choice_banter_live"].country_scope
    assert config.profiles["es_latam_word_choice_banter_explore"].enabled is True


def test_select_query_profiles_balances_portfolio() -> None:
    plan = select_query_profiles(PROFILE_PATH, limit=8)
    selected = list(plan.profiles)

    assert len(selected) == 8
    assert any(profile.portfolio_role == "frontier" for profile in selected)
    assert any(profile.language_lane == "local_bridge" for profile in selected)
    assert any(profile.language_lane == "ja_seed" for profile in selected)
    assert any(profile.motif == "object_anchor_banter" for profile in selected)
    assert any("jp" not in profile.country_scope for profile in selected)
    assert len({profile.topic_bucket for profile in selected}) >= 5

    topic_counts: dict[str, int] = {}
    for profile in selected:
        topic_counts[profile.topic_bucket] = topic_counts.get(profile.topic_bucket, 0) + 1
    assert max(topic_counts.values()) <= 2


def test_selection_state_roundtrip_records_selected_profiles(tmp_path: Path) -> None:
    plan = select_query_profiles(PROFILE_PATH, limit=6)
    updated_state = record_profile_selection(QuerySelectionState(), plan.profiles)

    state_path = tmp_path / "selection-state.json"
    save_profile_selection_state(state_path, updated_state)
    loaded_state = load_profile_selection_state(state_path)

    assert loaded_state.total_runs == 1
    assert loaded_state.profile_counts
    assert loaded_state.language_lane_counts
    assert loaded_state.topic_bucket_counts
    assert loaded_state.cluster_counts
    assert any(count >= 1 for count in loaded_state.profile_counts.values())
