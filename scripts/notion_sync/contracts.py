from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    idempotency_key: str
    created_at: str
    us_id: str
    page_id: str
    operation: str  # notion.pages.update
    properties: dict[str, Any]  # simple properties (our contract)
    verify_after_write: bool


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    created_at: str
    us_id: str
    page_id: str
    idempotency_key: str
    event_id: str
    operation: str
    expected_properties: dict[str, Any]
    notion_request: dict[str, Any]
    notion_response: dict[str, Any]
    verified: bool

