from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from notion_client import NotionAPIClient
from notion_client import NotionAPIError
from notion_sync.contracts import Receipt, utc_now_iso
from notion_sync.outbox import NotionOutbox
from notion_sync.store import append_jsonl, atomic_write_json, read_json


def _parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotionWorker:
    def __init__(
        self,
        *,
        outbox_dir: Path,
        notion: NotionAPIClient,
        max_attempts: int = 8,
    ) -> None:
        self.outbox = NotionOutbox(outbox_dir)
        self.notion = notion
        self.max_attempts = max_attempts

    def _claim_one(self) -> Path | None:
        self.outbox.queue_dir.mkdir(parents=True, exist_ok=True)
        self.outbox.processing_dir.mkdir(parents=True, exist_ok=True)
        for event_path in sorted(self.outbox.queue_dir.glob("*.json")):
            processing_path = self.outbox.processing_dir / event_path.name
            try:
                event_path.rename(processing_path)
                return processing_path
            except FileNotFoundError:
                continue
        return None

    def process_once(self) -> bool:
        event_path = self._claim_one()
        if event_path is None:
            return False

        payload = read_json(event_path)
        idempotency_key = payload["idempotency_key"]
        receipt_path = self.outbox.receipt_path(idempotency_key)
        if receipt_path.exists():
            event_path.unlink(missing_ok=True)
            return True

        next_run_at = _parse_iso(payload.get("next_run_at", payload["created_at"]))
        if _utc_now() < next_run_at:
            # Not ready yet; move back to queue.
            event_path.rename(self.outbox.queue_dir / event_path.name)
            return True

        attempts = int(payload.get("attempts", 0))
        if attempts >= self.max_attempts:
            self._dead_letter(event_path, payload, "attempts_exhausted")
            return True

        try:
            page_id = payload["page_id"]
            props = payload["properties"]
            notion_req = {"page_id": page_id, "properties": props}
            notion_resp = self.notion.update_page_simple(page_id=page_id, properties=props)

            verified = True
            if payload.get("verify_after_write", True):
                verified = self.notion.verify_page_simple(
                    page_id=page_id, expected_properties=props
                )
                if not verified:
                    raise RuntimeError("read_after_write_verification_failed")

            receipt = Receipt(
                receipt_id=str(uuid.uuid4()),
                created_at=utc_now_iso(),
                us_id=payload["us_id"],
                page_id=page_id,
                idempotency_key=idempotency_key,
                event_id=payload["event_id"],
                operation=payload["operation"],
                expected_properties=props,
                notion_request=notion_req,
                notion_response=notion_resp,
                verified=verified,
            )
            receipt_payload = json.loads(json.dumps(receipt.__dict__, ensure_ascii=False))
            atomic_write_json(receipt_path, receipt_payload)
            append_jsonl(self.outbox.audit_dir / "receipts.jsonl", receipt_payload)

            # Lightweight index for done_gate O(1) lookup.
            atomic_write_json(
                self.outbox.root_dir / "index" / "us_id" / f"{payload['us_id']}.json",
                {"us_id": payload["us_id"], "receipt": str(receipt_path)},
            )

            event_path.unlink(missing_ok=True)
            return True
        except Exception as exc:  # noqa: BLE001 - operational boundary
            return self._retry_or_dead_letter(event_path, payload, exc)

    def _retry_or_dead_letter(self, event_path: Path, payload: dict[str, Any], exc: Exception) -> bool:
        if isinstance(exc, NotionAPIError) and exc.status_code in (400, 401, 403, 404):
            payload["attempts"] = int(payload.get("attempts", 0)) + 1
            payload["last_error"] = repr(exc)
            payload["last_error_at"] = utc_now_iso()
            self._dead_letter(event_path, payload, f"non_retryable_http_{exc.status_code}")
            return True

        attempts = int(payload.get("attempts", 0)) + 1
        payload["attempts"] = attempts
        payload["last_error"] = repr(exc)
        payload["last_error_at"] = utc_now_iso()

        # Exponential backoff with cap.
        base = 2.0
        delay = min(120.0, base * (2 ** min(attempts, 6))) * (1 + random.random() * 0.25)
        payload["next_run_at"] = (_utc_now() + _timedelta_seconds(delay)).isoformat()

        if attempts >= self.max_attempts:
            self._dead_letter(event_path, payload, "retry_exhausted")
            return True

        atomic_write_json(event_path, payload)
        # Move back to queue for later processing.
        event_path.rename(self.outbox.queue_dir / event_path.name)
        return True

    def _dead_letter(self, event_path: Path, payload: dict[str, Any], reason: str) -> None:
        self.outbox.dead_letter_dir.mkdir(parents=True, exist_ok=True)
        dead_path = self.outbox.dead_letter_dir / f"{payload['idempotency_key']}.json"
        payload["dead_letter_reason"] = reason
        payload["dead_letter_at"] = utc_now_iso()
        atomic_write_json(dead_path, payload)
        append_jsonl(self.outbox.audit_dir / "dead_letter.jsonl", payload)
        event_path.unlink(missing_ok=True)

def _timedelta_seconds(seconds: float):
    # Local helper to avoid importing timedelta in multiple call sites.
    from datetime import timedelta

    return timedelta(seconds=seconds)
