# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-page promotional website for Pixel Alchemy, a premium digital agency. The site features an **Organic/Blobmorphism** design style with fluid shapes, smooth animations, and modern interactions.

**Technology Stack:**
- Pure HTML5, CSS3, and Vanilla JavaScript (no frameworks or dependencies)
- Google Fonts: Bricolage Grotesque (display) and Plus Jakarta Sans (body)
- No build process required - files run directly in browser

## Development Commands

Since this is a static website with no build system:

**To run locally:**
```bash
# Open directly in browser
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows

# Or use a simple HTTP server
python3 -m http.server 8000
# Then visit http://localhost:8000
```

**No build, compile, or test commands needed** - this is intentional for simplicity.

## Architecture & Design System

### Color System (Organic Earth Tones)

The entire color palette is defined in CSS variables at `:root` in `styles.css`:

- **Base colors**: `--color-charcoal` (dark), `--color-cream` (light background)
- **Accent colors**: `--color-terracotta` (primary CTA), `--color-sage`, `--color-lavender`, `--color-clay`
- **Each color has a `-light` variant** for hover states and subtle variations
- **Gradients**: `--gradient-warm` (terracotta→clay), `--gradient-cool` (sage→lavender)

When modifying colors, always update the CSS variables rather than hardcoding values.

### Typography Hierarchy

- **Display font** (`--font-display`): Bricolage Grotesque - used for all headings and emphasis
- **Body font** (`--font-body`): Plus Jakarta Sans - used for paragraphs and UI elements

Font sizes use fluid responsive units throughout. Major headings use `clamp()` for automatic scaling.

### The Blobmorphism System

Blob shapes are core to the design language, not just decoration:

1. **Hero blobs** (`.blob-1` through `.blob-4`): Animated background elements with `blob-float` keyframes
2. **Border radius variable**: `--border-radius-blob: 60% 40% 30% 70% / 60% 30% 70% 40%` creates organic shapes
3. **Visual blob** (`.visual-blob`): Large animated shape in hero section

Blobs use:
- CSS filters (`blur`, `backdrop-filter`)
- Transform animations (20s duration for breathing effect)
- Layered z-index for depth
- Gradients for color transitions

### Animation System

**Three animation approaches:**

1. **CSS Keyframe animations**: Used for continuous effects (blob floating, card floating, ripple)
2. **Intersection Observer + CSS classes**: For scroll-triggered animations (`.wow-fade-up`, `.wow-fade-in`)
3. **JavaScript-driven animations**: Counter numbers, tilt effects, parallax

All animations respect `prefers-reduced-motion` media query.

**Key animation files:**
- Hero animations: `script.js` lines ~1-80
- Scroll animations (WoW): `script.js` lines ~54-80
- Counter animation: `script.js` lines ~83-110
- Interactive effects: `script.js` lines ~112-200

### Section Structure

The page follows this order (each section is a semantic `<section>` with ID):

1. **Navigation** (`#nav`) - Auto-hides on scroll down, reappears on scroll up
2. **Hero** (`#home`) - Main value prop with animated blobs and floating cards
3. **Services** (`#services`) - 6 service cards in responsive grid
4. **Process** (`#process`) - 4-step process timeline
5. **About** (`#about`) - Company info with animated statistics
6. **Testimonials** (`#testimonials`) - 3 client testimonials
7. **FAQ** (`#faq`) - Accordion with 6 questions
8. **Contact** (`#contact`) - Form with name, email, service selector, message
9. **Footer** - Standard footer with links

### Component Patterns

**Service Cards** (`.service-card`):
- Hover tilt effect via JavaScript
- Icon at top, title, description, link
- Background blob decoration

**Process Steps** (`.process-step`):
- Numbered badge
- Title and description
- Connected by timeline line on desktop

**Testimonial Cards** (`.testimonial-card`):
- Star rating display
- Quote text
- Client name and company
- Profile image area

**FAQ Items** (`.faq-item`):
- Accordion functionality via JavaScript
- Question button with chevron icon
- Collapsible answer with smooth transition

**Buttons**:
- `.btn-primary`: Terracotta background with ripple effect
- `.btn-secondary`: Outlined style
- Both have icon support and hover animations

### JavaScript Architecture

Organized into logical sections (marked with comment headers):

1. **Navigation**: Scroll effects, mobile menu toggle
2. **Smooth Scroll**: Anchor link handling with offset for fixed nav
3. **WoW Animations**: Intersection Observer for scroll-triggered animations
4. **Counter Animation**: Animates numbers in About section statistics
5. **Blob Animations**: Parallax and floating effects
6. **Tilt Effect**: 3D perspective on service cards (mouse movement)
7. **Ripple Effect**: Button click animation
8. **FAQ Accordion**: Expand/collapse functionality
9. **Form Handling**: Contact form submission (currently preventDefault only)
10. **Analytics**: Placeholder for event tracking

Each section is self-contained and can be modified independently.

## Key Development Considerations

### When Adding New Sections

1. Follow the established HTML structure: `<section class="section-name" id="section-name">`
2. Add `.wow-fade-up` to elements that should animate on scroll
3. Use `data-delay` attribute for staggered animations (100ms increments)
4. Maintain consistent spacing using CSS variables (`--spacing-*`)
5. Add navigation link if section should be in menu

### When Modifying Animations

- Continuous animations should be 6-20s duration for natural feel
- Scroll animations should have 0.6-0.8s duration
- Always test with `prefers-reduced-motion: reduce` enabled
- Use `transform` and `opacity` for GPU acceleration (avoid animating `left`, `top`, `width`, `height`)

### Responsive Design Strategy

Mobile-first approach with breakpoints:
- **Base**: Mobile (<480px)
- **480px**: Small tablets
- **768px**: Tablets
- **1024px**: Desktop

Grid layouts automatically adjust:
- Services: 1 col (mobile) → 2 col (tablet) → 3 col (desktop)
- Hero: Stacked (mobile) → Side-by-side (desktop)

### Form Integration

The contact form in `script.js` (around line 150) currently only prevents default submission. To integrate with a backend:

```javascript
contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(contactForm);
    // Add your API endpoint and handling here
});
```

Form fields: `name`, `email`, `service`, `message`

### Performance Notes

- All animations use GPU-accelerated properties
- Intersection Observer unobserves elements after animation triggers (performance optimization)
- No external JS libraries reduces bundle size
- Event listeners use throttling where appropriate

## File Organization

- **index.html**: All markup and content (single file)
- **styles.css**: All styles organized by section with clear comment headers
- **script.js**: All JavaScript organized by feature with clear comment headers
- **README.md**: Documentation for end users
- **contexto.md**: Project context and design decisions (in Portuguese)

## Design Philosophy

This site prioritizes:

1. **Organic aesthetics**: Blob shapes, fluid animations, natural movement
2. **Professional elegance**: Subtle, not flashy animations
3. **CRO optimization**: Strategic CTAs, social proof, clear value proposition
4. **Mobile-first**: Touch-friendly, responsive, performant
5. **Accessibility**: ARIA labels, keyboard navigation, motion preferences
6. **No dependencies**: Vanilla everything for maximum control and minimal overhead

## Common Modifications

**To change primary accent color:**
Update `--color-terracotta` and `--color-terracotta-light` in `:root`

**To adjust animation speed globally:**
Modify `--transition-fast`, `--transition-base`, `--transition-slow` variables

**To add a new service:**
Copy a `.service-card` block in index.html and update content

**To modify blob shapes:**
Adjust `--border-radius-blob` variable percentages in `:root`

**To disable animations for testing:**
Comment out the Intersection Observer code or add `* { animation: none !important; }` temporarily
