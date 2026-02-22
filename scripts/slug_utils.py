"""
Pixel Alchemy — Slug Utilities
================================

Generate URL-safe slugs from business names and verify uniqueness
against existing site-demo/ directories.
"""

import re
import sys
import unicodedata
from pathlib import Path

# Allow imports when running from project root or scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))

from config import SITE_DEMO_DIR


def generate_slug(name: str, max_length: int = 60) -> str:
    """Generate a URL-safe slug from a business name.

    - Strips accents (NFD decomposition)
    - Lowercases
    - Replaces non-alphanumeric sequences with hyphens
    - Truncates at max_length on a hyphen boundary
    """
    # Normalize unicode and strip combining marks (accents)
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")

    # Lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    # Truncate at max_length on word boundary
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]

    return slug


def get_existing_slugs(site_demo_dir: Path = SITE_DEMO_DIR) -> set[str]:
    """Return the set of all existing directory names under site-demo/."""
    if not site_demo_dir.exists():
        return set()
    return {d.name for d in site_demo_dir.iterdir() if d.is_dir()}


def ensure_unique_slug(
    slug: str, existing: set[str] | None = None
) -> str:
    """Ensure slug is unique by appending a numeric suffix if needed."""
    if existing is None:
        existing = get_existing_slugs()

    if slug not in existing:
        return slug

    counter = 2
    while f"{slug}-{counter}" in existing:
        counter += 1

    return f"{slug}-{counter}"


def slug_to_url(slug: str) -> str:
    """Convert a slug to its full demo URL."""
    from config import SITE_DEMO_BASE_URL
    return f"{SITE_DEMO_BASE_URL}/{slug}/"
