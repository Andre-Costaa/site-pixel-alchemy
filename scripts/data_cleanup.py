"""
Fase 0.3 — Data Cleanup Script for Notion CRM
===============================================

This script documents and generates the cleanup operations performed on the
Notion "Controle" database (2f76f51e-b8a5-8088-a52c-db29fc3c1f81).

The actual updates were applied via Notion MCP tools in Claude Code.
This file serves as an audit trail.

Cleanup tasks:
  0.3.1 - Sync URL Demo + Slug from site-demo/ folders (via harmonizacao.csv)
  0.3.2 - Fix "Ribeirã Preto" typo in Endereço fields
  0.3.3 - Extract URLs from Mensagem field → URL Demo
  0.3.4 - Fix HAR-0010 status (if corrupted)
  0.3.5 - Normalize Origem: harmonizacao → Harmonização (done via schema update)
  0.3.6 - Flag fake phones ((16) 99999-9999) in Observações
  0.3.7 - Standardize legacy Notion records without IDs

Run: python3 scripts/data_cleanup.py
"""

import csv
import re
import unicodedata
from pathlib import Path

SITE_DEMO_DIR = Path(__file__).parent.parent / "site-demo"
CSV_PATH = Path(__file__).parent.parent / "harmonizacao.csv"
BASE_URL = "https://www.pixelalchemy.com.br/site-demo"


def generate_slug(name):
    """Generate URL slug from business name."""
    # Normalize unicode, strip accents
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    # Truncate at 60 chars on word boundary
    if len(slug) > 60:
        slug = slug[:60].rsplit("-", 1)[0]
    return slug


def get_existing_slugs():
    """Get all existing site-demo directory names."""
    if not SITE_DEMO_DIR.exists():
        return set()
    return {d.name for d in SITE_DEMO_DIR.iterdir() if d.is_dir()}


def extract_slug_from_url(url):
    """Extract slug from a pixelalchemy URL."""
    if not url:
        return None
    match = re.search(r"/site-demo/([^/]+)/?", url)
    return match.group(1) if match else None


def load_csv_mapping():
    """Load name→URL mapping from harmonizacao.csv."""
    mapping = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        url_idx = header.index("URL")
        nome_idx = header.index("Nome")
        for row in reader:
            if len(row) > max(url_idx, nome_idx):
                name = row[nome_idx].strip()
                url = row[url_idx].strip()
                if name and url:
                    mapping[name] = url
    return mapping


def task_sync_url_demo():
    """Task 0.3.1 - Generate URL Demo + Slug sync operations."""
    print("=" * 60)
    print("TASK 0.3.1: Sync URL Demo + Slug from site-demo folders")
    print("=" * 60)

    csv_mapping = load_csv_mapping()
    existing_slugs = get_existing_slugs()

    print(f"\nCSV entries: {len(csv_mapping)}")
    print(f"Site-demo folders: {len(existing_slugs)}")

    operations = []
    for name, url in csv_mapping.items():
        slug = extract_slug_from_url(url)
        if slug and slug in existing_slugs:
            operations.append({
                "name": name,
                "url_demo": url,
                "slug": slug,
            })

    print(f"Matched records to update: {len(operations)}")
    for op in operations:
        print(f"  {op['name']} → {op['slug']}")

    return operations


def task_fix_typo():
    """Task 0.3.2 - Identify records with 'Ribeirã Preto' typo."""
    print("\n" + "=" * 60)
    print("TASK 0.3.2: Fix 'Ribeirã Preto' → 'Ribeirão Preto' typo")
    print("=" * 60)
    print("Applied via Notion search + batch update on Endereço field")
    print("Search query: records where Endereço contains 'Ribeirã Preto'")
    print("Replace with: 'Ribeirão Preto'")


def task_extract_urls():
    """Task 0.3.3 - Extract URLs from Mensagem field."""
    print("\n" + "=" * 60)
    print("TASK 0.3.3: Extract URLs from Mensagem → URL Demo")
    print("=" * 60)
    print("Search: HAR records where Mensagem contains 'pixelalchemy.com.br/site-demo/'")
    print("Extract URL from message text → populate URL Demo field")


def task_fix_har0010():
    """Task 0.3.4 - Fix HAR-0010 status."""
    print("\n" + "=" * 60)
    print("TASK 0.3.4: Fix HAR-0010 (Dra. Karen Veronese)")
    print("=" * 60)
    print("Page ID: 30f6f51e-b8a5-8150-b559-f90d091286bf")
    print("Set Status → 'Lead' (was empty/corrupted)")
    print("Set URL Demo → https://www.pixelalchemy.com.br/site-demo/dra-karen-veronese/")
    print("Set Slug → dra-karen-veronese")


def task_normalize_origem():
    """Task 0.3.5 - Already done via schema rename."""
    print("\n" + "=" * 60)
    print("TASK 0.3.5: Normalize Origem (COMPLETED via schema update)")
    print("=" * 60)
    print("Renamed select option 'harmonizacao' → 'Harmonização' at schema level")


def task_flag_fake_phones():
    """Task 0.3.6 - Flag fake phone numbers."""
    print("\n" + "=" * 60)
    print("TASK 0.3.6: Flag fake phones ((16) 99999-9999)")
    print("=" * 60)
    print("Search: records where Telefone = '(16) 99999-9999'")
    print("Action: Add 'TELEFONE FALSO/PLACEHOLDER' to Observações")


def task_standardize_legacy():
    """Task 0.3.7 - Standardize legacy records without IDs."""
    print("\n" + "=" * 60)
    print("TASK 0.3.7: Standardize legacy Notion records")
    print("=" * 60)
    print("Search: records where ID is empty and Origem = 'Notion (Beleza)'")
    print("Action: Generate BEL-XXXX IDs, set Nicho=Beleza if empty")


if __name__ == "__main__":
    task_sync_url_demo()
    task_fix_typo()
    task_extract_urls()
    task_fix_har0010()
    task_normalize_origem()
    task_flag_fake_phones()
    task_standardize_legacy()
