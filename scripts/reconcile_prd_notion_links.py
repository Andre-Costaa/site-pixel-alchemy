#!/usr/bin/env python3
"""
Reconcile PRD stories with live Notion pages using slug matches.

Safe-by-default behavior:
- dry-run/report mode is the default
- writes to prd.json only with --apply
- only applies unique, deterministic slug matches
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT, NOTION_DATABASE_ID
from notion_client import NotionAPIClient, _extract_simple_value
from prd_store import load_prd, save_prd

SITE_RE = re.compile(r"site-demo/([^'/\s]+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile notionPageId links in prd.json using live Notion slug matches."
    )
    parser.add_argument("--prd", default="prd.json", help="Path to PRD JSON")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write notionPageId into PRD for unique safe matches",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional explicit report output path (default: .sinfonia/reports/...json)",
    )
    parser.add_argument(
        "--us-id",
        action="append",
        default=[],
        help="Restrict reconciliation to one or more user stories",
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


def _query_all_pages(client: NotionAPIClient) -> list[dict[str, Any]]:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload: dict[str, Any] = {"page_size": 100}
    pages: list[dict[str, Any]] = []
    while True:
        data = client._request_json("POST", url, payload)
        pages.extend(data.get("results") or [])
        if not data.get("has_more"):
            return pages
        payload = {"page_size": 100, "start_cursor": data.get("next_cursor")}


def _summarize_page(page: dict[str, Any]) -> dict[str, str]:
    props = page.get("properties") or {}
    return {
        "page_id": page.get("id", ""),
        "nome": _extract_simple_value(props.get("Nome")) or "",
        "status": _extract_simple_value(props.get("Status")) or "",
        "slug": _extract_simple_value(props.get("Slug")) or "",
        "us_id": _extract_simple_value(props.get("US ID")) or "",
        "url_demo": _extract_simple_value(props.get("URL Demo")) or "",
        "site_criado_em": _extract_simple_value(props.get("Site Criado Em")) or "",
    }


def _default_report_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return PROJECT_ROOT / ".sinfonia" / "reports" / f"notion-prd-reconcile-{stamp}.json"


def main() -> int:
    args = parse_args()
    prd_path = (Path.cwd() / args.prd).resolve()
    prd = load_prd(prd_path)
    filter_ids = set(args.us_id or [])

    client = NotionAPIClient()
    pages = [_summarize_page(page) for page in _query_all_pages(client)]

    pages_by_slug: dict[str, list[dict[str, str]]] = defaultdict(list)
    pages_by_id = {}
    for page in pages:
        pages_by_id[page["page_id"]] = page
        if page["slug"]:
            pages_by_slug[page["slug"]].append(page)

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry-run",
        "summary": {
            "stories_scanned": 0,
            "stories_requiring_notion": 0,
            "stories_missing_notion_page_id": 0,
            "safe_matches_found": 0,
            "updated": 0,
            "already_linked": 0,
            "missing_slug": 0,
            "missing_notion_match": 0,
            "duplicate_slug_in_notion": 0,
            "page_id_slug_conflict": 0,
        },
        "safe_matches": [],
        "already_linked": [],
        "missing_slug": [],
        "missing_notion_match": [],
        "duplicate_slug_in_notion": [],
        "page_id_slug_conflict": [],
        "skipped_not_required": [],
    }

    updated = 0

    for story in prd.get("userStories", []):
        us_id = story.get("id", "")
        if filter_ids and us_id not in filter_ids:
            continue

        report["summary"]["stories_scanned"] += 1
        criteria = story.get("acceptanceCriteria") or []
        if not isinstance(criteria, list):
            criteria = []
        requires_notion = _requires_notion(criteria)
        slug = _extract_slug(criteria)
        notion_page_id = (story.get("notionPageId") or "").strip()

        if not requires_notion:
            report["skipped_not_required"].append(
                {"us_id": us_id, "title": story.get("title", ""), "slug": slug}
            )
            continue

        report["summary"]["stories_requiring_notion"] += 1

        if not slug:
            report["summary"]["missing_slug"] += 1
            report["missing_slug"].append(
                {"us_id": us_id, "title": story.get("title", ""), "notionPageId": notion_page_id}
            )
            continue

        slug_matches = pages_by_slug.get(slug, [])

        if notion_page_id:
            page = pages_by_id.get(notion_page_id)
            if page and page.get("slug") == slug:
                report["summary"]["already_linked"] += 1
                report["already_linked"].append(
                    {
                        "us_id": us_id,
                        "title": story.get("title", ""),
                        "slug": slug,
                        "notionPageId": notion_page_id,
                        "notion_status": page.get("status", ""),
                        "notion_us_id": page.get("us_id", ""),
                    }
                )
                continue

            report["summary"]["page_id_slug_conflict"] += 1
            report["page_id_slug_conflict"].append(
                {
                    "us_id": us_id,
                    "title": story.get("title", ""),
                    "slug": slug,
                    "notionPageId": notion_page_id,
                    "linked_page": page,
                    "slug_matches": slug_matches,
                }
            )
            continue

        report["summary"]["stories_missing_notion_page_id"] += 1

        if not slug_matches:
            report["summary"]["missing_notion_match"] += 1
            report["missing_notion_match"].append(
                {"us_id": us_id, "title": story.get("title", ""), "slug": slug}
            )
            continue

        if len(slug_matches) > 1:
            report["summary"]["duplicate_slug_in_notion"] += 1
            report["duplicate_slug_in_notion"].append(
                {
                    "us_id": us_id,
                    "title": story.get("title", ""),
                    "slug": slug,
                    "candidates": slug_matches,
                }
            )
            continue

        match = slug_matches[0]
        entry = {
            "us_id": us_id,
            "title": story.get("title", ""),
            "slug": slug,
            "notionPageId": match["page_id"],
            "notion_name": match["nome"],
            "notion_status": match["status"],
            "notion_us_id": match["us_id"],
        }
        report["summary"]["safe_matches_found"] += 1
        report["safe_matches"].append(entry)

        if args.apply:
            story["notionPageId"] = match["page_id"]
            updated += 1

    if args.apply and updated:
        save_prd(prd, prd_path)
    report["summary"]["updated"] = updated

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
