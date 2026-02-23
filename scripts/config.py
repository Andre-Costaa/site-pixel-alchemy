"""
Pixel Alchemy — Centralized Configuration
==========================================

Shared constants for all automation scripts.
"""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SITE_DEMO_DIR = PROJECT_ROOT / "site-demo"
PRD_JSON_PATH = PROJECT_ROOT / "tasks" / "prd.json"
PRD_JSON_LEGACY_PATH = PROJECT_ROOT / "prd.json"
CSV_PATH = PROJECT_ROOT / "harmonizacao.csv"

# Notion IDs
NOTION_DATABASE_ID = "2f76f51e-b8a5-8088-a52c-db29fc3c1f81"
NOTION_DATA_SOURCE_ID = "2f76f51e-b8a5-800b-8c7e-000bf9f86798"

# Notion outbox root (local, not committed)
NOTION_OUTBOX_DIR = PROJECT_ROOT / ".notion-outbox"

# URLs
BASE_URL = "https://www.pixelalchemy.com.br"
SITE_DEMO_BASE_URL = f"{BASE_URL}/site-demo"

# ID prefixes per niche (used for generating prospect IDs)
NICHE_PREFIXES = {
    "Dentista": "DEN",
    "Veterinária": "VET",
    "Harmonização": "HAR",
    "Beleza": "BEL",
    "Pizzaria": "PIZ",
    "Barbearia": "BAR",
    "Padaria": "PAD",
    "Açougue": "ACG",
    "Pet Shop": "PET",
}

# Status pipeline
STATUS_PIPELINE = [
    "Lead",
    "Qualificado",
    "Site em Criação",
    "Mensagem Pronta",
    "Enviado",
    "Respondeu",
    "Reunião",
    "Proposta",
    "Fechado",
    "Perdido",
    "Descartado",
]
