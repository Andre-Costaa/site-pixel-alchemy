from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import prd_store  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestPRDStoreSave(unittest.TestCase):
    def test_save_alt_prd_does_not_overwrite_canonical_or_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "prd.json"
            legacy = root / "tasks" / "prd.json"
            alt = root / "prd.smoke.json"

            old_data = {"name": "old", "userStories": []}
            new_data = {"name": "new", "userStories": [{"id": "US-001"}]}

            canonical.parent.mkdir(parents=True, exist_ok=True)
            legacy.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(json.dumps(old_data), encoding="utf-8")
            legacy.write_text(json.dumps(old_data), encoding="utf-8")

            with mock.patch.object(prd_store, "PRD_JSON_PATH", canonical), mock.patch.object(
                prd_store, "PRD_JSON_LEGACY_PATH", legacy
            ):
                prd_store.save_prd(new_data, alt)

            self.assertEqual(read_json(alt), new_data)
            self.assertEqual(read_json(canonical), old_data)
            self.assertEqual(read_json(legacy), old_data)

    def test_save_canonical_syncs_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "prd.json"
            legacy = root / "tasks" / "prd.json"
            new_data = {"name": "canonical", "userStories": [{"id": "US-010"}]}

            with mock.patch.object(prd_store, "PRD_JSON_PATH", canonical), mock.patch.object(
                prd_store, "PRD_JSON_LEGACY_PATH", legacy
            ):
                prd_store.save_prd(new_data, canonical)

            self.assertEqual(read_json(canonical), new_data)
            self.assertEqual(read_json(legacy), new_data)

    def test_save_legacy_syncs_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "prd.json"
            legacy = root / "tasks" / "prd.json"
            new_data = {"name": "legacy", "userStories": [{"id": "US-020"}]}

            with mock.patch.object(prd_store, "PRD_JSON_PATH", canonical), mock.patch.object(
                prd_store, "PRD_JSON_LEGACY_PATH", legacy
            ):
                prd_store.save_prd(new_data, legacy)

            self.assertEqual(read_json(canonical), new_data)
            self.assertEqual(read_json(legacy), new_data)
