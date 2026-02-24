"""
Pixel Alchemy — Centralized Configuration
==========================================

Shared constants for all automation scripts.
"""

import os
import re
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent


def _load_dotenv_if_present(dotenv_path: Path) -> None:
    """Load environment variables from .env if present.

    Values from the process environment take precedence over .env entries.
    """
    if not dotenv_path.exists() or not dotenv_path.is_file():
        return

    key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key_pattern.match(key):
            continue

        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


# Auto-load project .env so agents/scripts don't depend on manual `source .env`.
_load_dotenv_if_present(PROJECT_ROOT / ".env")

SITE_DEMO_DIR = PROJECT_ROOT / "site-demo"
# Canonical PRD path.
PRD_JSON_PATH = PROJECT_ROOT / "prd.json"
# Legacy path kept in sync for backward compatibility.
PRD_JSON_LEGACY_PATH = PROJECT_ROOT / "tasks" / "prd.json"
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
