# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

*Add reusable patterns discovered during development here.*

- **done_gate.py requires problem_solution section**: The done_gate checks for tokens like "problema", "problem", "desafio" AND "solucao", "solution", "solu" in the HTML. Sites must include a problem/solution section to pass validation.

---

## [2026-03-12] - US-162
- **What was implemented**: Complete website for Hemocentro Heróis Vet (veterinary blood bank)
- **Files changed**:
  - `site-demo/hemocentro-herois-vet-2/index.html` - New self-contained site
- **Learnings:**
  - The done_gate.py checks for a problem/solution section by looking for specific tokens in the HTML
  - Added problem/solution section with CSS styles to pass validation
  - Business is a company (not individual Dr/Dra), so outreach message uses "vocês" and "do hemocentro"
  - Outbox pipeline: enqueue with `notion_outbox_enqueue.py`, then process with `notion_outbox_worker.py --once`
---
