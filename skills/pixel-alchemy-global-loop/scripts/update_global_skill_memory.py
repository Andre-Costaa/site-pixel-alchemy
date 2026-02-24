#!/usr/bin/env python3
"""
Append a learning entry and sync this skill to global agent skill roots.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path


SKIP_PARTS = {".git", "__pycache__"}
SKIP_FILES = {".DS_Store"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append learning to this skill and sync globally."
    )
    parser.add_argument("--learning", default="", help="Learning sentence to append")
    parser.add_argument("--us-id", default="", help="Optional US-XXX context")
    parser.add_argument("--evidence", default="", help="Optional evidence summary")
    parser.add_argument(
        "--skill-root",
        default="",
        help="Skill root directory (defaults to script parent)",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Extra sync target path (repeatable)",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Skip learning append and only sync files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without writing",
    )
    return parser.parse_args()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize(value: str) -> str:
    return " ".join(value.strip().split())


def learning_id(us_id: str, learning: str) -> str:
    base = f"{us_id.strip()}|{normalize(learning).lower()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def append_learning(
    *,
    log_path: Path,
    us_id: str,
    learning: str,
    evidence: str,
    dry_run: bool,
) -> tuple[bool, str]:
    learning_clean = normalize(learning)
    if not learning_clean:
        return False, "empty learning"

    entry_id = learning_id(us_id, learning_clean)
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    if f"[{entry_id}]" in existing:
        return False, f"duplicate [{entry_id}]"

    now = utc_now()
    day_header = f"## {now.strftime('%Y-%m-%d')}\n"
    ts = now.strftime("%Y-%m-%d %H:%M:%SZ")
    us_part = f" | {us_id.strip()}" if us_id.strip() else ""
    evidence_part = f" | evidence: {normalize(evidence)}" if evidence.strip() else ""
    line = f"- [{entry_id}] {ts}{us_part} | {learning_clean}{evidence_part}\n"

    content = existing
    if day_header not in content:
        if content and not content.endswith("\n"):
            content += "\n"
        content += "\n" + day_header
    content += line

    if dry_run:
        return True, f"would append [{entry_id}]"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(content, encoding="utf-8")
    return True, f"appended [{entry_id}]"


def default_targets(skill_name: str) -> list[Path]:
    home = Path.home()
    return [
        home / ".codex" / "skills" / skill_name,
        home / ".claude" / "skills" / skill_name,
        home / ".factory" / "skills" / skill_name,
        home / ".agents" / "skills" / skill_name,
    ]


def should_copy(rel_path: Path) -> bool:
    if any(part in SKIP_PARTS for part in rel_path.parts):
        return False
    if rel_path.name in SKIP_FILES:
        return False
    return True


def sync_skill(*, source: Path, target: Path, dry_run: bool) -> tuple[int, int]:
    copied = 0
    skipped = 0

    for path in source.rglob("*"):
        rel = path.relative_to(source)
        if not should_copy(rel):
            skipped += 1
            continue

        dest = target / rel
        if path.is_dir():
            if dry_run:
                continue
            dest.mkdir(parents=True, exist_ok=True)
            continue

        copied += 1
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    return copied, skipped


def main() -> int:
    args = parse_args()
    skill_root = (
        Path(args.skill_root).resolve()
        if args.skill_root
        else Path(__file__).resolve().parents[1]
    )
    skill_name = skill_root.name
    log_path = skill_root / "references" / "learning-log.md"

    if not args.sync_only and not normalize(args.learning):
        raise SystemExit("--learning is required unless --sync-only is set")

    if not args.sync_only:
        changed, msg = append_learning(
            log_path=log_path,
            us_id=args.us_id,
            learning=args.learning,
            evidence=args.evidence,
            dry_run=args.dry_run,
        )
        print(f"learning: {msg}")
    else:
        changed = False
        print("learning: skipped (--sync-only)")

    targets = default_targets(skill_name)
    if args.target:
        targets.extend(Path(t).expanduser().resolve() for t in args.target)

    # Remove duplicate targets and self-target.
    uniq_targets: list[Path] = []
    seen: set[str] = set()
    for target in targets:
        key = str(target.resolve())
        if key in seen:
            continue
        seen.add(key)
        if target.resolve() == skill_root.resolve():
            continue
        uniq_targets.append(target)

    errors = 0
    for target in uniq_targets:
        try:
            copied, skipped = sync_skill(
                source=skill_root,
                target=target,
                dry_run=args.dry_run,
            )
            mode = "dry-run" if args.dry_run else "synced"
            print(f"{mode}: {target} (copied={copied}, skipped={skipped})")
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"error: {target} -> {exc!r}")

    if errors:
        return 1
    if not changed and not args.sync_only:
        # Duplicate learning is non-fatal, sync may still have run.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
