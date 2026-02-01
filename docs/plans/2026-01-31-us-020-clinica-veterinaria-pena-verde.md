# US-020 - Clínica Veterinária Pena Verde - Site Completo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Create a single-page HTML website for Clínica Veterinária Pena Verde - Animais Silvestres e Exóticos in Ribeirão Preto, featuring a unique design focused on wild and exotic animals.

**Architecture:** Single HTML file with embedded CSS and JavaScript. Design will use an exotic/tropical color palette (forest green, tropical accents) with organic shapes and animations that reflect the wild/exotic animal specialty.

**Tech Stack:** HTML5, CSS3, Vanilla JavaScript, Google Fonts (Montserrat & Open Sans), Unsplash stock images for exotic animals

---

## Task 1: Create Project Directory Structure

**Files:**
- Create: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/`

**Step 1: Create the directory**

```bash
mkdir -p site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos
```

**Step 2: Verify directory creation**

Run: `ls -la site-demo/ | grep pena-verde`
Expected: Directory `clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos` is listed

---

## Task 2: Create HTML Document Structure

**Files:**
- Create: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Write HTML skeleton with meta tags**

Write the complete HTML structure including:
- Doctype, lang="pt-BR"
- Meta charset, viewport, description, keywords
- Title: "Clínica Veterinária Pena Verde | Animais Silvestres e Exóticos | Ribeirão Preto"
- Google Fonts links (Montserrat & Open Sans)
- Embedded `<style>` tag in `<head>`
- Embedded `<script>` tag before `</body>`

**Step 2: Define CSS variables for exotic/wild theme**

Create `:root` CSS variables with:
- Primary: Forest green `#2d6a4f`, Light green `#40916c`
- Secondary: Tropical teal `#1b4332`, accent lime `#52b788`
- Accent colors: Earth tone `#bc6c25`, warm sand `#dda15e`
- Background: Cream `#fefae0`, light sand `#faedcd`
- Text: Charcoal `#1f2937`, gray `#6b7280`
- White `#ffffff`
- Gradients: Forest gradient, tropical gradient
- Border radius variables: sm, md, lg, pill, blob
- Spacing variables: xs through 3xl
- Transition variables: fast, base, slow
- Font variables: display (Montserrat), body (Open Sans)

**Step 3: Add global CSS reset and base styles**

Include:
- Reset for margin, padding, box-sizing
- Smooth scroll behavior
- Body base styles (font, color, background, line-height)
- Image, link, ul, button base styles
- Container class (max-width 1200px, centered)
- Section base class (padding, positioning)

---

## Task 3: Implement Navigation Component

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add navigation HTML**

Create `<nav class="nav">` with:
- Container with logo (SVG leaf/nature icon + "Pena Verde" text)
- Navigation links: Início, Serviços, Depoimentos, Diferenciais, Contato
- Mobile hamburger toggle button

**Step 2: Add navigation CSS styles**

Include:
- Fixed positioning, z-index 1000
- Glassmorphism background (rgba with backdrop-filter)
- Shadow, transition
- Hidden class for scroll behavior
- Logo styling with forest green
- Nav links with underline hover effect
- Mobile menu styles (hidden by default, active state)
- Hamburger animation

**Step 3: Add navigation JavaScript**

Implement:
- Scroll detection to hide/show nav
- Mobile menu toggle functionality
- Close menu on link click
- Smooth scroll for anchor links with nav offset

---

## Task 4: Implement Hero Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Hero HTML structure**

Create `<section class="hero" id="home">` with:
- Background leaf/nature pattern decorations
- Two-column grid (content + image)
- Hero content with badges, title, description, CTAs
- Hero image with floating cards
- Use exotic animal image from Unsplash (parrot, toucan, or similar)

**Step 2: Add Hero CSS styles**

Include:
- Min-height 100vh, gradient background (forest theme)
- Animated leaf/pattern decorations with keyframes
- Hero badges with forest green styling
- Large title with gradient text highlight
- CTA buttons (primary with forest gradient, secondary outlined)
- Hero image with rounded corners and shadow
- Floating cards with animation (similar to reference)
- Fade-up and fade-in keyframe animations

**Step 3: Add Hero content details**

Content:
- Badges: "Especialistas em Animais Silvestres", "Cuidado Exótico"
- Title: "Cuidado Veterinário <span>Especializado</span> para Animais Silvestres e Exóticos"
- Description: "Na Clínica Veterinária Pena Verde, somos especialistas no atendimento de animais silvestres e exóticos. Nossa equipe tem expertise para cuidar de pássaros, répteis, roedores e muito mais."
- CTAs: "Agendar Consulta" (primary), "Nossos Serviços" (secondary)
- Image: Use Unsplash photo of exotic animal (parrot/toucan/macaw)
- Floating cards: "+500 Animais Atendidos", "+8 Anos de Experiência"

**Step 4: Add Hero JavaScript**

Implement:
- Parallax effect on leaf decorations
- Counter animation for floating cards

---

## Task 5: Implement Problem/Solution Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Problem/Solution HTML**

Create `<section class="problem-solution" id="problem-solution">` with:
- Section header with tag, title, subtitle
- Two-column grid with comparison cards
- Problem card with red X icons
- Solution card with green check icons

**Step 2: Add Problem/Solution CSS**

Include:
- White background
- Comparison cards with border-radius
- Problem card: dashed border, neutral background
- Solution card: tropical/forest gradient background, white text
- Icon styling (red for X, green/lime for check)
- Wow animation classes

**Step 3: Add Problem/Solution content**

Problem points:
- Veterinários sem experiência com animais exóticos
- Clínicas que não atendem certas espécies
- Falta de equipamentos adequados para animais pequenos
- Ambiente estressante para animais silvestres

Solution points:
- Equipe especializada em animais silvestres e exóticos
- Atendimento completo para todas as espécies
- Equipamentos específicos para cada tipo de animal
- Ambiente projetado para reduzir estresse de animais selvagens

---

## Task 6: Implement Services Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Services HTML**

Create `<section class="services" id="services">` with:
- Section header
- 3-column grid of service cards
- Each card: icon, title, description

**Step 2: Add Services CSS**

Include:
- Gradient background
- Card styling with hover effects (lift, shadow, top border reveal)
- Service icon with gradient background
- Scale-up animation

**Step 3: Add Services content**

6 Services:
1. Consultas para Animais Silvestres - Atendimento especializado para pássaros, répteis, roedores e outros exóticos
2. Cirurgias de Animais Exóticos - Procedimentos cirúrgicos adaptados para cada espécie
3. Exames Especializados - Diagnóstico por imagem e laboratorial específico
4. Nutrição e Manejo - Orientações alimentares e de manejo adequadas
5. Emergências 24h - Atendimento de urgência para animais exóticos
6. Aconselhamento para Tutores - Educação sobre cuidados específicos

---

## Task 7: Implement Testimonials Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Testimonials HTML**

Create `<section class="testimonials" id="testimonials">` with:
- Section header with white text
- 3-column grid of testimonial cards
- Each card: star rating, quote, author info

**Step 2: Add Testimonials CSS**

Include:
- Dark/forest background with white text
- Glassmorphism cards (rgba with backdrop-filter)
- Star icons in gold/amber
- Avatar with gradient background and initials
- Fade-up animation

**Step 3: Add Testimonials content**

3 Testimonials:
1. Mariana Costa - "A Pena Verde salvou minha calopsita. Os veterinários entendem profundamente o comportamento de aves e trataram minha pequena com tanto carinho."
2. João Pedro Silva - "Tenho um iguana e sempre foi difícil encontrar veterinário preparado. A equipe da Pena Verde é incrível, conhece tudo sobre répteis!"
3. Carla Mendes - "Meus coelhos são tratados como reis aqui. finalmente encontrei uma clínica que sabe cuidar de animais exóticos com a dedicação que merecem."

---

## Task 8: Implement Differentials Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Differentials HTML**

Create `<section class="differentials" id="differentials">` with:
- Section header
- 3-column grid of differential items
- Each item: icon, title, text

**Step 2: Add Differentials CSS**

Include:
- White background
- Large icon containers with tropical gradient
- Fade-up animation

**Step 3: Add Differentials content**

6 Differentials:
1. Especialistas em Silvestres - Veterinários com formação específica em animais silvestres
2. Instalações Adequadas - Ambiente projetado para diferentes espécies exóticas
3. Equipamentos Específicos - Instrumentos apropriados para animais de diferentes portes
4. Atendimento Humanizado - Cada animal recebe atenção individualizada
5. Rede de Especialistas - Parcerias com referências nacionais em medicina de exóticos
6. Educação Continuada - Equipe sempre atualizada com as melhores práticas

---

## Task 9: Implement Contact Section

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Contact HTML**

Create `<section class="contact" id="contact">` with:
- Two-column grid (info + form)
- Contact info items: address, phone, hours
- Contact form with fields: name, phone, animal type, service, message
- Form success message

**Step 2: Add Contact CSS**

Include:
- Gradient background
- Contact info cards with icon + content
- Form wrapper with white background
- Form inputs with focus states
- Submit button with forest gradient
- Success message styling

**Step 3: Add Contact content**

Info:
- Title: "Entre em Contato"
- Address: R. Daniel Kujawski, 919 - Jardim Macedo, Ribeirão Preto - SP, 14091-010
- Phone: (16) 99992-1419
- Hours: Segunda a Sexta: 8h às 18h, Sábados: 8h às 12h

Form fields:
- Nome Completo (required)
- Telefone (required, with mask)
- Tipo de Animal (required): Ave, Réptil, Roedor, Outro
- Serviço Desejado (required): Consulta, Cirurgia, Exames, Emergência
- Mensagem (textarea, optional)

---

## Task 10: Implement Footer Component

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add Footer HTML**

Create `<footer class="footer">` with:
- 4-column grid
- Brand column with logo and description
- Quick links column
- Services column
- Contact column
- Bottom bar with copyright and social links

**Step 2: Add Footer CSS**

Include:
- Dark forest background
- White text
- Link hover effects (lime green)
- Social icon buttons with hover effects

**Step 3: Add Footer content**

- Brand: "Clínica Veterinária Pena Verde", description
- Links: Início, Serviços, Depoimentos, Diferenciais
- Services: Consultas, Cirurgias, Exames, Emergências
- Contact: Phone, Address
- Social: Facebook, Instagram, WhatsApp
- Copyright: 2026

---

## Task 11: Add Animation and Interaction JavaScript

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Add WoW scroll animations**

Implement Intersection Observer for:
- .wow-fade-up elements
- .wow-fade-in elements
- .wow-scale-up elements
- Support for data-delay attribute

**Step 2: Add form handling**

Implement:
- Form submit prevention
- Simulated submission with loading state
- Success message display
- Form reset
- Phone input mask

**Step 3: Add nav active state on scroll**

Implement:
- Scroll position tracking
- Active class on nav links based on visible section

**Step 4: Add responsive styles**

Ensure:
- Mobile breakpoint (<768px): Single column grids
- Tablet breakpoint (<1024px): 2-column grids
- Desktop (1024px+): Full layouts
- Reduced motion media query support

---

## Task 12: Final Quality Check

**Files:**
- Modify: `site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`

**Step 1: Verify all sections exist**

Check: Navigation, Hero, Problem/Solution, Services, Testimonials, Differentials, Contact, Footer

**Step 2: Verify responsive design**

Test: All grids collapse to single column on mobile

**Step 3: Verify no emojis or placeholders**

Check: All icons are SVG, all images are Unsplash URLs

**Step 4: Verify animations work**

Check: Scroll animations, hover effects, form submission

**Step 5: Verify contact info is correct**

Check: Address (R. Daniel Kujawski, 919), Phone (16) 99992-1419

---

## Task 13: Git Commit

**Files:**
- Git operation

**Step 1: Stage the new file**

```bash
git add site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html
```

**Step 2: Create commit**

```bash
git commit -m "feat: US-020 - Clínica Veterinária Pena Verde - Animais Silvestres e Exóticos - Site Completo"
```

**Step 3: Push to remote**

```bash
git push
```

---

## Task 14: Update Checkpoint Document

**Files:**
- Create: `docs/checkpoint.md` (if not exists) or Modify existing

**Step 1: Update checkpoint.md**

Add/Update entry:
```markdown
### US-020 - Clínica Veterinária Pena Verde - Animais Silvestres e Exóticos
- **Status**: ✅ Complete
- **URL**: pixelalchemy.com.br/site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos
- **Date**: 2026-01-31
- **Description**: Single-page website for veterinary clinic specializing in wild and exotic animals in Ribeirão Preto
```

**Step 2: Commit checkpoint update**

```bash
git add docs/checkpoint.md
git commit -m "docs: Update checkpoint with US-020 completion status"
git push
```

---

## Task 15: Final Verification

**Step 1: Verify file exists**

Run: `ls -lh site-demo/clinica-veterinaria-pena-verde-animais-silvestres-e-exoticos/index.html`
Expected: File exists with reasonable size (>50KB)

**Step 2: Verify git status**

Run: `git status`
Expected: Working tree clean (all committed)

**Step 3: Mark complete**

Signal completion with: `<promise>COMPLETE</promise>`
