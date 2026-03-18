#!/usr/bin/env python3
"""
Backfill US ID on live Notion pages in status "Mensagem Pronta" using unique slug matches from prd.json.

Safe-by-default behavior:
- dry-run/report mode is the default
- writes to Notion only with --apply
- only applies unique slug matches
- uses the local outbox worker for verified updates
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import NOTION_DATABASE_ID, NOTION_OUTBOX_DIR
from notion_client import NotionAPIClient, _extract_simple_value
from notion_sync.outbox import NotionOutbox
from notion_sync.worker import NotionWorker
from reconcile_prd_notion_links import _extract_slug
from prd_store import load_prd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill Notion US ID for pages in 'Mensagem Pronta' using unique slug matches from prd.json."
    )
    parser.add_argument("--prd", default="prd.json", help="Path to PRD JSON")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enqueue and process live Notion updates through the outbox",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional explicit report output path",
    )
    return parser.parse_args()


def _default_report_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path.cwd() / ".sinfonia" / "reports" / f"notion-mensagem-pronta-usid-sync-{stamp}.json"


def _query_mensagem_pronta_pages(client: NotionAPIClient) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {
        "filter": {
            "property": "Status",
            "select": {"equals": "Mensagem Pronta"},
        },
        "page_size": 100,
    }
    pages: list[dict[str, Any]] = []
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    while True:
        data = client._request_json("POST", url, payload)
        pages.extend(data.get("results") or [])
        if not data.get("has_more"):
            return pages
        payload = {
            "filter": {
                "property": "Status",
                "select": {"equals": "Mensagem Pronta"},
            },
            "page_size": 100,
            "start_cursor": data.get("next_cursor"),
        }


def _summarize_page(page: dict[str, Any]) -> dict[str, str]:
    props = page.get("properties") or {}
    return {
        "page_id": page.get("id", ""),
        "nome": _extract_simple_value(props.get("Nome")) or "",
        "status": _extract_simple_value(props.get("Status")) or "",
        "slug": _extract_simple_value(props.get("Slug")) or "",
        "us_id": _extract_simple_value(props.get("US ID")) or "",
        "url_demo": _extract_simple_value(props.get("URL Demo")) or "",
    }


def main() -> int:
    args = parse_args()
    prd = load_prd((Path.cwd() / args.prd).resolve())

    slug_to_stories: dict[str, list[dict[str, str]]] = defaultdict(list)
    for story in prd.get("userStories", []):
        criteria = story.get("acceptanceCriteria") or []
        if not isinstance(criteria, list):
            criteria = []
        slug = _extract_slug(criteria)
        if not slug:
            continue
        slug_to_stories[slug].append(
            {
                "us_id": story.get("id", ""),
                "title": story.get("title", ""),
                "notionPageId": story.get("notionPageId", ""),
            }
        )

    notion = NotionAPIClient()
    pages = [_summarize_page(page) for page in _query_mensagem_pronta_pages(notion)]
    outbox = NotionOutbox(NOTION_OUTBOX_DIR)
    worker = NotionWorker(outbox_dir=NOTION_OUTBOX_DIR, notion=notion) if args.apply else None

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry-run",
        "summary": {
            "pages_scanned": 0,
            "pages_with_us_id": 0,
            "pages_missing_us_id": 0,
            "unique_slug_matches": 0,
            "duplicate_slug_matches": 0,
            "no_prd_match": 0,
            "updated": 0,
        },
        "already_filled": [],
        "eligible_updates": [],
        "duplicate_slug_matches": [],
        "no_prd_match": [],
    }

    for page in pages:
        report["summary"]["pages_scanned"] += 1
        if page["us_id"]:
            report["summary"]["pages_with_us_id"] += 1
            report["already_filled"].append(page)
            continue

        report["summary"]["pages_missing_us_id"] += 1
        slug = page["slug"]
        matches = slug_to_stories.get(slug, []) if slug else []

        if len(matches) == 1:
            match = matches[0]
            report["summary"]["unique_slug_matches"] += 1
            entry = {
                **page,
                "matched_story": match,
                "properties": {"US ID": match["us_id"]},
            }
            report["eligible_updates"].append(entry)
            if args.apply:
                outbox.enqueue_update_page_properties(
                    us_id=match["us_id"],
                    page_id=page["page_id"],
                    properties={"US ID": match["us_id"]},
                    verify_after_write=True,
                )
                report["summary"]["updated"] += 1
            continue

        if len(matches) > 1:
            report["summary"]["duplicate_slug_matches"] += 1
            report["duplicate_slug_matches"].append(
                {
                    **page,
                    "matches": matches,
                }
            )
            continue

        report["summary"]["no_prd_match"] += 1
        report["no_prd_match"].append(page)

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
