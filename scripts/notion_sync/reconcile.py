from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

# Allow running as `python3 scripts/notion_sync/reconcile.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from notion_sync.outbox import NotionOutbox
from notion_sync.store import read_json


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Notion outbox state.")
    parser.add_argument(
        "--outbox-dir",
        default=".notion-outbox",
        help="Outbox root directory (default: .notion-outbox)",
    )
    parser.add_argument(
        "--stale-minutes",
        type=int,
        default=60,
        help="Report queue events older than this (default: 60)",
    )
    args = parser.parse_args()

    outbox = NotionOutbox(Path(args.outbox_dir))
    queue = sorted(outbox.queue_dir.glob("*.json"))
    processing = sorted(outbox.processing_dir.glob("*.json"))
    dead = sorted(outbox.dead_letter_dir.glob("*.json"))

    print(f"queue={len(queue)} processing={len(processing)} dead_letter={len(dead)}")

    cutoff = _utc_now().timestamp() - (args.stale_minutes * 60)
    stale = []
    for p in queue:
        payload = read_json(p)
        created_at = datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00")).timestamp()
        if created_at < cutoff:
            stale.append((p, payload.get("us_id"), payload.get("attempts", 0), payload.get("last_error")))

    if stale:
        print("\nStale queue events:")
        for p, us_id, attempts, last_error in stale:
            print(f"- {p.name} us_id={us_id} attempts={attempts} last_error={last_error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
