---
name: pixel-alchemy-site-pipeline
version: 1
max_retries: 2
timeout_minutes: 30
requires:
  - prd.json
  - template-mensagem-outreach.md
  - scripts/reconcile_prd_notion_links.py
  - scripts/done_gate.py
  - scripts/notion_outbox_enqueue.py
  - scripts/notion_outbox_worker.py
  - AGENTS.md
---

# Pixel Alchemy Site Pipeline

You are executing user story **{{us_id}}** for Pixel Alchemy.

**Read `AGENTS.md` before starting.** It contains all project conventions, design system, and coding standards.

---

## Step 1: Read the user story from prd.json

```bash
python3 -c "import json; prd=json.load(open('prd.json')); story=[s for s in prd['userStories'] if s['id']=='{{us_id}}'][0]; print(json.dumps(story, indent=2, ensure_ascii=False))"
```

Extract and confirm:
- **Nome**: {{nome}}
- **Slug**: {{slug}}
- **Nicho**: {{nicho}}
- **Telefone**: {{telefone}}
- **Endereco**: {{endereco}}
- **Notion Page ID**: {{notion_page_id}}

If `Notion Page ID` is missing, STOP and reconcile before proceeding:

```bash
python3 scripts/reconcile_prd_notion_links.py --us-id {{us_id}}
python3 scripts/reconcile_prd_notion_links.py --us-id {{us_id}} --apply
```

If any required field is still missing after reconciliation, STOP and exit with error.

---

## Step 2: Research the business

Search for real information about **{{nome}}**:
- Google: services offered, opening hours, team members
- Instagram: brand colors, visual style, recent posts
- Facebook: reviews, photos, business description

Use this research to populate the site with real data. Do NOT use placeholder content.

---

## Step 3: Create the site

```bash
mkdir -p site-demo/{{slug}}
```

Create `site-demo/{{slug}}/index.html` as a **self-contained single file** (inline CSS + JS). Requirements:

1. All 9 standard sections: Navigation, Hero, Services, Process, Differentials, Testimonials, FAQ, Contact, Footer
2. Contact form with: name, email/phone, service selector, message
3. Real business info from Step 2 (phone, address, services, testimonials)
4. Color palette adapted to the business niche and brand
5. Responsive at all breakpoints: 480px, 768px, 1024px, 1440px
6. Blobmorphism design system (see AGENTS.md)
7. Scroll animations with Intersection Observer
8. No emojis anywhere in code or content
9. No external CSS/JS files — everything inline

---

## Step 4: Generate outreach message

Read `template-mensagem-outreach.md` for the template and examples.

Determine if **{{nome}}** is:
- **Pessoa fisica** (Dr./Dra. + name): use "dele/dela", "do consultorio da Dra./do Dr.", "queria"
- **Empresa** (business name): use "voces", "da clinica/barbearia/pizzaria", "queriam"

Adapt tone to **{{nicho}}**:
- Healthcare (Dentista, Veterinaria, Harmonizacao): "autoridade e sofisticacao", "pacientes"
- Beauty (Beleza, Barbearia): "estilo e profissionalismo", "clientes"
- Food (Pizzaria, Padaria, Acougue): "apetite e qualidade", "clientes"
- Pet Shop: "confianca e profissionalismo", "tutores"

Rules:
- Max 800 characters
- Include URL: `https://www.pixelalchemy.com.br/site-demo/{{slug}}/`
- Follow the exact template structure from `template-mensagem-outreach.md`

Save the message:

```bash
cat > /tmp/mensagem-{{us_id}}.txt << 'EOF'
[generated message here]
EOF
```

---

## Step 5: Update Notion via outbox

**ALL fields are required. The outbox will BLOCK if any is missing.**

Preferred command:

```bash
python3 scripts/notion_update_from_prd.py --us-id {{us_id}} --mensagem-file /tmp/mensagem-{{us_id}}.txt --site-criado-em {{date}} --process
```

Fallback only if you already have a verified `{{notion_page_id}}` and need manual control:

```bash
cd scripts && python3 notion_outbox_enqueue.py \
  --us-id {{us_id}} \
  --page-id {{notion_page_id}} \
  --status "Mensagem Pronta" \
  --url-demo "https://www.pixelalchemy.com.br/site-demo/{{slug}}/" \
  --slug "{{slug}}" \
  --mensagem-file /tmp/mensagem-{{us_id}}.txt \
  --site-criado-em {{date}}
python3 notion_outbox_worker.py --once
```

Verify the receipt was created. If the worker fails, check `NOTION_TOKEN` and retry.

---

## Step 6: Commit and push

```bash
git add site-demo/{{slug}}/
git commit -m "feat: {{us_id}} - {{nome}} - Site Completo"
git push origin main
```

Do NOT use `git add .` or `git add -A`.

---

## Step 7: Run done gate

```bash
cd scripts && python3 done_gate.py --us-id {{us_id}}
```

**If output is `DONE GATE: PASS`**: Exit with code 0. The orchestrator will mark the story as done.

**If output is `DONE GATE: FAIL`**: Read the specific check failures, fix the issues, and re-run the done gate. If you cannot fix them, exit with a non-zero code and describe the failures in your output.

**Do NOT run `mark_story_done.py` yourself.** The orchestrator handles that after validating your done_gate result.
