"""
Pixel Alchemy — Notion Client Wrapper
=======================================

Abstraction layer for Notion CRM operations.

When running inside Claude Code, these functions describe the MCP tool calls
to make. When running standalone, they use the notion-client Python SDK.

Usage within Claude Code (MCP):
    - get_prospects_by_status() → use notion-search with data_source_url filter
    - update_prospect() → use notion-update-page with update_properties command
    - create_prospect() → use notion-create-pages with data_source_id parent

Usage standalone (requires NOTION_TOKEN env var):
    pip install notion-client
    NOTION_TOKEN=secret_xxx python3 scripts/notion_client.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import NOTION_DATA_SOURCE_ID


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
