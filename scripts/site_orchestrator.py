"""
Pixel Alchemy — Site Orchestrator
====================================

Generates user stories in prd.json format from Notion prospect data,
manages the site creation pipeline, and writes back results to Notion.

Workflow:
    1. Query Notion for prospects with Status = "Qualificado"
    2. Generate slug, US ID, and user story JSON
    3. Append to prd.json
    4. Update Notion: Status → "Site em Criação"
    5. (External) Claude Code / Ralph TUI creates the site
    6. Update Notion: Status → "Mensagem Pronta", URL Demo, Slug, US ID, Site Criado Em

Usage:
    # Show what would be generated (dry run)
    python3 scripts/site_orchestrator.py --dry-run

    # Generate user stories for all qualified prospects
    python3 scripts/site_orchestrator.py

    # Generate for a specific prospect by name
    python3 scripts/site_orchestrator.py --name "Dra. Exemplo"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SITE_DEMO_BASE_URL, SITE_DEMO_DIR
from notion_dedup_guard import check_duplicate, check_slug_duplicate
from prd_store import load_prd, save_prd
from slug_utils import ensure_unique_slug, generate_slug, get_existing_slugs


def get_next_us_id(prd: dict) -> tuple[str, int]:
    """Get the next available US-XXX ID and priority number."""
    stories = prd.get("userStories", [])
    if not stories:
        return "US-001", 1

    max_num = 0
    for story in stories:
        sid = story.get("id", "")
        if sid.startswith("US-"):
            try:
                num = int(sid.split("-")[1])
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                pass

    next_num = max_num + 1
    return f"US-{next_num:03d}", next_num


def get_last_us_id(prd: dict) -> str:
    """Get the last US ID for dependency chaining."""
    stories = prd.get("userStories", [])
    if not stories:
        return ""
    return stories[-1].get("id", "")


def build_user_story(
    prospect: dict,
    us_id: str,
    priority: int,
    slug: str,
    previous_us_id: str,
) -> dict:
    """Build a user story dict in the exact prd.json format.

    Args:
        prospect: Dict with keys: Nome, Telefone, Endereço, Descrição, Nicho
        us_id: e.g. "US-089"
        priority: numeric priority
        slug: URL slug for site-demo/
        previous_us_id: for dependsOn chain
    """
    nome = prospect.get("Nome", "")
    telefone = prospect.get("Telefone", "")
    endereco = prospect.get("Endereço", "")
    descricao = prospect.get("Descrição", "")
    page_id = prospect.get("page_id") or prospect.get("Page ID") or prospect.get("pageId") or ""

    # Build description
    desc_parts = [f"Criar site profissional para {nome}"]
    # Add city when we have an address that is not already explicit.
    if endereco and "ribeirão preto" not in endereco.lower():
        desc_parts[0] += f" em Ribeirão Preto"
    if descricao:
        desc_parts.append(descricao)

    # Build acceptance criteria
    criteria = [
        "Site HTML único com CSS e JS embutidos",
        "Design premiado, único e memorável - evitar template genérico",
        "Seguir integralmente o prompt-modelo.md",
        f"Seções: Hero, Problema/Solução, Serviços, Depoimentos, Diferenciais, Contato, Footer",
    ]

    if endereco:
        criteria.append(f"Informações: {endereco}")
    if telefone:
        criteria.append(f"Telefone: {telefone}")

    criteria.extend([
        f"Criar pasta 'site-demo/{slug}' e salvar index.html dentro",
        "Gerar mensagem de outreach personalizada (ver template-mensagem-outreach.md)",
        "Atualizar Notion: Status → 'Mensagem Pronta', URL Demo, Mensagem, Slug, US ID, Site Criado Em",
        f"Rodar done gate: python3 scripts/done_gate.py --us-id {us_id} (só marcar passes=true se PASS)",
        "Fazer git add, commit e push ao finalizar",
    ])

    story = {
        "id": us_id,
        "title": f"{nome} - Site Completo",
        "description": ". ".join(desc_parts) + ".",
        "acceptanceCriteria": criteria,
        "priority": priority,
        "passes": False,
        "notes": "",
        "dependsOn": [previous_us_id] if previous_us_id else [],
        "completionNotes": "",
        # Optional: enable objective Notion updates/verification later.
        "notionPageId": page_id,
    }

    return story


def generate_for_prospect(
    prospect: dict,
    prd: dict,
    existing_slugs: set[str],
    dry_run: bool = False,
) -> dict | None:
    """Generate a user story for a single prospect.

    Returns the generated story dict, or None if skipped.
    """
    nome = prospect.get("Nome", "")
    if not nome:
        print(f"  SKIP: No name provided")
        return None

    # Dedup check: reject if prospect already exists in Notion
    existing = check_duplicate(nome)
    if existing:
        print(f"  SKIP: Duplicate in Notion — '{nome}' already exists (page={existing['page_id']}, status={existing.get('Status', '')})")
        return None

    # Generate slug
    raw_slug = generate_slug(nome)
    slug = ensure_unique_slug(raw_slug, existing_slugs)

    # Dedup check: reject if slug already used
    if check_slug_duplicate(slug):
        print(f"  SKIP: Slug '{slug}' already in use (Notion or disk)")
        return None

    # Check if site already exists
    site_dir = SITE_DEMO_DIR / slug
    if site_dir.exists():
        print(f"  SKIP: Site already exists at site-demo/{slug}/")
        return None

    # Get next IDs
    us_id, priority = get_next_us_id(prd)
    previous_us_id = get_last_us_id(prd)

    # Build story
    story = build_user_story(prospect, us_id, priority, slug, previous_us_id)

    print(f"  {us_id}: {nome}")
    print(f"    Slug: {slug}")
    print(f"    URL:  {SITE_DEMO_BASE_URL}/{slug}/")

    if dry_run:
        print(f"    [DRY RUN] Would append to prd.json")
        return story

    # Append to prd.json
    prd["userStories"].append(story)
    save_prd(prd)
    existing_slugs.add(slug)

    print(f"    Appended to prd.json")

    return story


def main():
    parser = argparse.ArgumentParser(
        description="Generate user stories from Notion prospects"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Generate for a specific prospect by name",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Path to a JSON file with prospect data (array of objects)",
    )
    args = parser.parse_args()

    prd = load_prd()
    existing_slugs = get_existing_slugs()

    print(f"Current prd.json: {len(prd.get('userStories', []))} stories")
    print(f"Existing site-demo dirs: {len(existing_slugs)}")
    print()

    if args.from_json:
        # Load prospects from a JSON file
        with open(args.from_json, "r", encoding="utf-8") as f:
            prospects = json.load(f)

        if args.name:
            prospects = [p for p in prospects if args.name.lower() in p.get("Nome", "").lower()]

        print(f"Processing {len(prospects)} prospect(s)...")
        generated = []
        for prospect in prospects:
            result = generate_for_prospect(prospect, prd, existing_slugs, args.dry_run)
            if result:
                generated.append(result)

        print(f"\nGenerated {len(generated)} user story(ies)")
    else:
        print("No input provided. Use --from-json to supply prospect data.")
        print()
        print("Example workflow with Claude Code MCP:")
        print("  1. Search Notion: notion-search query='Qualificado'")
        print("  2. Fetch each prospect: notion-fetch id=<page_id>")
        print("  3. Save to JSON: prospects.json")
        print("  4. Run: python3 scripts/site_orchestrator.py --from-json prospects.json")
        print("  5. Ralph TUI processes new entries in prd.json")
        print("  6. Update Notion: notion_outbox_enqueue + notion_outbox_worker (or notion_update_from_prd --process)")


if __name__ == "__main__":
    main()
