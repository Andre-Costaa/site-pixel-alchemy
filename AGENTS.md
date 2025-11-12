# Repository Guidelines

## Project Structure & Module Organization
The site is a static landing page served directly from the repository root. `index.html` contains the layout, inline styles, and the Tailwind utility classes that drive most visuals. Interactive behaviors (particle canvas, scroll reveal, counters) live in `main.js`, while `main-premium.js` contains experimental premium-only effects. Assets such as the favicon, animation helpers, and prototype files sit beside the HTML for easy relative imports. No build step is required; shipping the root directory publishes the entire experience.

## Build, Test, and Development Commands
- `npm install` — pulls the minimal dev dependencies (Playwright tooling and shadcn preset) so optional scripts can run.
- `npx serve@latest -s .` — spins up a zero-config static server for local preview; any similar tool (e.g., `python3 -m http.server 4173`) works as long as it serves the repository root.
- `npx playwright test` — placeholder end-to-end suite; create tests under `tests/e2e` before running, and execute `npx playwright install` once per machine to fetch browsers.

## Coding Style & Naming Conventions
Prefer semantic HTML sections and keep Tailwind-style utility classes grouped from general to specific (layout → spacing → color → effects). Indent HTML and JS with four spaces. CSS added inside `<style>` tags should stay grouped by component (e.g., `.about-metrics-panel` block), with brief comments only for non-obvious behaviors. Name new JS modules with kebab-case filenames (e.g., `hero-effects.js`) and export functions in camelCase.

## Testing Guidelines
There is no legacy suite, so target every interactive module you touch. For UI checks, add Playwright specs inside `tests/e2e`. Name files after the feature (`about-metrics.spec.ts`) and cover at least the primary viewport states (desktop and mobile widths). Run `npx playwright test --headed` when debugging animations and include relevant screenshots or videos in pull requests when tests fail locally.

## Commit & Pull Request Guidelines
Existing history uses descriptive sentence-style messages (“Initial commit: …”). Follow the `type: short summary` pattern when adding features (e.g., `feat: refine about metrics layout`). Each pull request should include: concise summary, before/after screenshots or screen-recordings for visual tweaks, linked issue or task ID, and a checklist of tests executed (manual viewports or automated). Keep branches focused on a single concern and rebase before requesting review to avoid merge clutter.

## Security & Configuration Tips
Never commit API keys or service credentials; the project only needs static assets. If a feature does require secrets (analytics tokens, form handlers), load them through environment-specific `.env` files ignored by Git and inject via server-side tooling, not directly in `index.html`.
