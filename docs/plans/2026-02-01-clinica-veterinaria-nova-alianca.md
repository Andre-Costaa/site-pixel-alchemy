# Clínica Veterinária Nova Aliança Website Implementation Plan

> **For Claude:** This is a direct implementation task following the established Pixel Alchemy codebase patterns.

**Goal:** Create a professional, award-winning single-page website for Clínica Veterinária Nova Aliança using organic/blobmorphism design system.

**Architecture:** Single HTML file with embedded CSS and JavaScript, following the established design patterns from the Pixel Alchemy codebase (styles.css, script.js). No build process, runs directly in browser.

**Tech Stack:** Pure HTML5, CSS3, Vanilla JavaScript - no frameworks or dependencies.

---

## Task 1: Create Site Directory

**Files:**
- Create: `site-demo/clinica-veterinaria-nova-alianca/index.html`

**Step 1: Create directory structure**

```bash
mkdir -p site-demo/clinica-veterinaria-nova-alianca
```

---

## Task 2: Implement HTML Structure

**Files:**
- Create: `site-demo/clinica-veterinaria-nova-alianca/index.html`

**Content:** Complete HTML structure with:
- Head section with Google Fonts (Bricolage Grotesque, Plus Jakarta Sans)
- Meta tags for responsive design
- Navigation with logo and menu
- Hero section with main CTA
- Problem/Solution section
- Services section (6 services)
- Testimonials section
- Differentials/Why Choose Us section
- Contact section with form
- Footer with clinic info

**Clinic Details:**
- Name: Clínica Veterinária Nova Aliança
- Address: José Ferreira da Costa, 305 - Jardim Nova Alianca Sul, Ribeirão Preto - SP, 14027-005, Brazil
- Phone: (16) 99741-8829
- URL: pixelalchemy.com.br/site-demo/clinica-veterinaria-nova-alianca

---

## Task 3: Implement CSS Styling

**Files:**
- Modify: `site-demo/clinica-veterinaria-nova-alianca/index.html` (add `<style>` block)

**Content:** Embedded CSS following Pixel Alchemy design system:

**Color Palette (Veterinary Theme):**
```css
:root {
  /* Base colors */
  --color-charcoal: #2C3E50;
  --color-cream: #F8F5F2;

  /* Veterinary-friendly accent colors */
  --color-teal: #2A9D8F; /* Primary - calming, medical */
  --color-teal-light: #3DB8A8;
  --color-sage: #606C38; /* Natural, healing */
  --color-sage-light: #7A8A4A;
  --color-coral: #E76F51; /* Warm CTA */
  --color-coral-light: #F49A7C;
  --color-sand: #D4A373;
  --color-sand-light: #EBCAAA;

  /* Gradients */
  --gradient-warm: linear-gradient(135deg, var(--color-coral) 0%, var(--color-sand) 100%);
  --gradient-cool: linear-gradient(135deg, var(--color-teal) 0%, var(--color-sage) 100%);

  /* Border radius for blob shapes */
  --border-radius-blob: 60% 40% 30% 70% / 60% 30% 70% 40%;

  /* Spacing */
  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 2rem;
  --spacing-lg: 4rem;
  --spacing-xl: 6rem;
}
```

**Key Styles:**
- Typography: Bricolage Grotesque for headings, Plus Jakarta Sans for body
- Blob animations using `blob-float` keyframes
- Responsive grid layouts
- Button styles with ripple effect
- Smooth scroll behavior
- Mobile-first responsive design with breakpoints at 480px, 768px, 1024px

---

## Task 4: Implement JavaScript Functionality

**Files:**
- Modify: `site-demo/clinica-veterinaria-nova-alianca/index.html` (add `<script>` block)

**Content:** Embedded JavaScript with:

**1. Navigation:**
- Auto-hide on scroll down, show on scroll up
- Mobile menu toggle
- Smooth scroll for anchor links

**2. Scroll Animations (WoW):**
- Intersection Observer for `.wow-fade-up`, `.wow-fade-in` classes
- Staggered animations using `data-delay` attribute

**3. Counter Animation:**
- Animated number counters for statistics

**4. Tilt Effect:**
- 3D perspective tilt on service cards

**5. Ripple Effect:**
- Button click ripple animation

**6. Form Handling:**
```javascript
contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(contactForm);
    // WhatsApp integration or email placeholder
    const phone = '5516997418829';
    const message = `Olá! Gostaria de agendar uma consulta.\n\nNome: ${formData.get('name')}\nEmail: ${formData.get('email')}\nServiço: ${formData.get('service')}\nMensagem: ${formData.get('message')}`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank');
});
```

---

## Task 5: Add Images and Assets

**Images to Use (Unsplash/Pexels stock):**
- Hero: Veterinary clinic professional with pet
- Services: Icons (SVG) for each service
- Testimonials: Placeholder avatar images
- About: Clinic interior or team image

**Service List:**
1. Consultas Clínicas
2. Cirurgias
3. Vacinação
4. Exames Laboratoriais
5. Emergências 24h
6. Banho & Tosa

---

## Task 6: Test and Verify

**Checklist:**
- All sections render correctly
- Animations work on scroll
- Form submits to WhatsApp
- Mobile responsive (test at 375px, 768px, 1024px)
- No console errors
- All links work

---

## Task 7: Git Commit

```bash
git add site-demo/clinica-veterinaria-nova-alianca/
git commit -m "feat: US-039 - Clínica Veterinária Nova Aliança - Site Completo"
git push
```

---

## Task 8: Update Checkpoint

**Files:**
- Modify: `.ralph-tui/progress.md`

**Add completion status:**
```markdown
- [x] US-039 - Clínica Veterinária Nova Aliança - pixelalchemy.com.br/site-demo/clinica-veterinaria-nova-alianca
```

---

## Design Notes

**Visual Style:**
- Organic/blobmorphism design with fluid shapes
- Calming teal and sage color palette (appropriate for veterinary)
- Coral CTAs for conversion
- Smooth animations with intersection observer
- Professional, trustworthy aesthetic

**Key Sections:**
1. **Hero:** "Cuidado Veterinário que Seu Pet Merece" with CTA "Agendar Consulta"
2. **Problem/Solution:** "Seu pet merece o melhor cuidado veterinário"
3. **Services:** 6 services with icons
4. **Testimonials:** 3 client testimonials
5. **Differentials:** 4-5 key differentiators
6. **Contact:** Form + address + phone + map link
7. **Footer:** Copyright and social links

**CTA Strategy:**
- Primary: WhatsApp link for direct contact
- Secondary: Phone number click-to-call
- All buttons lead to appointment booking
