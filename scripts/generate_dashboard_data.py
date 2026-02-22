#!/usr/bin/env python3
"""
Pixel Alchemy — Dashboard Data Generator
==========================================

Scans the codebase (site-demo/, prd.json, harmonizacao.csv, git log)
and produces admin/dashboard/dashboard-data.json consumed by the dashboard UI.

Usage:
    python3 scripts/generate_dashboard_data.py
"""

import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import shared config
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from config import (  # type: ignore[import-untyped]
    CSV_PATH,
    PRD_JSON_PATH,
    PROJECT_ROOT,
    SITE_DEMO_BASE_URL,
    SITE_DEMO_DIR,
    STATUS_PIPELINE,
)

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
OUTPUT_DIR = PROJECT_ROOT / "admin" / "dashboard"
OUTPUT_JSON = OUTPUT_DIR / "dashboard-data.json"

# ---------------------------------------------------------------------------
# Niche classification patterns
# ---------------------------------------------------------------------------
NICHE_DIR_PATTERNS = {
    "Dentista": re.compile(
        r"(odonto|dental|dent|oral|implant|sorriso|smile|ortodon|clareamento"
        r"|endodont|protese|buco|maxilo|periodon)",
        re.IGNORECASE,
    ),
    "Veterinaria": re.compile(
        r"(vet|veterina|animal|pet[ -]?care|fauna|zoo|bicho|pata|canil"
        r"|felino|equino|silvestr)",
        re.IGNORECASE,
    ),
    "Harmonizacao": re.compile(
        r"(harmoni|estetic|estetica|aesthet|beauty[ -]?clinic|clinic[ao]"
        r"|belle|glamor|pele|skin|derma|botox|preench|filler|livhera"
        r"|botoesthetic|botolifting|7[ -]?peles|rejuven)",
        re.IGNORECASE,
    ),
    "Beleza": re.compile(
        r"(salao|salon|beleza|beauty|cabelo|hair|nail|unha|manicure"
        r"|cilio|lash|sobrancelha|brow|coloracao|mechas|loiro|blond"
        r"|penteado|escova|make[ -]?up|maquiag)",
        re.IGNORECASE,
    ),
    "Barbearia": re.compile(
        r"(barb[ea]|barber|beard|corte[ -]?masc|platinado|pigment)",
        re.IGNORECASE,
    ),
    "Pet Shop": re.compile(
        r"(pet[ -]?shop|petshop|racao|acessorio[ -]?pet|banho[ -]?e[ -]?tosa)",
        re.IGNORECASE,
    ),
    "Pizzaria": re.compile(
        r"(pizza|pizzaria|forno[ -]?a[ -]?lenha)",
        re.IGNORECASE,
    ),
    "Padaria": re.compile(
        r"(padaria|bakery|panificadora|pao[ -]?artesanal|fermentacao)",
        re.IGNORECASE,
    ),
    "Acougue": re.compile(
        r"(acougue|butcher|carne|angus|premium[ -]?meat|churrasco)",
        re.IGNORECASE,
    ),
}

NICHE_HTML_PATTERNS = {
    "Dentista": re.compile(
        r"(odontolog|dentist|implante|clareamento|ortodont|endodont"
        r"|protese|canal|aparelho.ortod|faceta|lente.contato.dental"
        r"|sorriso|dente|gengiva|bucal)",
        re.IGNORECASE,
    ),
    "Veterinaria": re.compile(
        r"(veterinar|animal|pet|cachorro|gato|felino|canino"
        r"|consulta.veterinar|vacinacao.animal|castracao|cirurgia.vet"
        r"|emergencia.animal|24.?h.+vet|vet.+24.?h)",
        re.IGNORECASE,
    ),
    "Harmonizacao": re.compile(
        r"(harmoniza|estetica|botox|preenchimento|bioestimulador"
        r"|fios.pdo|sculptra|lipo.enzima|peeling|microagulhamento"
        r"|rejuvenescimento|toxina.botulinica|acido.hialuronico)",
        re.IGNORECASE,
    ),
    "Beleza": re.compile(
        r"(salao|salon|cabelo|hair|coloracao|mechas|corte.feminino"
        r"|escova|manicure|pedicure|nail|unha|cilio|lash|sobrancelha"
        r"|design.sobrancelha|maquiagem)",
        re.IGNORECASE,
    ),
    "Barbearia": re.compile(
        r"(barbearia|barber|corte.masculino|barba|degrade|pigmentacao"
        r"|platinado|navalha|barbeiro)",
        re.IGNORECASE,
    ),
    "Pet Shop": re.compile(
        r"(pet.?shop|racao|banho.?e.?tosa|acessorio.pet|brinquedo.pet)",
        re.IGNORECASE,
    ),
    "Pizzaria": re.compile(
        r"(pizza|pizzaria|forno.lenha|massa.artesanal|delivery.pizza)",
        re.IGNORECASE,
    ),
    "Padaria": re.compile(
        r"(padaria|panificadora|pao.artesanal|fermentacao.natural"
        r"|confeitaria|bolo|croissant)",
        re.IGNORECASE,
    ),
    "Acougue": re.compile(
        r"(acougue|carne|angus|picanha|corte.premium|churrasco"
        r"|bovino|suino|frango.caipira)",
        re.IGNORECASE,
    ),
}


# ---------------------------------------------------------------------------
# 1. classify_niche
# ---------------------------------------------------------------------------
def classify_niche(dirname: str, html_content: str) -> str:
    """Classify a site into a niche based on its directory name and HTML content."""
    # First pass: match on directory name
    for niche, pattern in NICHE_DIR_PATTERNS.items():
        if pattern.search(dirname):
            return niche

    # Second pass: match on HTML content (first 5000 chars for speed)
    snippet = html_content[:5000] if html_content else ""
    for niche, pattern in NICHE_HTML_PATTERNS.items():
        if pattern.search(snippet):
            return niche

    # Extended HTML scan (full content) as last resort
    for niche, pattern in NICHE_HTML_PATTERNS.items():
        if pattern.search(html_content):
            return niche

    return "Outro"


# ---------------------------------------------------------------------------
# 2. extract_seo_meta
# ---------------------------------------------------------------------------
def extract_seo_meta(html_path: Path) -> dict:
    """Extract SEO-relevant meta tags from an HTML file using regex."""
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return _empty_seo()

    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None

    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    description = desc_match.group(1).strip() if desc_match else None

    kw_match = re.search(
        r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    keywords = kw_match.group(1).strip() if kw_match else None

    og_title_match = re.search(
        r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    og_title = og_title_match.group(1).strip() if og_title_match else None

    og_desc_match = re.search(
        r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    og_description = og_desc_match.group(1).strip() if og_desc_match else None

    og_image_match = re.search(
        r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    og_image = og_image_match.group(1).strip() if og_image_match else None

    canonical_match = re.search(
        r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    canonical = canonical_match.group(1).strip() if canonical_match else None

    json_ld = bool(re.search(
        r'<script\s+type=["\']application/ld\+json["\']',
        content,
        re.IGNORECASE,
    ))

    robots_match = re.search(
        r'<meta\s+name=["\']robots["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    robots = robots_match.group(1).strip() if robots_match else None

    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
    has_h1 = h1_match is not None

    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image,
        "canonical": canonical,
        "json_ld": json_ld,
        "robots": robots,
        "has_h1": has_h1,
    }


def _empty_seo() -> dict:
    return {
        "title": None,
        "description": None,
        "keywords": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "canonical": None,
        "json_ld": False,
        "robots": None,
        "has_h1": False,
    }


# ---------------------------------------------------------------------------
# 3. compute_seo_score
# ---------------------------------------------------------------------------
def compute_seo_score(meta: dict) -> int:
    """
    Score 0-100 based on presence of SEO tags.

    Weights:
        title=15, description=15, keywords=10, OG tags=20 (5 each for title/desc/image + 5 any OG),
        canonical=15, json_ld=15, robots=5, h1=5
    """
    score = 0
    if meta.get("title"):
        score += 15
    if meta.get("description"):
        score += 15
    if meta.get("keywords"):
        score += 10
    # OG tags: 5 each for title, description, image; 5 for having any OG
    has_any_og = False
    if meta.get("og_title"):
        score += 5
        has_any_og = True
    if meta.get("og_description"):
        score += 5
        has_any_og = True
    if meta.get("og_image"):
        score += 5
        has_any_og = True
    if has_any_og:
        score += 5
    if meta.get("canonical"):
        score += 15
    if meta.get("json_ld"):
        score += 15
    if meta.get("robots"):
        score += 5
    if meta.get("has_h1"):
        score += 5
    return min(score, 100)


# ---------------------------------------------------------------------------
# 4. scan_all_sites
# ---------------------------------------------------------------------------
def scan_all_sites() -> dict:
    """Scan all sites in site-demo/, classify, extract SEO, compute scores."""
    sites_list = []
    niche_counts = {}
    seo_totals = {
        "with_title": 0,
        "with_description": 0,
        "with_keywords": 0,
        "with_og_tags": 0,
        "with_json_ld": 0,
        "with_canonical": 0,
        "with_robots": 0,
        "with_h1": 0,
    }
    total_seo_score = 0

    if not SITE_DEMO_DIR.exists():
        print(f"Warning: {SITE_DEMO_DIR} not found", file=sys.stderr)
        return {
            "total_count": 0,
            "niche_distribution": {},
            "seo_summary": {
                "avg_score": 0,
                **seo_totals,
            },
            "list": [],
        }

    dirs = sorted(
        d for d in SITE_DEMO_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

    for site_dir in dirs:
        slug = site_dir.name
        html_path = site_dir / "index.html"

        if not html_path.exists():
            continue

        try:
            html_content = html_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            html_content = ""

        niche = classify_niche(slug, html_content)
        seo = extract_seo_meta(html_path)
        seo_score = compute_seo_score(seo)

        niche_counts[niche] = niche_counts.get(niche, 0) + 1
        total_seo_score += seo_score

        if seo["title"]:
            seo_totals["with_title"] += 1
        if seo["description"]:
            seo_totals["with_description"] += 1
        if seo["keywords"]:
            seo_totals["with_keywords"] += 1
        if seo["og_title"] or seo["og_description"] or seo["og_image"]:
            seo_totals["with_og_tags"] += 1
        if seo["json_ld"]:
            seo_totals["with_json_ld"] += 1
        if seo["canonical"]:
            seo_totals["with_canonical"] += 1
        if seo["robots"]:
            seo_totals["with_robots"] += 1
        if seo["has_h1"]:
            seo_totals["with_h1"] += 1

        url = f"{SITE_DEMO_BASE_URL}/{slug}/"

        sites_list.append({
            "slug": slug,
            "niche": niche,
            "url": url,
            "seo_score": seo_score,
            "seo": {
                "title": seo["title"],
                "description": seo["description"],
                "keywords": seo["keywords"],
                "og_title": seo["og_title"],
                "canonical": seo["canonical"],
                "json_ld": seo["json_ld"],
                "robots": seo["robots"],
                "has_h1": seo["has_h1"],
            },
        })

    total = len(sites_list)
    avg_score = round(total_seo_score / total, 1) if total > 0 else 0

    return {
        "total_count": total,
        "niche_distribution": dict(sorted(niche_counts.items(), key=lambda x: -x[1])),
        "seo_summary": {
            "avg_score": avg_score,
            **seo_totals,
        },
        "list": sites_list,
    }


# ---------------------------------------------------------------------------
# 5. parse_prd
# ---------------------------------------------------------------------------
def parse_prd() -> dict:
    """Parse prd.json for user story statistics."""
    if not PRD_JSON_PATH.exists():
        return {"total_stories": 0, "completed": 0, "pending": 0, "completion_rate": 0.0}

    try:
        data = json.loads(PRD_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"total_stories": 0, "completed": 0, "pending": 0, "completion_rate": 0.0}

    stories = data.get("userStories", [])
    total = len(stories)
    completed = sum(1 for s in stories if s.get("passes") is True)
    pending = total - completed

    rate = round((completed / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_stories": total,
        "completed": completed,
        "pending": pending,
        "completion_rate": rate,
    }


# ---------------------------------------------------------------------------
# 6. parse_csv
# ---------------------------------------------------------------------------
def parse_csv() -> dict:
    """Parse harmonizacao.csv for legacy record count."""
    if not CSV_PATH.exists():
        return {"total_records": 0}

    try:
        with open(CSV_PATH, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Subtract header row
        total = max(0, len(rows) - 1)
    except Exception:
        total = 0

    return {"total_records": total}


# ---------------------------------------------------------------------------
# 7. build_timeline
# ---------------------------------------------------------------------------
def build_timeline() -> list:
    """
    Build a cumulative timeline from git log.
    Executes git log once, filters for 'feat: US-' commits.
    """
    try:
        result = subprocess.run(
            [
                "git", "log",
                "--format=%aI|%s",
                "--grep=feat: US-",
                "--all",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []

    entries = []
    for line in lines:
        if "|" not in line:
            continue
        date_str, subject = line.split("|", 1)
        # Extract date (YYYY-MM-DD from ISO format)
        date = date_str[:10]
        # Extract US-XXX from subject
        us_match = re.search(r"US-(\d+)", subject)
        us_id = f"US-{us_match.group(1)}" if us_match else None
        # Clean title: remove "feat: US-XXX - " prefix
        title = re.sub(r"^feat:\s*US-\d+\s*-\s*", "", subject).strip()

        if us_id:
            entries.append({
                "date": date,
                "us_id": us_id,
                "title": title,
            })

    # Sort by date ascending, then by US number
    entries.sort(key=lambda e: (e["date"], e["us_id"]))

    # Add cumulative count
    timeline = []
    for i, entry in enumerate(entries, 1):
        timeline.append({
            **entry,
            "cumulative_count": i,
        })

    return timeline


# ---------------------------------------------------------------------------
# 8. build_pipeline
# ---------------------------------------------------------------------------
def build_pipeline() -> dict:
    """Build pipeline structure from STATUS_PIPELINE config."""
    counts = {stage: 0 for stage in STATUS_PIPELINE}
    # Default: all completed sites go to "Site Pronto"
    # This is a static view; CRM integration would update dynamically
    return {
        "stages": list(STATUS_PIPELINE),
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# 9. get_seo_clusters
# ---------------------------------------------------------------------------
def get_seo_clusters(niche_counts: dict) -> dict:
    """
    Return SEO keyword clusters per niche.
    Data based on Brazilian market research for Ribeirao Preto region.
    """
    clusters = {
        "Dentista": {
            "label": "Dentista",
            "color": "#e07856",
            "clusters": [
                {
                    "keyword": "dentista ribeirao preto",
                    "related": [
                        "dentista em ribeirao preto sp",
                        "melhor dentista ribeirao preto",
                        "clinica odontologica ribeirao preto",
                    ],
                    "volume": 2400,
                    "competition": "alta",
                    "opportunity": 65,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "implante dentario ribeirao preto",
                    "related": [
                        "implante dental preco ribeirao preto",
                        "implante dentario valor",
                        "carga imediata ribeirao preto",
                    ],
                    "volume": 1300,
                    "competition": "alta",
                    "opportunity": 60,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "clareamento dental ribeirao preto",
                    "related": [
                        "clareamento a laser ribeirao preto",
                        "clareamento dental preco",
                        "branqueamento dental",
                    ],
                    "volume": 880,
                    "competition": "media",
                    "opportunity": 75,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "ortodontia ribeirao preto",
                    "related": [
                        "ortodontista ribeirao preto",
                        "aparelho invisivel ribeirao preto",
                        "invisalign ribeirao preto",
                    ],
                    "volume": 720,
                    "competition": "media",
                    "opportunity": 70,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "faceta dentaria ribeirao preto",
                    "related": [
                        "lente de contato dental ribeirao preto",
                        "faceta de porcelana preco",
                        "lentes de contato dental valor",
                    ],
                    "volume": 590,
                    "competition": "media",
                    "opportunity": 72,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "emergencia dentaria ribeirao preto",
                    "related": [
                        "dentista 24 horas ribeirao preto",
                        "urgencia odontologica",
                        "dor de dente emergencia",
                    ],
                    "volume": 480,
                    "competition": "baixa",
                    "opportunity": 85,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "protese dentaria ribeirao preto",
                    "related": [
                        "protese fixa ribeirao preto",
                        "protocolo dentario ribeirao preto",
                        "dentadura fixa",
                    ],
                    "volume": 390,
                    "competition": "media",
                    "opportunity": 68,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "endodontia ribeirao preto",
                    "related": [
                        "tratamento de canal ribeirao preto",
                        "canal dentario preco",
                        "endodontista",
                    ],
                    "volume": 260,
                    "competition": "baixa",
                    "opportunity": 80,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "odontopediatria ribeirao preto",
                    "related": [
                        "dentista infantil ribeirao preto",
                        "dentista para crianca",
                        "odontopediatra",
                    ],
                    "volume": 210,
                    "competition": "baixa",
                    "opportunity": 82,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
                {
                    "keyword": "periodontia ribeirao preto",
                    "related": [
                        "tratamento gengiva ribeirao preto",
                        "periodontista",
                        "doenca periodontal tratamento",
                    ],
                    "volume": 170,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Dentista", 0),
                },
            ],
        },
        "Veterinaria": {
            "label": "Veterinaria",
            "color": "#8ba888",
            "clusters": [
                {
                    "keyword": "veterinario ribeirao preto",
                    "related": [
                        "clinica veterinaria ribeirao preto",
                        "vet ribeirao preto",
                        "medico veterinario ribeirao",
                    ],
                    "volume": 1900,
                    "competition": "alta",
                    "opportunity": 62,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "veterinario 24 horas ribeirao preto",
                    "related": [
                        "emergencia veterinaria ribeirao preto",
                        "pronto socorro animal ribeirao",
                        "vet 24h ribeirao",
                    ],
                    "volume": 1600,
                    "competition": "alta",
                    "opportunity": 58,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "veterinario de silvestres ribeirao preto",
                    "related": [
                        "vet exoticos ribeirao preto",
                        "veterinario aves ribeirao",
                        "veterinario repteis",
                    ],
                    "volume": 480,
                    "competition": "baixa",
                    "opportunity": 88,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "veterinario felino ribeirao preto",
                    "related": [
                        "clinica de gatos ribeirao preto",
                        "vet especialista em gatos",
                        "cat friendly clinic",
                    ],
                    "volume": 390,
                    "competition": "baixa",
                    "opportunity": 85,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "castracao ribeirao preto",
                    "related": [
                        "castracao cachorro preco ribeirao",
                        "castrar gato ribeirao preto",
                        "castracao popular",
                    ],
                    "volume": 720,
                    "competition": "media",
                    "opportunity": 70,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "veterinario domiciliar ribeirao preto",
                    "related": [
                        "atendimento veterinario em casa",
                        "vet em domicilio ribeirao",
                        "consulta veterinaria domiciliar",
                    ],
                    "volume": 320,
                    "competition": "baixa",
                    "opportunity": 82,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "dermatologia veterinaria ribeirao preto",
                    "related": [
                        "dermatologista animal",
                        "alergia cachorro veterinario",
                        "doenca de pele animal",
                    ],
                    "volume": 210,
                    "competition": "baixa",
                    "opportunity": 80,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "ortopedia veterinaria ribeirao preto",
                    "related": [
                        "cirurgia ortopedica animal",
                        "fratura animal tratamento",
                        "ortopedista veterinario",
                    ],
                    "volume": 170,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "vacinacao animal ribeirao preto",
                    "related": [
                        "vacina cachorro ribeirao",
                        "vacina gato ribeirao preto",
                        "calendario vacinacao pet",
                    ],
                    "volume": 260,
                    "competition": "baixa",
                    "opportunity": 76,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
                {
                    "keyword": "cardiologia veterinaria ribeirao preto",
                    "related": [
                        "cardio vet ribeirao",
                        "ecocardiograma animal",
                        "cardiologista veterinario",
                    ],
                    "volume": 110,
                    "competition": "baixa",
                    "opportunity": 75,
                    "sites_targeting": niche_counts.get("Veterinaria", 0),
                },
            ],
        },
        "Harmonizacao": {
            "label": "Harmonizacao",
            "color": "#b5a6c8",
            "clusters": [
                {
                    "keyword": "harmonizacao facial ribeirao preto",
                    "related": [
                        "harmonizacao orofacial ribeirao",
                        "harmonizacao facial preco",
                        "clinica harmonizacao ribeirao",
                    ],
                    "volume": 1600,
                    "competition": "alta",
                    "opportunity": 60,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "botox ribeirao preto",
                    "related": [
                        "toxina botulinica ribeirao preto",
                        "botox preco ribeirao",
                        "aplicacao botox",
                    ],
                    "volume": 1300,
                    "competition": "alta",
                    "opportunity": 55,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "preenchimento labial ribeirao preto",
                    "related": [
                        "preenchimento acido hialuronico",
                        "preenchimento facial preco",
                        "filler labial ribeirao",
                    ],
                    "volume": 880,
                    "competition": "media",
                    "opportunity": 68,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "bioestimulador de colageno ribeirao preto",
                    "related": [
                        "sculptra ribeirao preto",
                        "radiesse ribeirao preto",
                        "bioestimulador preco",
                    ],
                    "volume": 590,
                    "competition": "media",
                    "opportunity": 72,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "fios de pdo ribeirao preto",
                    "related": [
                        "lifting com fios ribeirao",
                        "fios tensores preco",
                        "sustentacao facial fios",
                    ],
                    "volume": 390,
                    "competition": "baixa",
                    "opportunity": 80,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "lipo de papada ribeirao preto",
                    "related": [
                        "lipo enzimatica ribeirao",
                        "reduzir papada sem cirurgia",
                        "enzimas para papada",
                    ],
                    "volume": 320,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "peeling quimico ribeirao preto",
                    "related": [
                        "peeling facial ribeirao",
                        "peeling de fenol",
                        "peeling profundo",
                    ],
                    "volume": 260,
                    "competition": "baixa",
                    "opportunity": 76,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
                {
                    "keyword": "microagulhamento ribeirao preto",
                    "related": [
                        "micro needling ribeirao",
                        "dermapen ribeirao preto",
                        "microagulhamento preco",
                    ],
                    "volume": 210,
                    "competition": "baixa",
                    "opportunity": 74,
                    "sites_targeting": niche_counts.get("Harmonizacao", 0),
                },
            ],
        },
        "Beleza": {
            "label": "Beleza",
            "color": "#c4a68a",
            "clusters": [
                {
                    "keyword": "salao de beleza ribeirao preto",
                    "related": [
                        "melhor salao ribeirao preto",
                        "salao de beleza feminino ribeirao",
                        "cabeleireiro ribeirao preto",
                    ],
                    "volume": 1900,
                    "competition": "alta",
                    "opportunity": 58,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
                {
                    "keyword": "coloracao cabelo ribeirao preto",
                    "related": [
                        "mechas ribeirao preto",
                        "luzes cabelo ribeirao",
                        "loiro platinado salao",
                    ],
                    "volume": 880,
                    "competition": "media",
                    "opportunity": 70,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
                {
                    "keyword": "manicure ribeirao preto",
                    "related": [
                        "manicure e pedicure ribeirao",
                        "nail designer ribeirao preto",
                        "unha em gel ribeirao",
                    ],
                    "volume": 720,
                    "competition": "media",
                    "opportunity": 65,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
                {
                    "keyword": "extensao de cilios ribeirao preto",
                    "related": [
                        "mega hair cilios ribeirao",
                        "volume russo cilios",
                        "cilios fio a fio ribeirao",
                    ],
                    "volume": 590,
                    "competition": "media",
                    "opportunity": 72,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
                {
                    "keyword": "design de sobrancelha ribeirao preto",
                    "related": [
                        "micropigmentacao sobrancelha ribeirao",
                        "sobrancelha henna ribeirao",
                        "design sobrancelha preco",
                    ],
                    "volume": 480,
                    "competition": "media",
                    "opportunity": 68,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
                {
                    "keyword": "escova progressiva ribeirao preto",
                    "related": [
                        "progressiva ribeirao preto",
                        "alisamento capilar",
                        "tratamento capilar ribeirao",
                    ],
                    "volume": 390,
                    "competition": "baixa",
                    "opportunity": 75,
                    "sites_targeting": niche_counts.get("Beleza", 0),
                },
            ],
        },
        "Barbearia": {
            "label": "Barbearia",
            "color": "#1a1f2e",
            "clusters": [
                {
                    "keyword": "barbearia ribeirao preto",
                    "related": [
                        "melhor barbearia ribeirao preto",
                        "barbeiro ribeirao preto",
                        "barber shop ribeirao",
                    ],
                    "volume": 1300,
                    "competition": "alta",
                    "opportunity": 60,
                    "sites_targeting": niche_counts.get("Barbearia", 0),
                },
                {
                    "keyword": "corte masculino ribeirao preto",
                    "related": [
                        "corte degrade ribeirao",
                        "corte social ribeirao preto",
                        "corte masculino preco",
                    ],
                    "volume": 590,
                    "competition": "media",
                    "opportunity": 68,
                    "sites_targeting": niche_counts.get("Barbearia", 0),
                },
                {
                    "keyword": "barba ribeirao preto",
                    "related": [
                        "design de barba ribeirao",
                        "barba alinhada preco",
                        "barbeiro especialista barba",
                    ],
                    "volume": 320,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Barbearia", 0),
                },
                {
                    "keyword": "pigmentacao capilar ribeirao preto",
                    "related": [
                        "micropigmentacao capilar ribeirao",
                        "tratamento calvicie ribeirao",
                        "pigmentacao capilar preco",
                    ],
                    "volume": 210,
                    "competition": "baixa",
                    "opportunity": 82,
                    "sites_targeting": niche_counts.get("Barbearia", 0),
                },
                {
                    "keyword": "platinado masculino ribeirao preto",
                    "related": [
                        "descoloracao masculina ribeirao",
                        "platinado barbeiro",
                        "loiro masculino",
                    ],
                    "volume": 170,
                    "competition": "baixa",
                    "opportunity": 80,
                    "sites_targeting": niche_counts.get("Barbearia", 0),
                },
            ],
        },
        "Pet Shop": {
            "label": "Pet Shop",
            "color": "#65a3b8",
            "clusters": [
                {
                    "keyword": "pet shop ribeirao preto",
                    "related": [
                        "loja pet ribeirao preto",
                        "pet shop 24h ribeirao",
                        "melhor pet shop ribeirao",
                    ],
                    "volume": 1600,
                    "competition": "alta",
                    "opportunity": 55,
                    "sites_targeting": niche_counts.get("Pet Shop", 0),
                },
                {
                    "keyword": "racao premium ribeirao preto",
                    "related": [
                        "racao natural ribeirao",
                        "racao golden ribeirao preto",
                        "racao royal canin ribeirao",
                    ],
                    "volume": 480,
                    "competition": "media",
                    "opportunity": 65,
                    "sites_targeting": niche_counts.get("Pet Shop", 0),
                },
                {
                    "keyword": "acessorios pet ribeirao preto",
                    "related": [
                        "coleira personalizada ribeirao",
                        "cama pet ribeirao preto",
                        "brinquedo cachorro ribeirao",
                    ],
                    "volume": 210,
                    "competition": "baixa",
                    "opportunity": 75,
                    "sites_targeting": niche_counts.get("Pet Shop", 0),
                },
            ],
        },
        "Pizzaria": {
            "label": "Pizzaria",
            "color": "#d4543b",
            "clusters": [
                {
                    "keyword": "pizzaria ribeirao preto",
                    "related": [
                        "melhor pizza ribeirao preto",
                        "pizza delivery ribeirao",
                        "pizzaria perto de mim",
                    ],
                    "volume": 2900,
                    "competition": "alta",
                    "opportunity": 50,
                    "sites_targeting": niche_counts.get("Pizzaria", 0),
                },
                {
                    "keyword": "pizza artesanal ribeirao preto",
                    "related": [
                        "pizza forno a lenha ribeirao",
                        "pizzaria artesanal delivery",
                        "pizza napolitana ribeirao",
                    ],
                    "volume": 480,
                    "competition": "media",
                    "opportunity": 72,
                    "sites_targeting": niche_counts.get("Pizzaria", 0),
                },
            ],
        },
        "Padaria": {
            "label": "Padaria",
            "color": "#d4a76a",
            "clusters": [
                {
                    "keyword": "padaria ribeirao preto",
                    "related": [
                        "melhor padaria ribeirao preto",
                        "padaria artesanal ribeirao",
                        "cafe da manha ribeirao",
                    ],
                    "volume": 1600,
                    "competition": "alta",
                    "opportunity": 55,
                    "sites_targeting": niche_counts.get("Padaria", 0),
                },
                {
                    "keyword": "pao artesanal ribeirao preto",
                    "related": [
                        "pao fermentacao natural ribeirao",
                        "sourdough ribeirao preto",
                        "padaria fermentacao natural",
                    ],
                    "volume": 320,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Padaria", 0),
                },
            ],
        },
        "Acougue": {
            "label": "Acougue",
            "color": "#8b2500",
            "clusters": [
                {
                    "keyword": "acougue ribeirao preto",
                    "related": [
                        "acougue premium ribeirao",
                        "casa de carnes ribeirao preto",
                        "melhor acougue ribeirao",
                    ],
                    "volume": 880,
                    "competition": "media",
                    "opportunity": 65,
                    "sites_targeting": niche_counts.get("Acougue", 0),
                },
                {
                    "keyword": "carne angus ribeirao preto",
                    "related": [
                        "angus ribeirao preto",
                        "carne premium ribeirao",
                        "picanha angus ribeirao",
                    ],
                    "volume": 260,
                    "competition": "baixa",
                    "opportunity": 78,
                    "sites_targeting": niche_counts.get("Acougue", 0),
                },
            ],
        },
    }

    return clusters


# ---------------------------------------------------------------------------
# 10. main
# ---------------------------------------------------------------------------
def main():
    """Orchestrate all data collection and write dashboard-data.json."""
    print("Pixel Alchemy Dashboard Data Generator")
    print("=" * 42)

    print("Scanning sites...")
    sites_data = scan_all_sites()
    print(f"  Found {sites_data['total_count']} sites")
    print(f"  Niches: {sites_data['niche_distribution']}")
    print(f"  Avg SEO score: {sites_data['seo_summary']['avg_score']}")

    print("Parsing PRD...")
    prd_data = parse_prd()
    print(f"  {prd_data['completed']}/{prd_data['total_stories']} stories completed ({prd_data['completion_rate']}%)")

    print("Parsing CSV (legacy)...")
    csv_data = parse_csv()
    print(f"  {csv_data['total_records']} records")

    print("Building timeline from git log...")
    timeline = build_timeline()
    print(f"  {len(timeline)} timeline entries")

    print("Building pipeline...")
    pipeline = build_pipeline()
    # Update pipeline with real data: sites that exist = "Site Pronto"
    pipeline["counts"]["Site Pronto"] = sites_data["total_count"]

    print("Loading SEO clusters...")
    seo_clusters = get_seo_clusters(sites_data["niche_distribution"])
    print(f"  {len(seo_clusters)} niches with keyword data")

    # Assemble final JSON
    dashboard_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sites": sites_data,
        "prd": prd_data,
        "csv_legacy": csv_data,
        "pipeline": pipeline,
        "timeline": timeline,
        "seo_clusters": seo_clusters,
    }

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write JSON
    OUTPUT_JSON.write_text(
        json.dumps(dashboard_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nDashboard data written to: {OUTPUT_JSON}")
    print(f"JSON size: {OUTPUT_JSON.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
