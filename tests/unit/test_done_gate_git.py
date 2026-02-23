from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import done_gate  # noqa: E402


class TestDoneGateGit(unittest.TestCase):
    def test_check_git_uses_site_path_not_grep(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir(parents=True, exist_ok=True)
            prd = {
                "name": "x",
                "userStories": [
                    {
                        "id": "US-001",
                        "acceptanceCriteria": [
                            "Criar pasta 'site-demo/example' e salvar index.html dentro"
                        ],
                    }
                ],
            }
            (root / "tasks" / "prd.json").write_text(json.dumps(prd), encoding="utf-8")

            def fake_run_git(args, cwd):
                cmd = " ".join(args)
                if cmd.startswith("log -n 1") and "site-demo/example/index.html" in cmd:
                    return 0, "abc123", ""
                if cmd.startswith("branch -r") and "abc123" in cmd:
                    return 0, "  origin/main\n", ""
                return 0, "", ""

            with mock.patch.object(done_gate, "run_git", side_effect=fake_run_git):
                checks = done_gate.check_git(
                    "US-001",
                    prd["userStories"][0],
                    root,
                    require_origin_main=True,
                )

            by_name = {c["name"]: c for c in checks}
            self.assertTrue(by_name["git.commit.local"]["passed"])
            self.assertTrue(by_name["git.commit.origin_main"]["passed"])
