"""
Pixel Alchemy — Notion Client Wrapper
=======================================

Abstraction layer for Notion CRM operations.

When running inside Claude Code, these functions describe the MCP tool calls
to make.

When running standalone (no MCP), use `NotionAPIClient` which talks directly
to the Notion REST API with bounded retries and optional read-after-write
verification.

Usage within Claude Code (MCP):
    - get_prospects_by_status() → use notion-search with data_source_url filter
    - update_prospect() → use notion-update-page with update_properties command
    - create_prospect() → use notion-create-pages with data_source_id parent

Usage standalone (requires NOTION_TOKEN env var):
    NOTION_TOKEN=secret_xxx python3 scripts/notion_client.py
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from config import NOTION_DATA_SOURCE_ID, NOTION_DATABASE_ID


def mcp_search_prospects(query: str) -> dict:
    """Generate MCP tool call for notion-search."""
    return {
        "tool": "mcp__plugin_Notion_notion__notion-search",
        "params": {
            "query": query,
            "data_source_url": f"collection://{NOTION_DATA_SOURCE_ID}",
        },
    }


def mcp_fetch_prospect(page_id: str) -> dict:
    """Generate MCP tool call for notion-fetch."""
    return {
        "tool": "mcp__plugin_Notion_notion__notion-fetch",
        "params": {"id": page_id},
    }


def mcp_update_prospect(page_id: str, properties: dict) -> dict:
    """Generate MCP tool call for notion-update-page.

    Args:
        page_id: Notion page UUID (with or without dashes)
        properties: Dict of property names to values. Special formats:
            - Date: use "date:Field Name:start", "date:Field Name:is_datetime"
            - URL fields named "url"/"id": prefix with "userDefined:"
            - Numbers: use Python numbers
    """
    return {
        "tool": "mcp__plugin_Notion_notion__notion-update-page",
        "params": {
            "data": {
                "page_id": page_id,
                "command": "update_properties",
                "properties": properties,
            }
        },
    }


def mcp_create_prospect(properties: dict) -> dict:
    """Generate MCP tool call for notion-create-pages.

    Args:
        properties: Dict with at minimum "Nome" (title field).
            Common fields: Nome, Nicho, Status, Telefone, Endereço,
            URL Demo, Slug, userDefined:ID, Origem
    """
    return {
        "tool": "mcp__plugin_Notion_notion__notion-create-pages",
        "params": {
            "parent": {
                "data_source_id": NOTION_DATA_SOURCE_ID,
            },
            "pages": [{"properties": properties}],
        },
    }


def build_site_ready_update(
    page_id: str,
    slug: str,
    us_id: str,
    url_demo: str,
    site_created_date: str,
    mensagem: str = "",
) -> dict:
    """Build the MCP update call for after a site is created.

    Sets: Status → "Mensagem Pronta", URL Demo, Slug, US ID, Mensagem, Site Criado Em
    """
    properties = {
        "Status": "Mensagem Pronta",
        "URL Demo": url_demo,
        "Slug": slug,
        "US ID": us_id,
        "date:Site Criado Em:start": site_created_date,
        "date:Site Criado Em:is_datetime": 0,
    }

    # Add message if provided
    if mensagem:
        properties["Mensagem"] = mensagem

    return mcp_update_prospect(page_id, properties)


def build_site_in_progress_update(page_id: str) -> dict:
    """Build the MCP update call when site creation starts."""
    return mcp_update_prospect(page_id, {"Status": "Site em Criação"})


def print_mcp_call(call: dict) -> None:
    """Pretty-print an MCP tool call for debugging."""
    print(json.dumps(call, indent=2, ensure_ascii=False))


class NotionAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class NotionAPIClient:
    """
    Minimal Notion REST client with bounded retries for operational use.

    This intentionally supports the subset of operations needed by the workflow:
    - update page properties (simple contract)
    - fetch page and verify properties (read-after-write)
    """

    def __init__(
        self,
        *,
        token: str | None = None,
        notion_version: str = "2022-06-28",
        timeout_seconds: float = 20.0,
        max_attempts: int = 6,
        sleep_fn=time.sleep,
        rand_fn=random.random,
    ) -> None:
        self.token = token or os.environ.get("NOTION_TOKEN", "")
        self.notion_version = notion_version or os.environ.get("NOTION_API_VERSION", "2022-06-28")
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.sleep_fn = sleep_fn
        self.rand_fn = rand_fn

        if not self.token:
            raise ValueError("Missing NOTION_TOKEN for standalone Notion API client")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request_json(self, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                req = urllib.request.Request(url, data=body, method=method)
                for k, v in self._headers().items():
                    req.add_header(k, v)

                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
                status = getattr(e, "code", None)

                # Non-retryable client errors.
                if status in (400, 401, 403, 404):
                    raise NotionAPIError("Notion API request failed (non-retryable)", status_code=status, body=raw)

                retry_after = None
                if status == 429:
                    retry_after = e.headers.get("Retry-After")
                    try:
                        retry_after = float(retry_after) if retry_after is not None else None
                    except ValueError:
                        retry_after = None

                retryable = status in (409, 429, 500, 502, 503, 504)
                if not retryable:
                    raise NotionAPIError("Notion API request failed", status_code=status, body=raw)

                last_error = NotionAPIError("Notion API request failed (retryable)", status_code=status, body=raw)

                if attempt >= self.max_attempts:
                    raise last_error

                delay = retry_after if retry_after is not None else self._backoff_seconds(attempt)
                self.sleep_fn(delay)
            except urllib.error.URLError as e:
                last_error = e
                if attempt >= self.max_attempts:
                    raise NotionAPIError("Notion API request failed (network)", body=repr(e))
                self.sleep_fn(self._backoff_seconds(attempt))

        raise NotionAPIError("Notion API request failed", body=repr(last_error))

    def _backoff_seconds(self, attempt: int) -> float:
        # Exponential backoff with jitter, bounded.
        base = 0.8 * (2 ** min(attempt, 6))
        jitter = self.rand_fn() * 0.25 * base
        return min(20.0, base + jitter)

    def fetch_page(self, page_id: str) -> dict[str, Any]:
        return self._request_json("GET", f"https://api.notion.com/v1/pages/{page_id}")

    def query_database_by_status(self, status: str, database_id: str = NOTION_DATABASE_ID) -> dict[str, Any]:
        payload = {
            "filter": {
                "property": "Status",
                "select": {"equals": status},
            }
        }
        return self._request_json("POST", f"https://api.notion.com/v1/databases/{database_id}/query", payload)

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        payload = {"properties": properties}
        return self._request_json("PATCH", f"https://api.notion.com/v1/pages/{page_id}", payload)

    def update_page_simple(self, *, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        normalized = _normalize_simple_properties(properties)
        encoded = _encode_simple_properties_for_notion(normalized)
        return self.update_page(page_id, encoded)

    def verify_page_simple(self, *, page_id: str, expected_properties: dict[str, Any]) -> bool:
        normalized_expected = _normalize_simple_properties(expected_properties)
        page = self.fetch_page(page_id)
        props = page.get("properties") or {}
        if not isinstance(props, dict):
            return False

        for name, expected in normalized_expected.items():
            if name not in props:
                return False
            actual = _extract_simple_value(props.get(name))
            if actual is None:
                return False

            # Normalize whitespace in rich text comparisons.
            if isinstance(expected, str) and isinstance(actual, str):
                if " ".join(expected.split()) != " ".join(actual.split()):
                    return False
            else:
                if actual != expected:
                    return False
        return True


def _normalize_simple_properties(properties: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    date_fields: dict[str, dict[str, Any]] = {}

    for key, value in (properties or {}).items():
        if not isinstance(key, str):
            continue

        if key.startswith("date:"):
            rest = key[len("date:") :]
            if ":" in rest:
                field, sub = rest.rsplit(":", 1)
                date_fields.setdefault(field, {})
                date_fields[field][sub] = value
                continue

        name = key
        if name.startswith("userDefined:"):
            name = name.split(":", 1)[1]
        out[name] = value

    for field, data in date_fields.items():
        # Our minimal contract is date-only for this workflow.
        start = data.get("start")
        if start:
            out[field] = start

    return out


def _encode_rich_text(value: str) -> dict[str, Any]:
    if not value:
        return {"rich_text": []}
    return {
        "rich_text": [
            {
                "type": "text",
                "text": {"content": value},
            }
        ]
    }


def _encode_simple_properties_for_notion(properties: dict[str, Any]) -> dict[str, Any]:
    encoded: dict[str, Any] = {}
    for name, value in properties.items():
        if name == "Status":
            encoded[name] = {"select": {"name": str(value)}}
        elif name == "URL Demo":
            encoded[name] = {"url": str(value)}
        elif name == "Site Criado Em":
            encoded[name] = {"date": {"start": str(value)}}
        elif isinstance(value, (int, float)) and name in ("Valor",):
            encoded[name] = {"number": value}
        else:
            encoded[name] = _encode_rich_text("" if value is None else str(value))
    return encoded


def _extract_simple_value(prop_obj: Any) -> Any:
    if not isinstance(prop_obj, dict):
        return None

    ptype = prop_obj.get("type")
    if ptype == "select":
        sel = prop_obj.get("select")
        return sel.get("name") if isinstance(sel, dict) else None
    if ptype == "url":
        return prop_obj.get("url")
    if ptype == "date":
        dt = prop_obj.get("date")
        return dt.get("start") if isinstance(dt, dict) else None
    if ptype in ("rich_text", "title"):
        arr = prop_obj.get(ptype) or []
        if not isinstance(arr, list):
            return None
        parts = []
        for item in arr:
            if isinstance(item, dict):
                txt = item.get("plain_text")
                if isinstance(txt, str):
                    parts.append(txt)
        return "".join(parts).strip()
    if ptype == "number":
        return prop_obj.get("number")
    if ptype == "checkbox":
        return prop_obj.get("checkbox")
    return None


if __name__ == "__main__":
    # Example: generate MCP calls for a test prospect
    print("=== Search for qualified prospects ===")
    print_mcp_call(mcp_search_prospects("Qualificado"))

    print("\n=== Update prospect after site creation ===")
    print_mcp_call(
        build_site_ready_update(
            page_id="example-uuid",
            slug="dra-exemplo",
            us_id="US-089",
            url_demo="https://www.pixelalchemy.com.br/site-demo/dra-exemplo/",
            site_created_date="2026-02-22",
            mensagem="Olá! Sou o André, fundador da Pixel Alchemy...",
        )
    )
