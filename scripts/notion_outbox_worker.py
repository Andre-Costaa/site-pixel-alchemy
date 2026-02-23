#!/usr/bin/env python3
"""
Process the Notion outbox queue (no MCP required).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import NOTION_OUTBOX_DIR
from notion_client import NotionAPIClient
from notion_sync.worker import NotionWorker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Notion outbox worker.")
    parser.add_argument(
        "--outbox-dir",
        default=str(NOTION_OUTBOX_DIR),
        help="Outbox root directory",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one event and exit",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=1000,
        help="Max iterations (default: 1000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notion = NotionAPIClient()
    worker = NotionWorker(outbox_dir=Path(args.outbox_dir), notion=notion)

    if args.once:
        processed = worker.process_once()
        print("processed" if processed else "idle")
        return 0

    loops = 0
    while loops < args.max_loops:
        loops += 1
        processed = worker.process_once()
        if not processed:
            print("idle")
            return 0

    print("max_loops reached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

