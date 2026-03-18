#!/usr/bin/env python3
"""
Enqueue and optionally process a Notion update for a PRD user story.

This removes manual mistakes by reading:
- `notionPageId` from the story
- `slug` from acceptanceCriteria (site-demo/<slug>)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from config import NOTION_OUTBOX_DIR, SITE_DEMO_BASE_URL
from notion_sync.outbox import NotionOutbox
from notion_sync.worker import NotionWorker
from notion_client import NotionAPIClient
from prd_store import load_prd


SITE_RE = re.compile(r"site-demo/([^'/\s]+)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update Notion for a PRD story via outbox (no MCP).")
    p.add_argument("--us-id", required=True, help="Story ID, e.g. US-090")
    p.add_argument("--prd", default="prd.json", help="Path to PRD JSON")
    p.add_argument("--mensagem-file", required=True, help="Path to message text file")
    p.add_argument("--site-criado-em", required=True, help="YYYY-MM-DD")
    p.add_argument("--email-negocio", default="", help="Set Email Negocio")
    p.add_argument("--email-responsavel", default="", help="Set Email Responsavel")
    p.add_argument("--nome-responsavel", default="", help="Set Nome Responsavel")
    p.add_argument("--cargo-responsavel", default="", help="Set Cargo Responsavel")
    p.add_argument("--fonte-email", default="", help="Set Fonte Email select value")
    p.add_argument("--status-email", default="", help="Set Status Email select value")
    p.add_argument("--email-validado-em", default="", help="YYYY-MM-DD for Email Validado Em")
    p.add_argument("--outbox-dir", default=str(NOTION_OUTBOX_DIR), help="Outbox root directory")
    p.add_argument("--process", action="store_true", help="Run worker immediately after enqueue")
    return p.parse_args()


def _extract_slug(criteria: list[str]) -> str | None:
    for item in criteria:
        if not isinstance(item, str):
            continue
        m = SITE_RE.search(item)
        if m:
            return m.group(1)
    return None


def main() -> int:
    args = parse_args()
    prd = load_prd((Path.cwd() / args.prd).resolve())
    story = next((s for s in prd.get("userStories", []) if s.get("id") == args.us_id), None)
    if not story:
        raise SystemExit(f"Story not found: {args.us_id}")

    page_id = (story.get("notionPageId") or "").strip()
    if not page_id:
        raise SystemExit(f"Story {args.us_id} missing notionPageId (provide in orchestrator input JSON).")

    criteria = story.get("acceptanceCriteria") or []
    if not isinstance(criteria, list):
        criteria = []
    slug = _extract_slug(criteria)
    if not slug:
        raise SystemExit(f"Could not extract slug for {args.us_id} from acceptanceCriteria.")

    mensagem = Path(args.mensagem_file).read_text(encoding="utf-8")
    url_demo = f"{SITE_DEMO_BASE_URL}/{slug}/"

    properties = {
        "Status": "Mensagem Pronta",
        "URL Demo": url_demo,
        "Mensagem": mensagem,
        "Slug": slug,
        "US ID": args.us_id,
        "Site Criado Em": args.site_criado_em,
    }
    if args.email_negocio:
        properties["Email Negocio"] = args.email_negocio
    if args.email_responsavel:
        properties["Email Responsavel"] = args.email_responsavel
    if args.nome_responsavel:
        properties["Nome Responsavel"] = args.nome_responsavel
    if args.cargo_responsavel:
        properties["Cargo Responsavel"] = args.cargo_responsavel
    if args.fonte_email:
        properties["Fonte Email"] = args.fonte_email
    if args.status_email:
        properties["Status Email"] = args.status_email
    if args.email_validado_em:
        properties["Email Validado Em"] = args.email_validado_em

    outbox = NotionOutbox(Path(args.outbox_dir))
    event = outbox.enqueue_update_page_properties(
        us_id=args.us_id,
        page_id=page_id,
        properties=properties,
        verify_after_write=True,
    )
    print(f"enqueued idempotency_key={event.idempotency_key} event_id={event.event_id}")

    if args.process:
        worker = NotionWorker(outbox_dir=Path(args.outbox_dir), notion=NotionAPIClient())
        worker.process_once()
        print("worker: processed once")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
