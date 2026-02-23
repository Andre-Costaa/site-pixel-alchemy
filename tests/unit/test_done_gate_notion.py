from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import done_gate  # noqa: E402


class TestDoneGateNotion(unittest.TestCase):
    def test_check_notion_fails_without_token(self):
        story = {
            "id": "US-300",
            "acceptanceCriteria": [
                "Atualizar Notion com Status 'Mensagem Pronta'",
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            # Ensure NOTION_TOKEN is NOT set.
            env = os.environ.copy()
            env.pop("NOTION_TOKEN", None)
            with mock.patch.dict(os.environ, env, clear=True):
                results = done_gate.check_notion("US-300", story, cwd)

        by_name = {c["name"]: c for c in results}
        self.assertIn("notion.token", by_name, f"Expected 'notion.token' check, got: {list(by_name.keys())}")
        self.assertFalse(by_name["notion.token"]["passed"])
        self.assertIn("NOTION_TOKEN", by_name["notion.token"]["detail"])

    def test_check_notion_fails_without_receipt(self):
        story = {
            "id": "US-301",
            "acceptanceCriteria": [
                "Atualizar Notion com Status 'Mensagem Pronta'",
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outbox_dir = Path(tmp)
            cwd = Path(tmp)

            # Set NOTION_TOKEN so we pass the token check.
            # Point NOTION_OUTBOX_DIR to our empty temp dir (no receipts).
            with mock.patch.dict(os.environ, {"NOTION_TOKEN": "dummy-token"}, clear=False):
                with mock.patch.object(done_gate, "NOTION_OUTBOX_DIR", outbox_dir):
                    results = done_gate.check_notion("US-301", story, cwd)

        by_name = {c["name"]: c for c in results}
        self.assertIn("notion.receipt", by_name, f"Expected 'notion.receipt' check, got: {list(by_name.keys())}")
        self.assertFalse(by_name["notion.receipt"]["passed"])
        self.assertIn("receipt", by_name["notion.receipt"]["detail"].lower())
