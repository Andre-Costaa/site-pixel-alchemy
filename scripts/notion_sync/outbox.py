from __future__ import annotations

import uuid
import fcntl
from pathlib import Path
from typing import Any

from notion_sync.contracts import OutboxEvent, canonical_json, sha256_hex, utc_now_iso
from notion_sync.store import append_jsonl, atomic_write_json, read_json


class NotionOutbox:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.queue_dir = root_dir / "queue"
        self.processing_dir = root_dir / "processing"
        self.receipts_dir = root_dir / "receipts"
        self.dead_letter_dir = root_dir / "dead-letter"
        self.audit_dir = root_dir / "audit"
        self.index_dir = root_dir / "index" / "idempotency"
        self.locks_dir = root_dir / "locks"

    def _event_path(self, event_id: str) -> Path:
        return self.queue_dir / f"{event_id}.json"

    def receipt_path(self, idempotency_key: str) -> Path:
        return self.receipts_dir / f"{idempotency_key}.json"

    def enqueue_update_page_properties(
        self,
        *,
        us_id: str,
        page_id: str,
        properties: dict[str, Any],
        verify_after_write: bool = True,
    ) -> OutboxEvent:
        # Deterministic key so repeated enqueues do not create duplicates.
        key_material = canonical_json(
            {
                "us_id": us_id,
                "page_id": page_id,
                "op": "notion.pages.update",
                "properties": properties,
            }
        )
        idempotency_key = sha256_hex(key_material)
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.locks_dir / f"{idempotency_key}.lock"

        with lock_path.open("w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            if self.receipt_path(idempotency_key).exists():
                return OutboxEvent(
                    event_id="(already-receipted)",
                    idempotency_key=idempotency_key,
                    created_at=utc_now_iso(),
                    us_id=us_id,
                    page_id=page_id,
                    operation="notion.pages.update",
                    properties=properties,
                    verify_after_write=verify_after_write,
                )

            index_path = self.index_dir / f"{idempotency_key}.json"
            if index_path.exists():
                existing = read_json(index_path)
                event_id = str(existing.get("event_id", ""))
                if event_id and (self.queue_dir / f"{event_id}.json").exists():
                    return OutboxEvent(
                        event_id=event_id,
                        idempotency_key=idempotency_key,
                        created_at=str(existing.get("created_at", utc_now_iso())),
                        us_id=us_id,
                        page_id=page_id,
                        operation="notion.pages.update",
                        properties=properties,
                        verify_after_write=verify_after_write,
                    )

            event_id = str(uuid.uuid4())
            event = OutboxEvent(
                event_id=event_id,
                idempotency_key=idempotency_key,
                created_at=utc_now_iso(),
                us_id=us_id,
                page_id=page_id,
                operation="notion.pages.update",
                properties=properties,
                verify_after_write=verify_after_write,
            )
            payload = {
                "event_id": event.event_id,
                "idempotency_key": event.idempotency_key,
                "created_at": event.created_at,
                "us_id": event.us_id,
                "page_id": event.page_id,
                "operation": event.operation,
                "properties": event.properties,
                "verify_after_write": event.verify_after_write,
                "attempts": 0,
                "next_run_at": event.created_at,
            }
            atomic_write_json(self._event_path(event_id), payload)
            self.index_dir.mkdir(parents=True, exist_ok=True)
            atomic_write_json(
                index_path,
                {
                    "idempotency_key": idempotency_key,
                    "event_id": event_id,
                    "created_at": event.created_at,
                },
            )
            append_jsonl(self.audit_dir / "events.jsonl", payload)
            return event
