#!/usr/bin/env python3
"""
Safe marker for PRD stories.

Marks `passes=true` only if done gate checks pass.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from done_gate import US_RE, evaluate_story
from prd_store import load_prd, save_prd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mark a PRD story as done only after done-gate validation."
    )
    parser.add_argument("--us-id", required=True, help="Story ID, e.g. US-090")
    parser.add_argument("--prd", default="tasks/prd.json", help="Path to prd.json")
    parser.add_argument(
        "--completion-notes",
        default="Completed by agent (done gate validated)",
        help="Value to write in completionNotes",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes to write in story.notes",
    )
    parser.add_argument(
        "--no-require-origin-main",
        action="store_true",
        help="Allow marking done even if commit is not on origin/main yet",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not US_RE.match(args.us_id):
        print(f"Invalid US ID: {args.us_id}")
        return 2

    cwd = Path.cwd()
    prd_path = (cwd / args.prd).resolve()
    prd = load_prd(prd_path)

    result = evaluate_story(
        prd=prd,
        us_id=args.us_id,
        cwd=cwd,
        require_origin_main=not args.no_require_origin_main,
    )
    if not result["passed"]:
        print(f"DONE GATE failed for {args.us_id}. Story not marked as done.")
        for check in result["checks"]:
            if not check["passed"]:
                print(f"- {check['name']}: {check['detail']}")
        return 1

    story = None
    for item in prd["userStories"]:
        if isinstance(item, dict) and item.get("id") == args.us_id:
            story = item
            break

    if story is None:
        print(f"Story not found in PRD: {args.us_id}")
        return 1

    story["passes"] = True
    story["completionNotes"] = args.completion_notes
    if args.notes:
        story["notes"] = args.notes

    prd.setdefault("metadata", {})
    prd["metadata"]["updatedAt"] = datetime.now(timezone.utc).isoformat()

    save_prd(prd, prd_path)

    print(f"{args.us_id} marked as done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
