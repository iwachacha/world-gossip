"""Run a bounded Agent Reach Twitter evaluation pass from query profiles."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from .evaluate import evaluate_ledger
from .profiles import load_query_profiles
from .selection import (
    load_profile_selection_state,
    record_profile_selection,
    save_profile_selection_state,
    select_query_profiles,
)


def _load_profiles(path: Path) -> list[dict]:
    profiles = load_query_profiles(path)
    enabled_profiles = [profile for profile in profiles.values() if profile.enabled]
    enabled_profiles.sort(key=lambda profile: (profile.priority, profile.id), reverse=True)
    return [
        {
            "id": profile.id,
            "query_template": profile.query_template,
            "window_hours": profile.window_hours,
            "discovery_limit": profile.discovery_limit,
        }
        for profile in enabled_profiles
    ]


def _since_date(until: date, window_hours: int) -> date:
    days = max(1, (window_hours + 23) // 24)
    return until - timedelta(days=days)


def _run_collect(profile: dict, *, until: date, save_dir: Path, run_id: str, limit_cap: int | None) -> None:
    window_hours = int(profile.get("window_hours") or 168)
    since = _since_date(until, window_hours).isoformat()
    limit = int(profile.get("discovery_limit") or 16)
    if limit_cap is not None:
        limit = min(limit, limit_cap)

    command = [
        "agent-reach",
        "collect",
        "--channel",
        "twitter",
        "--operation",
        "search",
        "--input",
        str(profile["query_template"]),
        "--since",
        since,
        "--until",
        until.isoformat(),
        "--limit",
        str(limit),
        "--item-text-mode",
        "snippet",
        "--item-text-max-chars",
        "560",
        "--raw-mode",
        "minimal",
        "--save-dir",
        str(save_dir),
        "--run-id",
        run_id,
        "--intent",
        "precision_eval",
        "--query-id",
        str(profile["id"]),
        "--source-role",
        "search_result",
        "--json",
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded Agent Reach evaluation pass.")
    parser.add_argument("--profiles", default="config/query_profiles.yml")
    parser.add_argument("--policy", default="config/twitter_precision_policy.yml")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-profiles", type=int, default=8)
    parser.add_argument("--limit-cap", type=int, default=16)
    parser.add_argument("--until", default=str(date.today()))
    parser.add_argument("--selection-mode", choices=("auto", "ordered"), default="auto")
    parser.add_argument("--selection-state", default=".agent-reach/profile-selection-state.json")
    parser.add_argument("--include-guarded", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    shards_dir = output_dir / "shards"
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir.mkdir(parents=True, exist_ok=True)

    profile_path = Path(args.profiles)
    selected_profiles_for_state = []
    if args.selection_mode == "auto":
        selection_state = load_profile_selection_state(Path(args.selection_state))
        selection_plan = select_query_profiles(
            profile_path,
            limit=args.max_profiles,
            state=selection_state,
            include_guarded=args.include_guarded,
        )
        output_dir.joinpath("selection.json").write_text(
            json.dumps(selection_plan.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        profiles = [
            {
                "id": profile.id,
                "query_template": profile.query_template,
                "window_hours": profile.window_hours,
                "discovery_limit": profile.discovery_limit,
            }
            for profile in selection_plan.profiles
        ]
        selected_profiles_for_state = list(selection_plan.profiles)
    else:
        profiles = _load_profiles(profile_path)[: args.max_profiles]
    until = date.fromisoformat(args.until)
    run_id = f"worldgossip-precision-eval-{until.isoformat()}"

    for profile in profiles:
        _run_collect(
            profile,
            until=until,
            save_dir=shards_dir,
            run_id=run_id,
            limit_cap=args.limit_cap,
        )

    merge_command = [
        "agent-reach",
        "ledger",
        "merge",
        "--input",
        str(shards_dir),
        "--output",
        str(output_dir / "evidence.jsonl"),
        "--json",
    ]
    subprocess.run(merge_command, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

    summary = evaluate_ledger(output_dir / "evidence.jsonl", Path(args.policy), profile_path)
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.selection_mode == "auto":
        updated_state = record_profile_selection(
            load_profile_selection_state(Path(args.selection_state)),
            selected_profiles_for_state,
        )
        save_profile_selection_state(Path(args.selection_state), updated_state)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"summary_path={output_dir / 'summary.json'}")
    print(f"records={summary['total_records']} unique_posts={summary['unique_posts_seen']}")
    print(f"kept={summary['kept_posts']} dropped={summary['dropped_posts']} keep_rate={summary['keep_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
