# CLAUDE.md

## Quando Ler Este Documento

- Ao criar novos sites demo para clientes
- Ao trabalhar com codigo HTML/CSS/JS
- Ao definir convencoes de design ou arquitetura
- Para duvidas sobre stack tecnico (NAO para pipeline de prospeccao)

**Para pipeline de prospeccao e automacao, leia AGENTS.md primeiro.**

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pixel Alchemy is a digital agency that produces single-page promotional websites for Brazilian clinics (aesthetics, dental, veterinary, beauty). The repo contains **two layers**:

1. **Root site** (`index.html`, `styles.css`, `script.js`) — the agency's own promotional page at pixelalchemy.com.br
2. **Client sites** (`site-demo/<client-name>/`) — 160+ individual client websites, each deployed as a subdirectory of the main domain (e.g., `pixelalchemy.com.br/site-demo/dra-lara-costa/`)

Client data and prospect tracking lives in the **Notion CRM database**, which is the absolute source of truth. `harmonizacao.csv` and `prd.json` are operational artifacts only.

## Technology Stack

Pure HTML5, CSS3, and Vanilla JavaScript. No frameworks, no build process, no dependencies. Google Fonts: Bricolage Grotesque (display) + Plus Jakarta Sans (body).

## Development Commands

```bash
# Serve locally (needed for font loading and proper navigation)
python3 -m http.server 5500
# Then visit http://localhost:5500 (root site) or http://localhost:5500/site-demo/<client-name>/
```

No build, lint, or test commands exist. Manual visual QA at breakpoints 480px, 768px, 1024px, 1440px.

## Client Site Architecture

### Two file patterns coexist

- **Self-contained** (majority — ~133 sites): Single `index.html` with all CSS in `<style>` and all JS in `<script>` tags inline
- **Separated** (~12 early sites): Three files — `index.html`, `styles.css`, `script.js`

When creating new client sites, use the **self-contained single-file pattern** (it's the current standard).

### Standard section structure for client sites

Each client site follows the same section template, adapted to the business type:

1. **Navigation** — Auto-hides on scroll down, mobile hamburger menu
2. **Hero** — Value prop, CTAs, animated blobs/visual elements
3. **Services/Treatments** — Card grid (responsive: 1→2→3 columns)
4. **Process/How It Works** — Timeline or steps
5. **About/Differentials** — Stats counter, trust signals
6. **Testimonials** — Client reviews with star ratings
7. **FAQ** — Accordion
8. **Contact** — Form (name, email/phone, service selector, message) + business info
9. **Footer** — Links, legal info

Sections may be renamed or reordered per business niche (e.g., veterinary clinics emphasize "Emergência 24h", dental clinics emphasize "Tratamentos").

## Design System (Root Site + Template)

### Color system

All colors are CSS custom properties in `:root`. Each accent color has a `-light` variant.

- Base: `--color-charcoal`, `--color-cream`
- Accents: `--color-terracotta` (primary CTA), `--color-sage`, `--color-lavender`, `--color-clay`
- Gradients: `--gradient-warm` (terracotta→clay), `--gradient-cool` (sage→lavender)

Client sites customize these values per brand but follow the same variable naming pattern.

### Blobmorphism system

Blob shapes are the core design language — not mere decoration:

- `--border-radius-blob: 60% 40% 30% 70% / 60% 30% 70% 40%` creates organic shapes
- Hero blobs (`.blob-1` through `.blob-4`) use CSS `blur` + `backdrop-filter` + 20s transform animations
- Layered z-index for depth perception

### Animation system

Three approaches, all respecting `prefers-reduced-motion`:

1. **CSS keyframes**: Continuous effects (blob floating 6–20s, card floating, ripple)
2. **Intersection Observer**: Scroll-triggered `.wow-fade-up` / `.wow-fade-in` with `data-delay` for stagger (100ms increments), threshold 0.1, rootMargin -50px
3. **JavaScript-driven**: Counter animation (stats), tilt effect (service cards), parallax (blobs)

Use only `transform` and `opacity` for GPU acceleration.

### Responsive breakpoints

Mobile-first: base (<480px) → 480px → 768px → 1024px.

## Coding Conventions

- **HTML**: Semantic sections with `<section class="section-name" id="section-name">`
- **CSS**: 4-space indent, leverage existing `--color-*` / `--spacing-*` tokens, lowercase-kebab class names, sectioned comment blocks
- **JS**: Vanilla ES6, `const`/`let`, camelCase identifiers, modular sections under documented comment headers, `querySelector` APIs
- **No emojis** in any code or content — create SVG/image if an icon is needed

## Commit Convention

```
feat: US-XXX - Client Name - Site Completo
```

Each client site is a single commit as a user story (US-XXX, sequential numbering). Portuguese descriptions are standard. Commits should be concise and action-oriented.

## Visual QA

`.playwright-mcp/` contains PNG screenshots at multiple breakpoints for previously reviewed sites. When making UI changes, compare against these baselines. Key breakpoints to verify: 480px, 768px, 1024px, 1440px. Check: nav scroll behavior, hero animations, accordion, stats counter, contact form, mobile menu.

## CRM — Fonte de Verdade: SQLite

### Source of truth policy (2026-04-15)

**`prospects.db` (SQLite) e a UNICA fonte de verdade para prospeccao e automacao.**
Notion e um arquivo historico / referencia manual. Nunca escrever no Notion via automacao.

- **SQLite wins** para pipeline, status, e dados operacionais.
- Notion = leitura apenas para referencia de dados historicos.
- `harmonizacao.csv` e `prospects-novos-batch.json` = seed data, leitura apenas.

### Como atualizar antes de trabalhar

```bash
cd ~/site-pixel-alchemy
NOTION_API_TOKEN='ntn_...' python3 scripts/sync_notion_csv_to_sqlite.py && \
  python3 scripts/generate_crm_data.py
```

### Dashboard

**URL**: https://www.pixelalchemy.com.br/admin/dashboard/
**Senha**: `pixel2026`

### Dados reais (2026-04-15)

| Metrica | Valor |
|---------|-------|
| Total prospects | 308 |
| Com telefone | 279 |
| Pipeline: Lead | 149 |
| Pipeline: Contatado | 159 |
| Respondeu/Reuniao/Proposta/Fechado | 0 |

### Notion CRM — Referencia Historica

**Database**: `2f76f51e-b8a5-8088-a52c-db29fc3c1f81`
**Nota**: O campo `Telefone` no Notion e tipo `rich_text`, NAO `phone_number`.

### Database schema

| Property | Type | Values / Notes |
|---|---|---|
| **Nome** | title | Client/business name (primary key) |
| **ID** | text | Internal identifier (auto-generated by scripts) |
| **Nicho** | select | `Dentista`, `Veterinária`, `Harmonização`, `Beleza`, `Pizzaria`, `Barbearia`, `Padaria`, `Açougue`, `Pet Shop` |
| **Status** | select | `Lead` → `Qualificado` → `Site em Criação` → `Mensagem Pronta` → `Enviado` → `Respondeu` → `Reunião` → `Proposta` → `Fechado` / `Perdido` / `Descartado` |
| **Aprovado** | select | `Aprovado`, `Reprovado`, `Pendente` |
| **Venda** | select | `Sim`, `Não`, `Em negociação` |
| **Valor** | number (R$) | Deal value in BRL |
| **Telefone** | text | Phone number with area code |
| **Email** | text | Business or owner contact email (researched during site creation) |
| **Endereço** | text | Business full address |
| **Site** | text | Existing website URL (if any) |
| **URL Demo** | url | **CRITICAL**: Link to demo site `https://www.pixelalchemy.com.br/site-demo/<slug>/` |
| **Instagram** | text | Instagram handle or URL |
| **Facebook** | text | Facebook page URL |
| **Descrição** | text | Business description (used in site creation) |
| **Mensagem** | text | **CRITICAL**: Personalized outreach message (generated after site creation) |
| **Resposta** | text | Client's response to outreach |
| **Observações** | text | Internal notes |
| **Origem** | select | `Dentistas`, `Veterinária`, `harmonizacao`, `Pesquisa`, `Notion (Beleza)` |
| **Slug** | text | **CRITICAL**: URL slug for site-demo directory (e.g., `dra-laura-sanches`) |
| **US ID** | text | **CRITICAL**: Operational story/job identifier used by automation (e.g., `US-089`) |
| **Site Criado Em** | date | **CRITICAL**: Date when site was created (YYYY-MM-DD format) |
| **Canal Contato** | select | `WhatsApp`, `Instagram DM`, `Email`, `Telefone` — preferred outreach channel |
| **Tentativas Contato** | number | Number of outreach attempts made |
| **Motivo Perda** | select | `Sem resposta`, `Sem interesse`, `Preço`, `Já tem site`, `Concorrente` — reason for loss |
| **Google Maps ID** | text | Google Maps place ID for the business |
| **Data 1º Contato** | date | First outreach date |
| **Data Follow-up** | date | Follow-up date |
| **Horário** | date | Scheduled time |

### Sales pipeline — TWO LAYERS (reconciled 2026-04-15)

**Camada 1 — SQLite Funnel (automacao/scripts):**
```
Lead → Contatado → Respondeu → Reuniao → Proposta → Fechado
```
Usado por: `sync_notion_csv_to_sqlite.py`, `lead_discovery_maps.py`, `generate_crm_data.py`

**Camada 2 — Notion Granular (operacao detalhada):**
```
Lead → Qualificado → Site em Criacao → Mensagem Pronta → Enviado → Respondeu → Reuniao → Proposta → Fechado / Perdido / Descartado
```
Usado por: Notion CRM, `notion_outbox_enqueue.py`, `notion_outbox_worker.py`

**Mapeamento Notion → SQLite para automacao:**
| Notion | SQLite |
|--------|--------|
| Lead | Lead |
| Qualificado / Site em Criacao / Mensagem Pronta / Enviado | Contatado |
| Respondeu / Reuniao / Proposta | mapeia diretamente |
| Fechado / Perdido / Descartado | Fechado |

**Regra: SQLite e a fonte unica para automacao. Notion e granular para referencia humana.**

**Pipeline stages**:

- **Lead**: Prospect identified, initial data collected
- **Qualificado**: Prospect vetted and approved for site creation
- **Site em Criação**: User story generated, agent is building the site
- **Mensagem Pronta**: OK: Site created + outreach message generated + Notion updated (READY TO SEND)
- **Enviado**: Outreach message sent to prospect via WhatsApp/Instagram
- **Respondeu**: Prospect responded to outreach
- **Reunião**: Meeting scheduled or completed
- **Proposta**: Proposal sent to client
- **Fechado**: Deal closed (check `Venda` = `Sim` and `Valor` for amount)
- **Perdido**: Prospect declined or went silent
- **Descartado**: Prospect disqualified

### Accessing via MCP (ad-hoc queries only)

Use the Notion MCP tools for **ad-hoc queries and reads** only:
- **Search**: `notion-search` with query related to prospect names
- **Fetch database**: `notion-fetch` with ID `2f76f51e-b8a5-8088-a52c-db29fc3c1f81`
- **Create prospect**: `notion-create-pages` with parent `data_source_id: "2f76f51e-b8a5-800b-8c7e-000bf9f86798"`

Para atualizacoes de producao (pipeline automatizado), use o outbox (ver abaixo).

### CRITICAL: How to Update Notion After Creating a Site

**When you finish creating a client site, you MUST update the Notion database via the outbox pipeline.** This creates verifiable receipts that done_gate requires to pass.

**Step 1 -- Enqueue the update:**

```bash
python3 scripts/notion_outbox_enqueue.py --us-id US-090 --page-id 2f76f51e-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

This reads the execution artifact from `prd.json` and enqueues all required field updates into `.notion-outbox/queue/`. The canonical record remains the linked page in Notion.

**Step 2 -- Process the outbox queue:**

```bash
python3 scripts/notion_outbox_worker.py --once
```

This sends the update to Notion and writes a verified receipt to `.notion-outbox/receipts/` plus `.notion-outbox/index/us_id/US-XXX.json`. The done_gate checks this evidence.

**Fields updated by the outbox pipeline:**
- [done] `Status` -> `"Mensagem Pronta"` (exact value, do NOT use "Site Pronto")
- [done] `URL Demo` -> Full URL to the deployed site
- [done] `Mensagem` -> The personalized outreach message you generated
- [done] `Slug` -> URL slug used in site-demo directory
- [done] `US ID` -> Operational story/job identifier used by automation
- [done] `Site Criado Em` -> Date the site was created

**Finding the Notion page_id**:
1. Search Notion for the prospect name
2. Use the page ID returned from the search
3. Or check the execution artifact `notionPageId` field, which must point back to the canonical Notion page

**Reconciliation rule**:
- Execution artifacts that require Notion must contain `notionPageId`
- If a legacy story is missing it, run `python3 scripts/reconcile_prd_notion_links.py` first
- Review the report, then use `--apply` only for unique safe matches

## Python Scripts Workflow

The `scripts/` directory contains automation tools for the site creation pipeline. See `scripts/README.md` for complete documentation.

### `site_orchestrator.py`
Generates execution artifacts in `prd.json` from canonical Notion prospects.

`page_id` from Notion is mandatory in the prospect payload. New stories that require Notion must not be created without `notionPageId`.

```bash
# Preview what would be generated (dry run)
python3 scripts/site_orchestrator.py --dry-run

# Generate user stories from all qualified prospects
python3 scripts/site_orchestrator.py --from-json prospects.json

# Generate for specific prospect
python3 scripts/site_orchestrator.py --from-json prospects.json --name "Dra. Laura"
```

### `notion_client.py`
Python wrapper for Notion CRM operations. Used internally by the outbox worker to build API payloads. For production updates, use the outbox pipeline instead of calling this module directly (see "How to Update Notion After Creating a Site" above).

### `reconcile_prd_notion_links.py`
Safely reconciles legacy stories in `prd.json` with live Notion pages by slug. Default mode is report-only; `--apply` writes `notionPageId` only for unique safe matches.

### `sync_story_identity_to_notion.py`
Synchronizes `Slug` and `US ID` from stories that already have `notionPageId` to their linked Notion pages via the outbox.

### `slug_utils.py`
Utilities for generating and ensuring unique URL slugs:
- `generate_slug(nome)` — converts name to URL-safe slug
- `ensure_unique_slug(slug, existing)` — guarantees uniqueness
- `get_existing_slugs()` — lists all existing slugs in `site-demo/`

### `message_generator.py`
Reference module for programmatic message generation. In practice, the LLM agent generates messages using `template-mensagem-outreach.md` for better context adaptation.

## Key Files

- `index.html` / `styles.css` / `script.js` — Root agency site
- `site-demo/<client-name>/` — Individual client sites (145+)
- `harmonizacao.csv` — Legacy client/prospect data (superseded by Notion CRM)
- `contexto.md` — Original design brief and research decisions (Portuguese)
- `politica-de-privacidade.html` / `termos-de-uso.html` — Legal pages
- `.playwright-mcp/` — Visual QA baseline screenshots
- `template-mensagem-outreach.md` — Outreach message template with examples by niche
- `NOTION-FIELDS-REFERENCE.md` — **Quick reference for Notion database fields and update patterns**
- `scripts/README.md` — Complete workflow documentation
- `scripts/notion_outbox_enqueue.py` — Enqueue Notion updates (outbox pattern)
- `scripts/notion_outbox_worker.py` — Process outbox queue, create verified receipts
- `scripts/notion_sync/` — Outbox infrastructure (contracts, store, worker, reconcile)
- `.notion-outbox/` — Local outbox state (gitignored)

## When Creating a New Client Site

1. Create directory under `site-demo/<client-slug>/`
2. Use self-contained `index.html` (inline CSS + JS)
3. Research the business (Google, Instagram, Facebook, official website) to get real info: services, address, phone, testimonials, and contact channels
4. Adapt the standard section template to the business niche
5. Customize color palette based on the client's brand/niche
6. Ensure all breakpoints render correctly (480, 768, 1024, 1440)
7. **Generate personalized outreach message** following `template-mensagem-outreach.md`:
   - **MUST** identify if prospect is pessoa física (Dr./Dra.) or empresa
   - Use correct pronouns:
     - Pessoa física (individual): "dele/dela", "queria", "do consultório da/do Dr."
     - Empresa (business): "vocês", "queriam", "da clínica/pizzaria/barbearia"
   - Adapt tone to business type:
     - Professional for healthcare (Dentista, Veterinária, Harmonização)
     - Relaxed/friendly for food & beauty (Pizzaria, Barbearia, Beleza)
   - Structure: Greeting → Context → Demo URL → Objective → CTA → Closing
   - Include demo URL and personalized context about their business
   - Keep message under 800 characters for WhatsApp/Instagram
   - See `template-mensagem-outreach.md` for complete examples by niche
8. **Update Notion CRM via outbox** (NOT via MCP directly):
   - Preferred: `python3 scripts/notion_update_from_prd.py --us-id US-XXX --mensagem-file /tmp/mensagem.txt --site-criado-em YYYY-MM-DD --process`
   - Fallback manual flow: `python3 scripts/notion_outbox_enqueue.py --us-id US-XXX --page-id PAGE_ID`
   - Process manual queue: `python3 scripts/notion_outbox_worker.py --once`
   - This updates: `Status` -> "Mensagem Pronta", `URL Demo`, `Mensagem`, `Slug`, `US ID`, `Site Criado Em`
   - The done_gate requires the outbox receipt to pass
9. Commit as `feat: US-XXX - Client Name - Site Completo`
10. **Done Gate** before setting `passes=true`:
   - Run: `python3 scripts/done_gate.py --us-id US-XXX`
   - Only mark done if output is `DONE GATE: PASS`
   - Preferred marker: `python3 scripts/mark_story_done.py --us-id US-XXX`

## Workflow Checklist

Before marking a client site as complete, verify:

- [ ] Site created in `site-demo/<slug>/index.html`
- [ ] Site tested locally at all breakpoints (480/768/1024/1440px)
- [ ] Outreach message generated following `template-mensagem-outreach.md`
- [ ] Correct pronouns used (pessoa física vs empresa)
- [ ] Tone appropriate for business niche
- [ ] `notionPageId` present in the story before production Notion update
- [ ] Notion updated via outbox (`notion_outbox_enqueue.py` + `notion_outbox_worker.py`) with Status **"Mensagem Pronta"** + all required fields
- [ ] Commit created with correct format
- [ ] Pushed to repository
- [ ] Done gate passed (`python3 scripts/done_gate.py --us-id US-XXX`)
