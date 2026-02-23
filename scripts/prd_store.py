"""
PRD Store
=========

Single source of truth is `tasks/prd.json` (per repository process),
but this repo historically used `prd.json` at the project root.

This module reads from the canonical path when present and keeps the
legacy file in sync on writes to avoid divergence during transition.
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


def save_prd(data: dict[str, Any], path: Path | None = None) -> None:
    prd_path = path or PRD_JSON_PATH

    # Write to the requested path atomically.
    atomic_write_json(prd_path, data)

    # Bidirectional sync: always keep canonical and legacy in lockstep.
    if PRD_JSON_PATH.resolve() != prd_path.resolve():
        atomic_write_json(PRD_JSON_PATH, data)
    if PRD_JSON_LEGACY_PATH.resolve() != prd_path.resolve():
        atomic_write_json(PRD_JSON_LEGACY_PATH, data)

