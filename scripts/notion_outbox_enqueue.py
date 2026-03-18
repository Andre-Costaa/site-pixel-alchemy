#!/usr/bin/env python3
"""
Enqueue Notion updates into the local outbox (no MCP required).

This writes an outbox event that can be processed by `notion_outbox_worker.py`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import NOTION_OUTBOX_DIR
from notion_sync.outbox import NotionOutbox


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enqueue a Notion page update into the outbox.")
    parser.add_argument("--us-id", required=True, help="User story id, e.g. US-090")
    parser.add_argument("--page-id", required=True, help="Notion page UUID")
    parser.add_argument("--status", default="", help="Set Status select value (e.g. 'Mensagem Pronta')")
    parser.add_argument("--url-demo", default="", help="Set URL Demo")
    parser.add_argument("--slug", default="", help="Set Slug")
    parser.add_argument("--mensagem-file", default="", help="Path to a text file for Mensagem")
    parser.add_argument("--site-criado-em", default="", help="YYYY-MM-DD for Site Criado Em")
    parser.add_argument("--email-negocio", default="", help="Set Email Negocio")
    parser.add_argument("--email-responsavel", default="", help="Set Email Responsavel")
    parser.add_argument("--nome-responsavel", default="", help="Set Nome Responsavel")
    parser.add_argument("--cargo-responsavel", default="", help="Set Cargo Responsavel")
    parser.add_argument("--fonte-email", default="", help="Set Fonte Email select value")
    parser.add_argument("--status-email", default="", help="Set Status Email select value")
    parser.add_argument("--email-validado-em", default="", help="YYYY-MM-DD for Email Validado Em")
    parser.add_argument(
        "--outbox-dir",
        default=str(NOTION_OUTBOX_DIR),
        help="Outbox root directory",
    )
    parser.add_argument(
        "--no-verify-after-write",
        action="store_true",
        help="Do not verify via read-after-write (not recommended)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    properties: dict[str, object] = {}
    if args.status:
        properties["Status"] = args.status
    if args.url_demo:
        properties["URL Demo"] = args.url_demo
    if args.slug:
        properties["Slug"] = args.slug
    if args.site_criado_em:
        properties["Site Criado Em"] = args.site_criado_em
    if args.mensagem_file:
        properties["Mensagem"] = Path(args.mensagem_file).read_text(encoding="utf-8")
    if args.us_id:
        properties["US ID"] = args.us_id
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

    if not properties:
        raise SystemExit("No properties provided. Pass --status/--url-demo/--slug/--mensagem-file/--site-criado-em.")

    # Enforce all critical fields are present to prevent incomplete Notion updates.
    required = {"Status", "Mensagem", "Slug", "URL Demo", "US ID"}
    missing = required - set(properties.keys())
    if missing:
        raise SystemExit(
            f"BLOCKED: Missing required fields: {', '.join(sorted(missing))}.\n"
            f"All of {sorted(required)} must be provided.\n"
            f"Use --status, --url-demo, --slug, --mensagem-file, and --us-id."
        )

    outbox = NotionOutbox(Path(args.outbox_dir))
    event = outbox.enqueue_update_page_properties(
        us_id=args.us_id,
        page_id=args.page_id,
        properties=properties,
        verify_after_write=not args.no_verify_after_write,
    )
    print(f"enqueued idempotency_key={event.idempotency_key} event_id={event.event_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
