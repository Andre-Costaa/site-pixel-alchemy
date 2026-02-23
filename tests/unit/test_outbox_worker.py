from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from notion_client import NotionAPIError  # noqa: E402
from notion_sync.outbox import NotionOutbox  # noqa: E402
from notion_sync.worker import NotionWorker  # noqa: E402
from notion_sync.store import read_json  # noqa: E402


class _FakeNotion:
    def update_page_simple(self, *, page_id: str, properties: dict):
        return {"page_id": page_id, "properties": properties}

    def verify_page_simple(self, *, page_id: str, expected_properties: dict) -> bool:
        return True


class TestOutboxAndWorker(unittest.TestCase):
    def test_enqueue_is_idempotent_before_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            outbox = NotionOutbox(Path(tmp))
            a = outbox.enqueue_update_page_properties(
                us_id="US-123",
                page_id="page",
                properties={"Status": "Mensagem Pronta"},
            )
            b = outbox.enqueue_update_page_properties(
                us_id="US-123",
                page_id="page",
                properties={"Status": "Mensagem Pronta"},
            )
            self.assertEqual(a.idempotency_key, b.idempotency_key)
            self.assertEqual(a.event_id, b.event_id)

    def test_worker_creates_verified_receipt_and_us_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            outbox_dir = Path(tmp)
            outbox = NotionOutbox(outbox_dir)
            event = outbox.enqueue_update_page_properties(
                us_id="US-123",
                page_id="page",
                properties={"Status": "Mensagem Pronta", "US ID": "US-123"},
            )

            worker = NotionWorker(outbox_dir=outbox_dir, notion=_FakeNotion())
            processed = worker.process_once()
            self.assertTrue(processed)

            receipt_path = outbox.receipt_path(event.idempotency_key)
            self.assertTrue(receipt_path.exists())
            receipt = read_json(receipt_path)
            self.assertTrue(receipt.get("verified"))

            idx_path = outbox_dir / "index" / "us_id" / "US-123.json"
            self.assertTrue(idx_path.exists())

    def test_worker_dead_letter_on_non_retryable_error(self):
        class _FakeNotionNonRetryable:
            def update_page_simple(self, *, page_id: str, properties: dict):
                raise NotionAPIError("Unauthorized", status_code=401, body='{"message":"unauthorized"}')

            def verify_page_simple(self, *, page_id: str, expected_properties: dict) -> bool:
                return True

        with tempfile.TemporaryDirectory() as tmp:
            outbox_dir = Path(tmp)
            outbox = NotionOutbox(outbox_dir)
            event = outbox.enqueue_update_page_properties(
                us_id="US-200",
                page_id="page-401",
                properties={"Status": "Mensagem Pronta"},
            )

            worker = NotionWorker(outbox_dir=outbox_dir, notion=_FakeNotionNonRetryable())
            processed = worker.process_once()
            self.assertTrue(processed)

            # Dead-letter file must exist with the correct reason.
            dead_path = outbox.dead_letter_dir / f"{event.idempotency_key}.json"
            self.assertTrue(dead_path.exists(), f"Dead-letter file not found: {dead_path}")
            dead_payload = read_json(dead_path)
            self.assertEqual(dead_payload["dead_letter_reason"], "non_retryable_http_401")

            # No receipt should have been created.
            receipt_path = outbox.receipt_path(event.idempotency_key)
            self.assertFalse(receipt_path.exists(), "Receipt should NOT exist for non-retryable error")

    def test_worker_dead_letter_on_retry_exhaustion(self):
        class _FakeNotionAlwaysFails:
            def update_page_simple(self, *, page_id: str, properties: dict):
                raise RuntimeError("some_error")

            def verify_page_simple(self, *, page_id: str, expected_properties: dict) -> bool:
                return True

        with tempfile.TemporaryDirectory() as tmp:
            outbox_dir = Path(tmp)
            outbox = NotionOutbox(outbox_dir)
            event = outbox.enqueue_update_page_properties(
                us_id="US-201",
                page_id="page-retry",
                properties={"Status": "Mensagem Pronta"},
            )

            # max_attempts=1: first call will attempt (attempts=0 < 1), fail,
            # then _retry_or_dead_letter increments to 1 >= 1, triggering dead letter.
            worker = NotionWorker(outbox_dir=outbox_dir, notion=_FakeNotionAlwaysFails(), max_attempts=1)
            worker.process_once()

            dead_letter_files = list(outbox.dead_letter_dir.glob("*.json")) if outbox.dead_letter_dir.exists() else []
            self.assertTrue(len(dead_letter_files) > 0, "Dead-letter file should exist after retry exhaustion")

            dead_payload = read_json(dead_letter_files[0])
            self.assertIn("exhaust", dead_payload["dead_letter_reason"],
                          f"Expected reason to contain 'exhaust', got: {dead_payload['dead_letter_reason']}")

    def test_worker_read_after_write_failure_retries(self):
        class _FakeNotionVerifyFails:
            def update_page_simple(self, *, page_id: str, properties: dict):
                return {"page_id": page_id, "properties": properties}

            def verify_page_simple(self, *, page_id: str, expected_properties: dict) -> bool:
                return False

        with tempfile.TemporaryDirectory() as tmp:
            outbox_dir = Path(tmp)
            outbox = NotionOutbox(outbox_dir)
            event = outbox.enqueue_update_page_properties(
                us_id="US-202",
                page_id="page-verify",
                properties={"Status": "Mensagem Pronta"},
                verify_after_write=True,
            )

            worker = NotionWorker(outbox_dir=outbox_dir, notion=_FakeNotionVerifyFails(), max_attempts=8)
            worker.process_once()

            # Event should be moved back to queue (not dead-lettered, not receipted).
            receipt_path = outbox.receipt_path(event.idempotency_key)
            self.assertFalse(receipt_path.exists(), "Receipt should NOT exist when verification fails")

            dead_letter_files = list(outbox.dead_letter_dir.glob("*.json")) if outbox.dead_letter_dir.exists() else []
            self.assertEqual(len(dead_letter_files), 0, "Should NOT be dead-lettered after first failure")

            # Event should be back in the queue with incremented attempt count.
            queue_files = list(outbox.queue_dir.glob("*.json"))
            self.assertTrue(len(queue_files) > 0, "Event should be back in queue")
            requeued_payload = read_json(queue_files[0])
            self.assertGreaterEqual(int(requeued_payload.get("attempts", 0)), 1,
                                    "Attempt count should be incremented")

