"""
PRD Store
=========

Single source of truth is `prd.json` at the project root.
The legacy mirror `tasks/prd.json` is kept synchronized for compatibility.

This module reads from the canonical path when present and keeps the legacy
file in sync on writes to avoid divergence during transition.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import PRD_JSON_LEGACY_PATH, PRD_JSON_PATH
from notion_sync.store import atomic_write_json


def _validate_prd_shape(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("userStories"), list):
        raise ValueError("Invalid PRD JSON shape (expected dict with userStories list)")
    return data


def load_prd(path: Path | None = None) -> dict[str, Any]:
    prd_path = path or (PRD_JSON_PATH if PRD_JSON_PATH.exists() else PRD_JSON_LEGACY_PATH)
    with prd_path.open("r", encoding="utf-8") as f:
        return _validate_prd_shape(json.load(f))


def save_prd(
    data: dict[str, Any],
    path: Path | None = None,
    *,
    sync_mirrors: bool | None = None,
) -> None:
    prd_path = path or PRD_JSON_PATH
    canonical = PRD_JSON_PATH.resolve()
    legacy = PRD_JSON_LEGACY_PATH.resolve()
    target = prd_path.resolve()

    # Write to the requested path atomically.
    atomic_write_json(prd_path, data)

    # Mirror sync applies only to canonical/legacy targets by default.
    # This prevents alternate files (e.g. prd.smoke.json) from overwriting
    # production PRD paths.
    if sync_mirrors is None:
        sync_mirrors = target in {canonical, legacy}
    if not sync_mirrors:
        return

    # Bidirectional sync for canonical <-> legacy.
    if canonical != target:
        atomic_write_json(PRD_JSON_PATH, data)
    if legacy != target:
        atomic_write_json(PRD_JSON_LEGACY_PATH, data)
