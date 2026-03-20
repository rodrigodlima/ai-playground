#!/usr/bin/env python3
"""
parse_session.py

Finds and parses the most recent Claude Code session JSONL file created
AFTER a given Unix timestamp. Returns token usage as JSON to stdout.

Usage:
    python scripts/parse_session.py --after <unix_timestamp_seconds>
    python scripts/parse_session.py --after 1710000000

Output (JSON):
    {
      "session_file": "/home/user/.claude/projects/.../abc.jsonl",
      "input_tokens": 512,
      "output_tokens": 4,
      "cache_creation_tokens": 508,
      "cache_read_tokens": 0,
      "total_tokens": 516,
      "message_count": 2
    }
"""

import argparse
import json
import os
import sys
from pathlib import Path


def find_claude_dir() -> Path:
    """Locate ~/.claude/projects regardless of OS."""
    home = Path.home()
    candidate = home / ".claude" / "projects"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Claude projects directory not found at {candidate}.\n"
        "Make sure Claude Code has been run at least once."
    )


def find_session_after(claude_projects: Path, after_ts: float) -> Path | None:
    """Return the JSONL file created/modified after `after_ts` (epoch seconds)."""
    candidates = []
    for jsonl in claude_projects.rglob("*.jsonl"):
        mtime = jsonl.stat().st_mtime
        if mtime > after_ts:
            candidates.append((mtime, jsonl))

    if not candidates:
        return None

    # Most recently modified first
    candidates.sort(reverse=True)
    return candidates[0][1]


def parse_usage(session_file: Path) -> dict:
    """Sum all usage blocks in a JSONL session file."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "message_count": 0,
    }

    with open(session_file, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            usage = entry.get("usage") or entry.get("message", {}).get("usage", {})
            if not usage:
                continue

            totals["input_tokens"]          += usage.get("input_tokens", 0)
            totals["output_tokens"]         += usage.get("output_tokens", 0)
            totals["cache_creation_tokens"] += usage.get("cache_creation_input_tokens", 0)
            totals["cache_read_tokens"]     += usage.get("cache_read_input_tokens", 0)
            totals["message_count"]         += 1

    totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Claude Code session tokens")
    parser.add_argument(
        "--after",
        type=float,
        required=True,
        help="Unix timestamp (seconds). Only sessions newer than this are considered.",
    )
    args = parser.parse_args()

    try:
        claude_dir = find_claude_dir()
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    session_file = find_session_after(claude_dir, args.after)

    if session_file is None:
        print(json.dumps({"error": "No session file found after the given timestamp."}))
        sys.exit(1)

    result = parse_usage(session_file)
    result["session_file"] = str(session_file)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
