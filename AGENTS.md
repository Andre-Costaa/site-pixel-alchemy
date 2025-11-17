# Repository Guidelines

## Project Structure & Module Organization
- Single-page site with entry point at `index.html`; global styles in `styles.css`; behaviors in `script.js`.
- Brand assets live at `favicon.svg`, `logo.svg` and `apple-touch-icon.png.html`; manifest at `site.webmanifest`.
- Visual baselines for QA are in `.playwright-mcp/` (PNG captures of expected states); keep them updated when UI changes.
- Additional context lives in `README.md` (design notes) and `contexto.md`/`CLAUDE.md` (authoring guidance).

## Build, Test, and Development Commands
- No build step; the stack is vanilla HTML/CSS/JS. Open `index.html` directly or serve locally for smooth navigation and font loading:
  - `python3 -m http.server 5500` (or similar) from the repo root, then visit `http://localhost:5500`.
- For quick CSS/JS checks, reload the page; there is no bundler or watcher in use.

## Coding Style & Naming Conventions
- HTML: keep sections semantic (`header`, `section`, `footer`) and mirror the existing section labels and hierarchy.
- CSS: 4-space indentation; leverage existing custom properties (`--color-*`, `--spacing-*`, etc.) before adding new tokens. Class names are lowercase-kebab (e.g., `nav-menu`, `hero-blob`). Use the sectioned comment blocks already present for new areas.
- JS: vanilla ES6, `const`/`let` with camelCase identifiers (e.g., `trackEvent`, `navToggle`). Keep behaviors modular by grouping related logic under the documented headers and prefer `QuerySelector` APIs.
- Assets: prefer optimized SVG/PNG, matching the current visual style. Avoid introducing heavy dependencies.

## Testing Guidelines
- There is no automated test suite. Do a manual pass on key breakpoints (desktop, 1024px, 768px, 480px) verifying nav scroll behavior, hero animations, accordion, stats counter, and contact form flow.
- Use the images in `.playwright-mcp/` to compare states such as mobile menu open/closed and post-scroll nav.
- Respect `prefers-reduced-motion`; ensure new animations degrade gracefully.

## Commit & Pull Request Guidelines
- Follow the existing Git style: `Type: Description` with a capitalized type (e.g., `Refactor: Ajustar animações do hero`, `feat: add mobile menu tests`). Keep messages concise and action-oriented; Portuguese descriptions are common.
- PRs should describe the change, affected sections, and any design impacts. Attach before/after screenshots (desktop and mobile) when UI changes, note manual test steps/browsers, and link related issues or tasks if applicable.
