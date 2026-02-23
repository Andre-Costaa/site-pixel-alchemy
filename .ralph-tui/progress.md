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

## 2026-02-23 - US-003
- What was implemented: Fixed hero image for Dra. Laura Sanches site - replaced male dentist image with female dentist image to match the client's gender
- Files changed: `site-demo/dra-laura-sanches/index.html` (line 1538)
- **Learnings:**
  - When using stock images for professional sites, always verify that the image matches the client's gender and professional identity
  - Unsplash photo IDs: `photo-1559839734-2b71ea197ec2` shows a male doctor, `photo-1594824476967-48c8b964273f` shows a female healthcare professional
  - Playwright visual testing is essential to catch content mismatches that automated tests might miss
  - Always test at multiple breakpoints (375px, 768px, 1024px, 1440px) to ensure responsive images work correctly
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