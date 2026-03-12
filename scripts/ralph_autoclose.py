#!/usr/bin/env python3
"""
Auto-close sidecar for ralph-tui.

Watches `.ralph-tui/session.json` and automatically runs `mark_story_done.py`
for any task that becomes `status=completed` in tracker state.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-mark completed Ralph tasks as done in PRD."
    )
    parser.add_argument("--prd", default="prd.json", help="Path to PRD JSON file.")
    parser.add_argument(
        "--state-dir",
        default=".ralph-tui",
        help="Ralph state directory (contains session.json).",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=20,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--retry-seconds",
        type=int,
        default=300,
        help="Retry delay per failed US (seconds).",
    )
    parser.add_argument(
        "--no-require-origin-main",
        action="store_true",
        help="Forward --no-require-origin-main to mark_story_done.",
    )
    parser.add_argument("--once", action="store_true", help="Run one scan and exit.")
    parser.add_argument("--quiet", action="store_true", help="Reduce sidecar logs.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str, *, quiet: bool = False) -> None:
    if not quiet:
        print(msg, flush=True)


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def load_prd_passes(prd_path: Path) -> dict[str, bool]:
    with prd_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    stories = data.get("userStories")
    if not isinstance(stories, list):
        raise ValueError("Invalid PRD format: userStories must be a list")
    result: dict[str, bool] = {}
    for story in stories:
        if not isinstance(story, dict):
            continue
        us_id = story.get("id")
        if isinstance(us_id, str):
            result[us_id] = bool(story.get("passes") is True)
    return result


def completed_ids_from_session(session: dict[str, Any]) -> set[str]:
    tracker = session.get("trackerState")
    if not isinstance(tracker, dict):
        return set()
    tasks = tracker.get("tasks")
    if not isinstance(tasks, list):
        return set()

    completed: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("status") != "completed":
            continue
        us_id = task.get("id")
        if isinstance(us_id, str) and us_id:
            completed.add(us_id)
    return completed


def run_mark_story_done(
    *,
    us_id: str,
    prd: str,
    project_root: Path,
    no_require_origin_main: bool,
) -> tuple[int, str]:
    mark_script = project_root / "scripts" / "mark_story_done.py"
    completion_notes = (
        f"Auto-marked by ralph_autoclose.py at {utc_now()} "
        "(done gate validated)"
    )
    cmd = [
        sys.executable,
        str(mark_script),
        "--prd",
        prd,
        "--us-id",
        us_id,
        "--completion-notes",
        completion_notes,
    ]
    if no_require_origin_main:
        cmd.append("--no-require-origin-main")

    proc = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "").strip()
    if proc.stderr:
        output = (output + "\n" + proc.stderr.strip()).strip()
    return proc.returncode, output


def scan_once(
    *,
    prd: str,
    state_dir: Path,
    project_root: Path,
    no_require_origin_main: bool,
    retry_after: dict[str, float],
    retry_seconds: int,
    quiet: bool,
) -> None:
    session = load_json(state_dir / "session.json")
    if session is None:
        log(
            f"[ralph_autoclose] Session not found: {state_dir / 'session.json'}",
            quiet=quiet,
        )
        return

    prd_path = (project_root / prd).resolve()
    if not prd_path.exists():
        log(f"[ralph_autoclose] PRD not found: {prd_path}", quiet=quiet)
        return

    try:
        prd_passes = load_prd_passes(prd_path)
    except Exception as exc:  # noqa: BLE001
        log(f"[ralph_autoclose] Failed to read PRD: {exc!r}", quiet=quiet)
        return

    completed_ids = completed_ids_from_session(session)
    candidates = sorted(us_id for us_id in completed_ids if prd_passes.get(us_id) is not True)
    if not candidates:
        return

    now = time.monotonic()
    for us_id in candidates:
        if now < retry_after.get(us_id, 0.0):
            continue

        code, output = run_mark_story_done(
            us_id=us_id,
            prd=prd,
            project_root=project_root,
            no_require_origin_main=no_require_origin_main,
        )
        if code == 0:
            retry_after.pop(us_id, None)
            log(f"[ralph_autoclose] {us_id} marked done automatically.", quiet=quiet)
            continue

        retry_after[us_id] = now + max(1, retry_seconds)
        short = output.splitlines()[0] if output else "unknown error"
        log(
            f"[ralph_autoclose] {us_id} not marked ({short}); retry in {retry_seconds}s.",
            quiet=quiet,
        )


def main() -> int:
    args = parse_args()
    project_root = Path.cwd()
    state_dir = (project_root / args.state_dir).resolve()
    retry_after: dict[str, float] = {}

    log(
        f"[ralph_autoclose] started: prd={args.prd} state_dir={state_dir}",
        quiet=args.quiet,
    )

    try:
        while True:
            scan_once(
                prd=args.prd,
                state_dir=state_dir,
                project_root=project_root,
                no_require_origin_main=args.no_require_origin_main,
                retry_after=retry_after,
                retry_seconds=args.retry_seconds,
                quiet=args.quiet,
            )
            if args.once:
                break
            time.sleep(max(1, args.interval_seconds))
    except KeyboardInterrupt:
        log("[ralph_autoclose] interrupted.", quiet=args.quiet)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
