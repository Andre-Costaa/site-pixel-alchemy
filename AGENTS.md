# AGENTS.md

This file provides guidance to any AI agent (Claude Code, Droid/Factory AI, Codex, Kimi CLI, or similar) when working with code in this repository. It is the agent-agnostic equivalent of CLAUDE.md.

## Project Overview

Pixel Alchemy is a digital agency that produces single-page promotional websites for Brazilian clinics (aesthetics, dental, veterinary, beauty). The repo contains **two layers**:

1. **Root site** (`index.html`, `styles.css`, `script.js`) — the agency's own promotional page at pixelalchemy.com.br
2. **Client sites** (`site-demo/<client-name>/`) — 150+ individual client websites, each deployed as a subdirectory of the main domain (e.g., `pixelalchemy.com.br/site-demo/dra-lara-costa/`)

Client data and prospect tracking lives in the **Notion CRM database**, which is the absolute source of truth (see below).

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

### File pattern

Use the **self-contained single-file pattern**: Single `index.html` with all CSS in `<style>` and all JS in `<script>` tags inline. No external files.

### Standard section structure

Each client site follows the same section template, adapted to the business type:

1. **Navigation** — Auto-hides on scroll down, mobile hamburger menu
2. **Hero** — Value prop, CTAs, animated blobs/visual elements
3. **Services/Treatments** — Card grid (responsive: 1-2-3 columns)
4. **Process/How It Works** — Timeline or steps
5. **About/Differentials** — Stats counter, trust signals
6. **Testimonials** — Client reviews with star ratings
7. **FAQ** — Accordion
8. **Contact** — Form (name, email/phone, service selector, message) + business info
9. **Footer** — Links, legal info

Sections may be renamed or reordered per business niche (e.g., veterinary clinics emphasize "Emergencia 24h", dental clinics emphasize "Tratamentos").

## Design System

### Color system

All colors are CSS custom properties in `:root`. Each accent color has a `-light` variant.

- Base: `--color-charcoal`, `--color-cream`
- Accents: `--color-terracotta` (primary CTA), `--color-sage`, `--color-lavender`, `--color-clay`
- Gradients: `--gradient-warm` (terracotta-clay), `--gradient-cool` (sage-lavender)

Client sites customize these values per brand but follow the same variable naming pattern.

### Blobmorphism system

Blob shapes are the core design language:

- `--border-radius-blob: 60% 40% 30% 70% / 60% 30% 70% 40%` creates organic shapes
- Hero blobs (`.blob-1` through `.blob-4`) use CSS `blur` + `backdrop-filter` + 20s transform animations
- Layered z-index for depth perception

### Animation system

Three approaches, all respecting `prefers-reduced-motion`:

1. **CSS keyframes**: Continuous effects (blob floating 6-20s, card floating, ripple)
2. **Intersection Observer**: Scroll-triggered `.wow-fade-up` / `.wow-fade-in` with `data-delay` for stagger (100ms increments), threshold 0.1, rootMargin -50px
3. **JavaScript-driven**: Counter animation (stats), tilt effect (service cards), parallax (blobs)

Use only `transform` and `opacity` for GPU acceleration.

### Responsive breakpoints

Mobile-first: base (<480px) - 480px - 768px - 1024px.

## Coding Conventions

- **HTML**: Semantic sections with `<section class="section-name" id="section-name">`
- **CSS**: 4-space indent, leverage existing `--color-*` / `--spacing-*` tokens, lowercase-kebab class names, sectioned comment blocks
- **JS**: Vanilla ES6, `const`/`let`, camelCase identifiers, modular sections under documented comment headers, `querySelector` APIs
- **No emojis** in any code or content — create SVG/image if an icon is needed

## Commit Convention

```
feat: US-XXX - Client Name - Site Completo
```

Each client site is a single commit as a user story (US-XXX, sequential numbering). Portuguese descriptions are standard.

## Notion CRM — Controle de Prospeccao

**Database ID**: `2f76f51e-b8a5-8088-a52c-db29fc3c1f81`

### Source of truth policy

- **Notion is the absolute source of truth** for prospect data, pipeline status, technical identifiers, and delivery state.
- `prd.json` is an execution artifact only. It exists to support mass site creation and can be replaced in the future.
- If `prd.json` conflicts with Notion, **Notion wins**.
- Documentation and operational decisions must treat Notion as canonical.

### Database schema

| Property | Type | Values / Notes |
|---|---|---|
| **Nome** | title | Client/business name (primary key) |
| **Nicho** | select | `Dentista`, `Veterinaria`, `Harmonizacao`, `Beleza`, `Pizzaria`, `Barbearia`, `Padaria`, `Acougue`, `Pet Shop` |
| **Status** | select | `Lead` - `Qualificado` - `Site em Criacao` - `Mensagem Pronta` - `Enviado` - `Respondeu` - `Reuniao` - `Proposta` - `Fechado` / `Perdido` / `Descartado` |
| **Telefone** | text | Phone number with area code |
| **Endereco** | text | Business full address |
| **Email Negocio** | text | Public business email when found with evidence |
| **Email Responsavel** | text | Owner/partner/responsible email when found with evidence |
| **Status Email** | select | `Validado` - `Encontrado` - `Duvidoso` - `Nao encontrado` |
| **Fonte Email** | select | `Site` - `Instagram` - `Google` - `Facebook` - `Manual` |
| **Email Validado Em** | date | Date of the last reliable email validation |
| **URL Demo** | url | **CRITICAL**: `https://www.pixelalchemy.com.br/site-demo/<slug>/` |
| **Mensagem** | text | **CRITICAL**: Personalized outreach message |
| **Slug** | text | **CRITICAL**: URL slug for site-demo directory |
| **US ID** | text | **CRITICAL**: Operational story/job identifier used by automation (e.g., `US-089`) |
| **Site Criado Em** | date | **CRITICAL**: Date when site was created (YYYY-MM-DD) |
| **Descricao** | text | Business description |
| **Instagram** | text | Instagram handle or URL |

### PRD-Notion linkage rule

`notionPageId` in `prd.json` is only an operational pointer back to the canonical record in Notion.

- New execution artifacts must be created with `notionPageId` already populated.
- If a legacy story is missing `notionPageId`, do not continue the delivery flow until you reconcile it against Notion.
- Use `python3 scripts/reconcile_prd_notion_links.py` first in dry-run mode.
- Use `--apply` only after reviewing the report and confirming that the match is unique and safe.

### Sales pipeline

```
Lead - Qualificado - Site em Criacao - Mensagem Pronta - Enviado - Respondeu - Reuniao - Proposta - Fechado / Perdido / Descartado
```

- **Mensagem Pronta**: Site + outreach message + Notion update = READY TO SEND

## Pipeline Execution — Step by Step

This is the EXACT sequence for executing a user story (US-XXX). Follow every step. The done_gate will reject incomplete work.

### Step 1: Read the canonical record from Notion, then load `prd.json` only if needed

Always validate the prospect in Notion first. `prd.json` is only a working queue for mass execution.

Extract from Notion: client name, slug, phone, address, nicho, and page identity.

If the current run is being orchestrated through `prd.json`, then load the matching story:

```bash
python3 -c "import json; prd=json.load(open('prd.json')); story=[s for s in prd['userStories'] if s['id']=='US-XXX'][0]; print(json.dumps(story, indent=2, ensure_ascii=False))"
```

If `notionPageId` is missing, STOP and reconcile first:

```bash
python3 scripts/reconcile_prd_notion_links.py --us-id US-XXX
python3 scripts/reconcile_prd_notion_links.py --us-id US-XXX --apply
```

### Step 2: Research the business

Search Google, Instagram, Facebook, and the official website for real information: services, testimonials, team, brand colors, opening hours, and contact channels.

For email capture:

- Try `Email Responsavel` first only when there is explicit evidence.
- If no direct responsible email is found, look for `Email Negocio`.
- Save the result in Notion with `Status Email`, `Fonte Email`, and `Email Validado Em` when applicable.
- If no reliable email is found, set `Status Email` to `Nao encontrado` or `Duvidoso` and continue the flow normally.

### Step 3: Create the site

```bash
mkdir -p site-demo/<slug>
```

Create `site-demo/<slug>/index.html` — self-contained, inline CSS + JS. All 9 standard sections. Real business info. Responsive at all breakpoints.

### Step 4: Generate outreach message

Read `template-mensagem-outreach.md` for template and examples.

**CRITICAL RULES**:
- **Pessoa fisica** (Dr./Dra. + name): use "dele/dela", "do consultorio da Dra./do Dr.", "queria"
- **Empresa** (business name): use "voces", "da clinica/barbearia/pizzaria", "queriam"
- **Nicho-specific tone**:
  - Healthcare (Dentista, Veterinaria, Harmonizacao): "autoridade e sofisticacao", "pacientes"
  - Beauty (Beleza, Barbearia): "estilo e profissionalismo", "clientes"
  - Food (Pizzaria, Padaria, Acougue): "apetite e qualidade", "clientes"
  - Pet Shop: "confianca e profissionalismo", "tutores"
- Max 800 characters
- Include demo URL: `https://www.pixelalchemy.com.br/site-demo/<slug>/`

Save message to a temp file:

```bash
cat > /tmp/mensagem-US-XXX.txt << 'EOF'
[generated message here]
EOF
```

### Step 5: Update Notion via outbox

**ALL fields are required. The outbox will BLOCK if any is missing.**

Email fields are optional in the outbox update, but the result of email research should still be recorded in Notion whenever the schema is available.

```bash
cd scripts && python3 notion_outbox_enqueue.py \
  --us-id US-XXX \
  --page-id NOTION_PAGE_UUID \
  --status "Mensagem Pronta" \
  --url-demo "https://www.pixelalchemy.com.br/site-demo/<slug>/" \
  --slug "<slug>" \
  --mensagem-file /tmp/mensagem-US-XXX.txt \
  --site-criado-em $(date +%Y-%m-%d)
```

Then process the queue:

```bash
python3 notion_outbox_worker.py --once
```

### Step 6: Commit and push

```bash
git add site-demo/<slug>/
git commit -m "feat: US-XXX - Client Name - Site Completo"
git push origin main
```

### Step 7: Run done gate

```bash
cd scripts && python3 done_gate.py --us-id US-XXX
```

**Only mark the story as done if output is `DONE GATE: PASS`.**

If FAIL: read the check details, fix the issue, re-run.

```bash
python3 mark_story_done.py --us-id US-XXX
```

## Guardrails (enforced by scripts)

These are NOT suggestions. The pipeline scripts enforce them:

| Guardrail | Script | What happens if violated |
|---|---|---|
| Duplicate prospect | `site_orchestrator.py` + `notion_dedup_guard.py` | SKIP — story not created |
| Duplicate slug | `site_orchestrator.py` + `notion_dedup_guard.py` | SKIP — story not created |
| Missing `notionPageId` at story creation | `site_orchestrator.py` | SKIP — execution artifact not created |
| Incomplete outbox | `notion_outbox_enqueue.py` | BLOCKED — missing Status, Mensagem, Slug, URL Demo, or US ID |
| Missing fields in Notion | `done_gate.py` | FAIL — checks receipt has all 5 critical fields |
| Missing site sections | `done_gate.py` | FAIL — checks HTML for hero, services, testimonials, contact, footer, form |
| No git commit | `done_gate.py` | FAIL — requires commit containing site-demo/<slug>/index.html |

## Anti-patterns — DO NOT

- **DO NOT** update Notion directly via API or MCP. Always use the outbox pipeline (enqueue + worker).
- **DO NOT** use status "Site Pronto". The correct status is "Mensagem Pronta".
- **DO NOT** create or continue a story that requires Notion if `notionPageId` is missing.
- **DO NOT** treat `prd.json` as the source of truth when Notion says otherwise.
- **DO NOT** invent owner/business emails or infer them from domain patterns without evidence.
- **DO NOT** prefer manual `notion_outbox_enqueue.py` for new stories when `notion_update_from_prd.py` can be used.
- **DO NOT** skip the outreach message. The done_gate checks for it.
- **DO NOT** use `git add .` or `git add -A`. Add specific files only.
- **DO NOT** mark `passes=true` without running done_gate first.
- **DO NOT** create separated CSS/JS files. Use self-contained single-file pattern.
- **DO NOT** use emojis in code or content.

## Dedup Check (manual)

Before creating any new prospect or site:

```bash
cd scripts && python3 notion_dedup_guard.py --check-name "Dra. Laura Sanches"
cd scripts && python3 notion_dedup_guard.py --check-slug "dra-laura-sanches"
```

Exit code 0 = available. Exit code 1 = duplicate found.

To reconcile legacy stories already in `prd.json` but missing `notionPageId`:

```bash
python3 scripts/reconcile_prd_notion_links.py
python3 scripts/reconcile_prd_notion_links.py --apply
```

To fix stories that already have `notionPageId` but whose linked Notion page is missing `Slug` or `US ID`:

```bash
python3 scripts/sync_story_identity_to_notion.py
python3 scripts/sync_story_identity_to_notion.py --apply
```

## Key Files

- `prd.json` — User stories (source of truth for what to build)
- `template-mensagem-outreach.md` — Outreach message template with examples by niche
- `site-demo/<client-name>/` — Individual client sites (150+)
- `scripts/site_orchestrator.py` — Generates user stories from Notion prospects
- `scripts/reconcile_prd_notion_links.py` — Reconciles legacy `prd.json` stories with live Notion pages by slug
- `scripts/sync_story_identity_to_notion.py` — Syncs `Slug` and `US ID` from the story to the linked Notion page through the outbox
- `scripts/notion_outbox_enqueue.py` — Enqueue Notion updates (ALL fields required)
- `scripts/notion_outbox_worker.py` — Process outbox queue, create verified receipts
- `scripts/done_gate.py` — Validates all completion criteria before marking done
- `scripts/mark_story_done.py` — Marks story as done (only after done_gate PASS)
- `scripts/notion_dedup_guard.py` — Checks for duplicate prospects/slugs
- `CLAUDE.md` — Claude Code specific instructions (superset of this file)
- `NOTION-FIELDS-REFERENCE.md` — Quick reference for Notion database fields

## Workflow Checklist

Before marking a client site as complete, verify:

- [ ] Site created in `site-demo/<slug>/index.html` (self-contained)
- [ ] All 9 sections present (nav, hero, services, process, differentials, testimonials, FAQ, contact, footer)
- [ ] Responsive at all breakpoints (480/768/1024/1440px)
- [ ] Real business info used (phone, address, services from research)
- [ ] Outreach message generated following `template-mensagem-outreach.md`
- [ ] Correct pronouns (pessoa fisica vs empresa)
- [ ] Tone appropriate for business niche
- [ ] `notionPageId` present in the story before updating Notion
- [ ] Notion updated via outbox with ALL required fields (Status, URL Demo, Mensagem, Slug, US ID, Site Criado Em)
- [ ] Commit format: `feat: US-XXX - Client Name - Site Completo`
- [ ] Pushed to repository
- [ ] Done gate PASS: `python3 scripts/done_gate.py --us-id US-XXX`
