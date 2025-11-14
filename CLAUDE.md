# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PIXEL ALCHEMY** - A premium landing page for a technology agency featuring pastel color palette and advanced animations with Three.js, GSAP, and WebGL effects. This is a vanilla JavaScript project without build tools or package management.

## Technology Stack

- **Framework**: None (Vanilla JavaScript ES6+)
- **Styling**: Tailwind CSS (via CDN)
- **Animations**: GSAP 3.x, ScrollTrigger, Three.js
- **3D Graphics**: Three.js with custom WebGL shaders
- **No Build Process**: Direct HTML/CSS/JS files

## Project Structure

```
meu-site/
├── index.html           # Main landing page with inline Tailwind config
├── main.js             # Core application logic and animations
├── animation-fix.js    # Additional animation fixes
└── README.md           # Project documentation
```

## Design System

### Paleta de Cores Pastel Premium
- **Base**: Charcoal (#2C3E50) - Fundo principal
- **Neutro**: Platinum (#F5F2ED) - Textos e elementos claros
- **Accent 1**: Sage Green (#A8D5BA) - Verde suave pastel
- **Accent 2**: Rose Dust (#D4A5A5) - Rosa empoeirado pastel
- **Accent 3**: Lavender (#B8B9D3) - Lavanda pastel
- **Accent 4**: Teal (#7FA8A8) - Verde-azulado
- **Accent 5**: Peach (#F0D8C8) - Pêssego suave
- **Accent 6**: Silver (#C0C5CE) - Prata acinzentado
- **Variações**: Todas as cores têm versões com 20%, 40%, 60%, 80% de opacidade

### Typography
- **Primary**: Space Grotesk (headings and titles)
- **Secondary**: Inter (body text and UI)

### Visual Style
- Premium design with sophisticated pastel aesthetics
- Glassmorphism effects with soft colors
- Balanced contrast with harmonious palette
- Smooth animations and premium interactions

## Development Commands

Since this is a vanilla JavaScript project, there are no npm scripts. Use a local server:

```bash
# Python simple server
python -m http.server 8000

# Or Node.js serve
npx serve .

# Or VS Code Live Server extension
# Right-click index.html → Open with Live Server
```

Access at `http://localhost:8000`

## Key Architecture Concepts

### 1. Neural Network WebGL Canvas (Hero Section)
- `main.js` contains Three.js scene setup
- Particle system with interconnected nodes
- Animated using `requestAnimationFrame`
- Performance optimized for 60fps

### 2. GSAP ScrollTrigger Animations
- Sections animate on scroll
- Elements fade in and slide up sequentially
- Scroll-driven particle effects
- Smooth scrolling behavior

### 3. Interactive Elements
- Hover effects with directional glow
- Form validation and visual feedback
- Cursor trail effects
- Responsive card interactions

### 4. Performance Considerations
- Lazy loading for below-fold content
- `requestAnimationFrame` for animations
- Optimized particle count for mobile
- CSS will-change for animation performance

## Sections Structure

1. **Hero**: WebGL neural network canvas + animated title with glow
2. **Services**: 6 premium service cards with glassmorphism
3. **Process**: 4-step creative process with sequential animations
4. **About**: Animated statistics grid
5. **Contact**: Form with elegant validation

## Making Changes

### Adding New Sections
1. Add HTML structure to `index.html`
2. Add GSAP animations in `main.js`
3. Maintain pastel color palette from defined colors
4. Test scroll animations
5. Verify mobile responsiveness

### Modifying Animations
```javascript
// In main.js, adjust GSAP timelines
gsap.from('.element', {
  duration: 1,
  y: 50,
  opacity: 0,
  scrollTrigger: {
    trigger: '.element',
    start: 'top 80%'
  }
});
```

### Changing Colors
Use the predefined Tailwind color palette:
```css
/* Acceptable - using pastel palette colors */
bg-eterus-charcoal      /* Main background */
text-eterus-platinum    /* Light text */
bg-eterus-sage          /* Pastel green */
text-eterus-rose        /* Pastel rose */
border-eterus-lavender  /* Lavender border */

/* With opacity */
bg-eterus-sage-20       /* Sage with 20% opacity */
text-eterus-rose-80     /* Rose with 80% opacity */

/* NOT acceptable */
bg-blue-500             /* Colors outside defined palette */
```

## Testing

### Browser Compatibility
- Chrome 90+ (primary target)
- Firefox 88+
- Safari 14+
- Test WebGL support on target browsers

### Performance Testing
1. Open Chrome DevTools → Performance tab
2. Record scroll interactions
3. Verify 60fps during animations
4. Check for layout shifts (CLS < 0.1)

### Accessibility Testing
1. Keyboard navigation (Tab order)
2. Screen reader compatibility
3. Contrast verification (use Chrome DevTools)
4. Focus indicators visibility

## Performance Targets

- **Lighthouse Score**: 95+ (Performance)
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Animation FPS**: 60fps consistent

## Important Considerations

- **No Build Process**: All changes are immediate - refresh browser to see updates
- **CDN Dependencies**: Three.js, GSAP loaded from CDN - ensure network availability
- **Inline Tailwind Config**: Tailwind configuration is in `index.html` head section
- **WebGL Fallback**: Ensure graceful degradation if WebGL is unavailable
- **Mobile Performance**: Test particle count on lower-end devices
- **Paleta Pastel Estrita**: Use apenas as cores definidas na paleta pastel premium

## Common Tasks

### Update Content
Edit directly in `index.html` - no build step required

### Adjust Animation Timing
Modify GSAP parameters in `main.js`:
```javascript
// Increase/decrease duration
duration: 1.5  // seconds

// Adjust easing
ease: "power3.out"
```

### Optimize Performance
```javascript
// Reduce particle count for mobile
const particleCount = window.innerWidth < 768 ? 75 : 150;

// Throttle scroll listeners
const throttledScroll = throttle(handleScroll, 16); // 60fps
```

## Troubleshooting

### Animations Not Working
- Check browser console for JavaScript errors
- Verify GSAP and ScrollTrigger CDN loaded successfully
- Ensure HTML elements have correct class names
- Check ScrollTrigger triggers with: `ScrollTrigger.getAll()`

### WebGL Canvas Issues
- Verify WebGL support: `renderer.capabilities.isWebGLAvailable`
- Check browser console for WebGL errors
- Test on different browsers/devices
- Ensure canvas dimensions are set correctly

### Performance Issues
- Reduce particle count in `main.js`
- Disable animations on lower-end devices
- Use `will-change` CSS property sparingly
- Check for memory leaks in DevTools Performance tab

## File References

- `index.html:1-500` - Main HTML structure with all sections
- `main.js:1-100` - Three.js scene setup and particle system
- `main.js:100-200` - GSAP scroll animations
- `main.js:200-300` - Event handlers and interactions
- `animation-fix.js` - Additional animation patches

## Related Documentation

- [Three.js Documentation](https://threejs.org/docs/)
- [GSAP Documentation](https://greensock.com/docs/)
- [ScrollTrigger Guide](https://greensock.com/docs/v3/Plugins/ScrollTrigger)
- [Tailwind CSS](https://tailwindcss.com/docs)
