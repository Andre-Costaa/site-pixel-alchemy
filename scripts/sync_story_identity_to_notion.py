#!/usr/bin/env python3
"""
Sync identity fields from PRD stories to linked Notion pages.

Safe-by-default behavior:
- dry-run/report mode is the default
- writes to Notion only with --apply
- uses the local outbox worker for receipts and read-after-write verification
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import NOTION_OUTBOX_DIR
from notion_client import NotionAPIClient, _extract_simple_value
from notion_sync.outbox import NotionOutbox
from notion_sync.worker import NotionWorker
from prd_store import load_prd

SITE_RE = re.compile(r"site-demo/([^'/\s]+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Slug and US ID from prd.json stories to linked Notion pages."
    )
    parser.add_argument("--prd", default="prd.json", help="Path to PRD JSON")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enqueue and process live Notion updates through the outbox",
    )
    parser.add_argument(
        "--us-id",
        action="append",
        default=[],
        help="Restrict sync to one or more user stories",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional explicit report output path",
    )
    return parser.parse_args()


def _extract_slug(criteria: list[str]) -> str:
    for item in criteria:
        if not isinstance(item, str):
            continue
        match = SITE_RE.search(item)
        if match:
            return match.group(1)
    return ""


def _requires_notion(criteria: list[str]) -> bool:
    return any(
        isinstance(item, str) and "Atualizar Notion" in item for item in criteria
    )


def _query_page(client: NotionAPIClient, page_id: str) -> dict[str, Any]:
    page = client.fetch_page(page_id)
    props = page.get("properties") or {}
    return {
        "page_id": page.get("id", ""),
        "nome": _extract_simple_value(props.get("Nome")) or "",
        "status": _extract_simple_value(props.get("Status")) or "",
        "slug": _extract_simple_value(props.get("Slug")) or "",
        "us_id": _extract_simple_value(props.get("US ID")) or "",
    }


def _default_report_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path.cwd() / ".sinfonia" / "reports" / f"notion-story-identity-sync-{stamp}.json"


def main() -> int:
    args = parse_args()
    prd = load_prd((Path.cwd() / args.prd).resolve())
    filter_ids = set(args.us_id or [])
    notion = NotionAPIClient()
    outbox = NotionOutbox(NOTION_OUTBOX_DIR)

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry-run",
        "summary": {
            "stories_scanned": 0,
            "stories_requiring_notion": 0,
            "pages_checked": 0,
            "already_synced": 0,
            "eligible_updates": 0,
            "updated": 0,
            "missing_page_id": 0,
            "missing_slug": 0,
        },
        "already_synced": [],
        "eligible_updates": [],
        "missing_page_id": [],
        "missing_slug": [],
    }

    worker = NotionWorker(outbox_dir=NOTION_OUTBOX_DIR, notion=notion) if args.apply else None

    for story in prd.get("userStories", []):
        us_id = story.get("id", "")
        if filter_ids and us_id not in filter_ids:
            continue

        report["summary"]["stories_scanned"] += 1
        criteria = story.get("acceptanceCriteria") or []
        if not isinstance(criteria, list):
            criteria = []
        if not _requires_notion(criteria):
            continue

        report["summary"]["stories_requiring_notion"] += 1
        page_id = (story.get("notionPageId") or "").strip()
        slug = _extract_slug(criteria)

        if not page_id:
            report["summary"]["missing_page_id"] += 1
            report["missing_page_id"].append({"us_id": us_id, "title": story.get("title", "")})
            continue
        if not slug:
            report["summary"]["missing_slug"] += 1
            report["missing_slug"].append({"us_id": us_id, "title": story.get("title", ""), "page_id": page_id})
            continue

        page = _query_page(notion, page_id)
        report["summary"]["pages_checked"] += 1

        properties: dict[str, str] = {}
        if page.get("slug") != slug:
            properties["Slug"] = slug
        if page.get("us_id") != us_id:
            properties["US ID"] = us_id

        entry = {
            "us_id": us_id,
            "title": story.get("title", ""),
            "page_id": page_id,
            "story_slug": slug,
            "page_slug": page.get("slug", ""),
            "page_us_id": page.get("us_id", ""),
            "page_status": page.get("status", ""),
            "properties": properties,
        }

        if not properties:
            report["summary"]["already_synced"] += 1
            report["already_synced"].append(entry)
            continue

        report["summary"]["eligible_updates"] += 1
        report["eligible_updates"].append(entry)

        if args.apply:
            outbox.enqueue_update_page_properties(
                us_id=us_id,
                page_id=page_id,
                properties=properties,
                verify_after_write=True,
            )
            report["summary"]["updated"] += 1

    if args.apply and worker is not None:
        worker.process_once()

    report_path = Path(args.report_file).resolve() if args.report_file else _default_report_path()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"mode={report['mode']}")
    print(f"report={report_path}")
    for key, value in report["summary"].items():
        print(f"{key}={value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
