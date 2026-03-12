"""
Pixel Alchemy — Notion Dedup Guard
====================================

Anti-duplicate validation for the prospect pipeline.

Checks the Notion CRM database for existing records before creating new
ones, preventing duplicate entries by name or slug.

Usage (CLI):
    python3 scripts/notion_dedup_guard.py --check-name "Dra. Laura Sanches"
    python3 scripts/notion_dedup_guard.py --check-slug "dra-laura-sanches"

Usage (import):
    from notion_dedup_guard import check_duplicate, check_slug_duplicate
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from config import NOTION_DATABASE_ID, SITE_DEMO_DIR
from notion_client import NotionAPIClient, NotionAPIError, _extract_simple_value


def _normalize_for_comparison(text: str) -> str:
    """Normalize a string for case-insensitive, accent-insensitive comparison."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return " ".join(stripped.lower().split())


def _extract_page_summary(page: dict[str, Any]) -> dict[str, Any]:
    """Extract a summary dict from a raw Notion page object."""
    props = page.get("properties") or {}
    summary: dict[str, Any] = {
        "page_id": page.get("id", ""),
    }

    for field_name in ("Nome", "Slug", "Status", "Nicho", "US ID", "URL Demo", "Telefone"):
        prop_obj = props.get(field_name)
        if prop_obj is not None:
            summary[field_name] = _extract_simple_value(prop_obj)

    return summary


def check_duplicate(nome: str, *, client: NotionAPIClient | None = None) -> dict[str, Any] | None:
    """Query the Notion database for a record matching the given name.

    Comparison is case-insensitive and accent-insensitive.

    Args:
        nome: The prospect/business name to search for.
        client: Optional pre-configured NotionAPIClient instance.

    Returns:
        A summary dict of the existing record if found, None otherwise.
    """
    if client is None:
        client = NotionAPIClient()

    normalized_query = _normalize_for_comparison(nome)
    if not normalized_query:
        return None

    # Query database filtering by title property (Nome).
    # Notion's title filter is case-insensitive but we do an extra local check
    # to handle accent variations.
    payload = {
        "filter": {
            "property": "Nome",
            "title": {"equals": nome},
        },
    }

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    try:
        result = client._request_json("POST", url, payload)
    except NotionAPIError:
        # Fall back to a broader contains search if exact match fails.
        result = {"results": []}

    # Check exact match results first.
    for page in result.get("results") or []:
        props = page.get("properties") or {}
        nome_prop = props.get("Nome")
        actual_name = _extract_simple_value(nome_prop) or ""
        if _normalize_for_comparison(actual_name) == normalized_query:
            return _extract_page_summary(page)

    # If no exact match, try a broader contains filter for partial/accent mismatches.
    payload_contains = {
        "filter": {
            "property": "Nome",
            "title": {"contains": nome.split()[0] if nome.strip() else nome},
        },
    }

    try:
        result_broad = client._request_json("POST", url, payload_contains)
    except NotionAPIError:
        return None

    for page in result_broad.get("results") or []:
        props = page.get("properties") or {}
        nome_prop = props.get("Nome")
        actual_name = _extract_simple_value(nome_prop) or ""
        if _normalize_for_comparison(actual_name) == normalized_query:
            return _extract_page_summary(page)

    return None


def check_slug_duplicate(slug: str, *, client: NotionAPIClient | None = None) -> bool:
    """Check if a slug already exists in the Notion database or on disk.

    Args:
        slug: The URL slug to check (e.g., "dra-laura-sanches").
        client: Optional pre-configured NotionAPIClient instance.

    Returns:
        True if the slug is already in use, False otherwise.
    """
    if not slug:
        return False

    # Check filesystem first (fast).
    site_dir = SITE_DEMO_DIR / slug
    if site_dir.exists() and site_dir.is_dir():
        return True

    # Check Notion database.
    if client is None:
        client = NotionAPIClient()

    payload = {
        "filter": {
            "property": "Slug",
            "rich_text": {"equals": slug},
        },
    }

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    try:
        result = client._request_json("POST", url, payload)
    except NotionAPIError:
        # If API fails, at least we checked the filesystem above.
        return False

    results = result.get("results") or []
    return len(results) > 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Notion dedup guard — check for duplicate prospects",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check-name",
        metavar="NAME",
        help="Check if a prospect name already exists in Notion",
    )
    group.add_argument(
        "--check-slug",
        metavar="SLUG",
        help="Check if a slug already exists in Notion or site-demo/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be checked without making API calls",
    )

    args = parser.parse_args()

    if args.dry_run:
        if args.check_name:
            normalized = _normalize_for_comparison(args.check_name)
            print(f"[DRY RUN] Would check Notion for name: {args.check_name!r}")
            print(f"[DRY RUN] Normalized form: {normalized!r}")
        elif args.check_slug:
            site_dir = SITE_DEMO_DIR / args.check_slug
            print(f"[DRY RUN] Would check slug: {args.check_slug!r}")
            print(f"[DRY RUN] Directory path: {site_dir}")
            print(f"[DRY RUN] Directory exists: {site_dir.exists()}")
        return

    if args.check_name:
        print(f"Checking for duplicate: {args.check_name!r} ...")
        result = check_duplicate(args.check_name)
        if result is not None:
            print(f"DUPLICATE FOUND:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)
        else:
            print("No duplicate found. Name is available.")
            sys.exit(0)

    elif args.check_slug:
        print(f"Checking slug: {args.check_slug!r} ...")
        is_dup = check_slug_duplicate(args.check_slug)
        if is_dup:
            site_dir = SITE_DEMO_DIR / args.check_slug
            sources = []
            if site_dir.exists():
                sources.append("filesystem")
            sources.append("notion")  # If we got here, at least one source matched.
            print(f"SLUG IN USE (checked: {', '.join(sources)})")
            sys.exit(1)
        else:
            print("Slug is available.")
            sys.exit(0)


if __name__ == "__main__":
    main()
