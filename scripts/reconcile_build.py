"""Decide whether the current upstream lock needs another image build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIVE_STATUSES = {"queued", "in_progress", "waiting", "pending", "requested"}
COMPLETED_CONCLUSIONS = {
    "success",
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "stale",
    "startup_failure",
    "skipped",
    "neutral",
}


def run_title(version: str, commit: str) -> str:
    return f"Build WUD {version} ({commit})"


def decide_build(
    version: str,
    commit: str,
    runs: list[dict],
    release_exists: bool | None,
    max_attempts: int = 3,
) -> str:
    """Return dispatch, active, complete, capped, or ambiguous for this lock."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if release_exists is None:
        return "ambiguous"

    title = run_title(version, commit)
    matching = [run for run in runs if run.get("displayTitle") == title]
    if not matching:
        return "complete" if release_exists else "dispatch"

    if any(run.get("status") in ACTIVE_STATUSES for run in matching):
        return "active"
    if any(
        run.get("status") != "completed"
        or run.get("conclusion") not in COMPLETED_CONCLUSIONS
        or not isinstance(run.get("createdAt"), str)
        for run in matching
    ):
        return "ambiguous"
    matching.sort(key=lambda run: run["createdAt"], reverse=True)
    latest = matching[0]
    if latest.get("conclusion") == "success" and release_exists:
        return "complete"
    if len(matching) >= max_attempts:
        return "capped"
    return "dispatch"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--release-exists", choices=("true", "false", "unknown"), required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()

    runs = json.loads(args.runs.read_text(encoding="utf-8"))
    release_exists = {
        "true": True,
        "false": False,
        "unknown": None,
    }[args.release_exists]
    print(decide_build(args.version, args.commit, runs, release_exists, args.max_attempts))


if __name__ == "__main__":
    main()
