# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

- **Self-contained single-file pattern**: All new client sites use a single `index.html` with inline `<style>` and `<script>` tags. No external CSS/JS files.
- **Progressive enhancement animations**: Elements are always visible by default (`opacity: 1; transform: none`). JS adds `js-enabled` class to body, then IntersectionObserver adds `animated` class for entrance effects. Never hide content behind JS.
- **Font pairing convention**: Each site uses a unique serif + sans-serif Google Fonts pairing to differentiate from other sites. Avoid reusing exact same font combos across sites.
- **Color system**: Each site defines its own `--primary`, `--accent`, and variant CSS custom properties in `:root`. Use a distinct palette per client to avoid generic look.
- **SVG icons over HTML entities**: Prefer inline SVGs for icons (especially in service cards, contact items, footer) for consistent rendering cross-browser. HTML entities (`&#128205;` etc.) can render as emoji and break design consistency.
- **WhatsApp button**: Fixed bottom-right, links to `https://wa.me/55{phone_without_formatting}`. Include proper WhatsApp SVG icon.
- **Phone mask**: JS input mask for Brazilian phone format `(XX) XXXXX-XXXX` on contact form phone field.

---

## 2026-02-23 - US-001
- What was implemented: Complete professional site for Mairake Odontologia (dental clinic in Ribeirao Preto)
- Files changed: `site-demo/mairake-odontologia/index.html` (new)
- Design: Warm burgundy/plum (`#2d1b33`) + gold (`#c9a96e`) palette. Fonts: Cormorant Garamond (display) + Outfit (body). Split-screen hero with image, stats bar at bottom, problem/solution cards, 6 service cards, testimonials on dark bg, differentials with counters, contact form with 2-column layout.
- **Learnings:**
  - Bocardo site (reference) uses `Playfair Display + Inter` and teal/navy palette. Mairake differentiates with plum/gold and Cormorant Garamond + Outfit.
  - The `hero-stats-bar` pattern (bottom of hero with key metrics) is a strong visual anchor for dental sites.
  - Using inline SVGs for all icons avoids emoji rendering inconsistencies across platforms.
  - The `form-row` CSS grid pattern for side-by-side form fields improves desktop contact form UX.
  - Outreach message for Mairake already exists in `template-mensagem-outreach.md` as the example for "Clinica (empresa)" pattern.
---

## 2026-02-23 - US-005
- What was implemented: Fixed animation visibility issue for Dra. Ana Carolina Orlanda Junqueira Defina dental site
- Files changed: `site-demo/dra-ana-carolina-orlanda/index.html` (modified)
- Issue: Sections "A Experiência que Você Merece" (problem-solution), "Tratamentos que Transformam" (services), "Depoimentos", "Diferenciais" and "Contato" were invisible due to Intersection Observer not observing elements
- Fix: Added code to observe all `.animate-on-scroll` elements with the Intersection Observer
- **Learnings:**
  - When using Intersection Observer for scroll animations, you must call `observer.observe(el)` for each element you want to track
  - The CSS was correctly setting `opacity: 1` by default, but without the observer actively watching elements, the animation classes weren't being applied properly on scroll
  - Playwright visual testing confirmed all sections are now visible on both desktop and mobile breakpoints
---

## 2026-02-23 - US-100
- What was implemented: Playwright review and fix for Barbearia Soul Fine site (slug: barbearia-soul-fine)
- Files changed: `site-demo/barbearia-soul-fine/index.html` (modified - added Problem/Solution section)
- Issue: Done gate was failing on `site.section.problem_solution` check - the site had "Como Funciona" (process) and "Sobre" (about) sections but no dedicated Problem/Solution section
- Fix: Added dedicated Problem/Solution section with id="experiencia" between Hero and Services. Contains two cards: "O Problema" (5 pain points) and "Nossa Solucao" (5 solutions). Added responsive CSS styling matching the site's dark industrial barbershop theme.
- **Learnings:**
  - The done_gate.py check for `site.section.problem_solution` looks for both "problema/problem/desafio" AND "solucao/solution/solu" keywords in the normalized HTML content
  - A generic "Sobre" (About) or "Como Funciona" (Process) section does NOT satisfy this requirement - it must explicitly frame problems vs solutions
  - When adding sections to existing sites, match the existing CSS variable naming and color scheme (the site used `--amber-mid`, `--bg-card`, `--bg-surface` etc.)
  - The section should be placed early in the page flow (after Hero, before Services) to establish value proposition
  - Using `&#10005;` (X) and `&#10003;` (checkmark) as list markers creates clear visual distinction between problems and solutions
---

