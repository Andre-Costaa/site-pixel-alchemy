# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pixel Alchemy is a digital agency that produces single-page promotional websites for Brazilian clinics (aesthetics, dental, veterinary, beauty). The repo contains **two layers**:

1. **Root site** (`index.html`, `styles.css`, `script.js`) — the agency's own promotional page at pixelalchemy.com.br
2. **Client sites** (`site-demo/<client-name>/`) — 145+ individual client websites, each deployed as a subdirectory of the main domain (e.g., `pixelalchemy.com.br/site-demo/dra-lara-costa/`)

Client data and prospect tracking lives in `harmonizacao.csv` (legacy) and primarily in the **Notion CRM database** (see below).

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

## Notion CRM — Controle de Prospecção

The primary prospect/client management system is a Notion database accessible via MCP (Model Context Protocol).

**Page**: "Pixel Alchemy - Controle Prospecção" (`2f76f51e-b8a5-8038-8557-c157105f790d`)
**Database**: "Controle" (`2f76f51e-b8a5-8088-a52c-db29fc3c1f81`)
**Data Source**: `collection://2f76f51e-b8a5-800b-8c7e-000bf9f86798`

### Database schema

| Property | Type | Values / Notes |
|---|---|---|
| **Nome** | title | Client/business name (primary key) |
| **ID** | text | Internal identifier |
| **Nicho** | select | `Dentista`, `Veterinária`, `Harmonização`, `Beleza`, `Pizzaria`, `Barbearia`, `Padaria`, `Açougue`, `Pet Shop` |
| **Status** | select | `Novo` → `Enviado` → `Respondeu` → `Fechado` / `Perdido` |
| **Aprovado** | select | `Aprovado`, `Reprovado`, `Pendente` |
| **Venda** | select | `Sim`, `Não`, `Em negociação` |
| **Valor** | number (R$) | Deal value in BRL |
| **Telefone** | text | Phone number |
| **Endereço** | text | Business address |
| **Site** | text | Existing website |
| **URL Demo** | url | Link to the demo site under `site-demo/` |
| **Instagram** | text | Instagram handle/URL |
| **Facebook** | text | Facebook page |
| **Descrição** | text | Business description |
| **Mensagem** | text | Outreach message sent |
| **Resposta** | text | Client's response |
| **Observações** | text | Internal notes |
| **Origem** | select | `Dentistas`, `Veterinária`, `harmonizacao`, `Pesquisa`, `Notion (Beleza)` |
| **Data 1º Contato** | date | First outreach date |
| **Data Follow-up** | date | Follow-up date |
| **Horário** | date | Scheduled time |

### Sales pipeline flow

```
Novo → Enviado → Respondeu → Fechado (won) / Perdido (lost)
```

- **Novo**: Prospect identified, not yet contacted
- **Enviado**: Demo site created and outreach message sent
- **Respondeu**: Client responded to outreach
- **Fechado**: Deal closed (check `Venda` = `Sim` and `Valor` for amount)
- **Perdido**: Prospect declined or went silent

### Accessing via MCP

Use the Notion MCP tools to interact with this database:
- **Search**: `notion-search` with query related to prospect names
- **Fetch database**: `notion-fetch` with ID `2f76f51e-b8a5-8088-a52c-db29fc3c1f81`
- **Create prospect**: `notion-create-pages` with parent `data_source_id: "2f76f51e-b8a5-800b-8c7e-000bf9f86798"`
- **Update prospect**: `notion-update-page` with the page ID of the specific prospect

When creating a new client site, also create or update the corresponding row in this Notion database with the `URL Demo` pointing to the deployed site.

## Key Files

- `index.html` / `styles.css` / `script.js` — Root agency site
- `site-demo/<client-name>/` — Individual client sites (145+)
- `harmonizacao.csv` — Legacy client/prospect data (superseded by Notion CRM)
- `contexto.md` — Original design brief and research decisions (Portuguese)
- `politica-de-privacidade.html` / `termos-de-uso.html` — Legal pages
- `.playwright-mcp/` — Visual QA baseline screenshots

## When Creating a New Client Site

1. Create directory under `site-demo/<client-slug>/`
2. Use self-contained `index.html` (inline CSS + JS)
3. Research the business (Google, Instagram, Facebook) to get real info: services, address, phone, testimonials
4. Adapt the standard section template to the business niche
5. Customize color palette based on the client's brand/niche
6. Ensure all breakpoints render correctly (480, 768, 1024, 1440)
7. **Generate personalized outreach message** following `template-mensagem-outreach.md`:
   - Adapt tone to business type (professional for healthcare, relaxed for food/beauty)
   - Use correct pronouns (pessoa física vs empresa)
   - Include demo URL and personalized context
   - Keep message under 800 characters for WhatsApp/Instagram
8. **Update Notion CRM** with:
   - `Status` → "Mensagem Pronta"
   - `URL Demo` → full URL to deployed site
   - `Mensagem` → the generated outreach message
   - `Slug` → URL slug
   - `US ID` → user story ID (e.g., "US-089")
   - `Site Criado Em` → today's date (YYYY-MM-DD)
9. Commit as `feat: US-XXX - Client Name - Site Completo`
