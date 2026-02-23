# Scripts de Automação — Pixel Alchemy

Este diretório contém scripts Python para automação do workflow de criação de sites e gestão do Notion CRM.

## Visão Geral do Workflow

```
Prospecto no Notion (Status: "Qualificado")
    ↓
[1] site_orchestrator.py gera user story no tasks/prd.json
    ↓
[2] Ralph TUI / Agente cria o site usando prompt-modelo.md
    ↓
[3] Agente gera mensagem de outreach (template-mensagem-outreach.md)
    ↓
[4] Agente enfileira update no Notion (outbox) e processa com worker (sem MCP)
    Status → "Mensagem Pronta"
    URL Demo, Mensagem, Slug, US ID, Site Criado Em
    ↓
[5] Commit: "feat: US-XXX - Nome Cliente - Site Completo"
```

## Arquivos

### `config.py`
Configuração centralizada com:
- Paths do projeto (PRD_JSON_PATH, SITE_DEMO_DIR)
- IDs do Notion (DATABASE_ID, DATA_SOURCE_ID)
- URLs base (SITE_DEMO_BASE_URL)
- Prefixos de ID por nicho
- Pipeline de status

### `slug_utils.py`
Utilitários para geração de slugs:
- `generate_slug(nome)` — converte nome em slug URL-safe
- `ensure_unique_slug(slug, existing)` — garante unicidade adicionando sufixo numérico
- `get_existing_slugs()` — lista todos os slugs em `site-demo/`

### `site_orchestrator.py`
Gera user stories no `tasks/prd.json` a partir de prospectos exportados do Notion (JSON).

**Uso**:
```bash
# Ver o que seria gerado (dry run)
python3 scripts/site_orchestrator.py --dry-run

# Gerar user stories de todos os prospectos qualificados
python3 scripts/site_orchestrator.py --from-json prospects.json

# Gerar para um prospecto específico
python3 scripts/site_orchestrator.py --from-json prospects.json --name "Dra. Laura"
```

**Output**: Adiciona user stories ao `tasks/prd.json` com acceptance criteria completo, incluindo:
- Criação do site seguindo `prompt-modelo.md`
- **Geração de mensagem de outreach** (ver `template-mensagem-outreach.md`)
- **Atualização do Notion** com URL Demo, Mensagem, Slug, US ID, Site Criado Em
- Commit e push

### `notion_client.py`
Wrapper para Notion:
- geração de payloads MCP (quando rodando dentro do Claude Code)
- cliente REST standalone (`NotionAPIClient`) para execução sem MCP

### `notion_outbox_enqueue.py` / `notion_outbox_worker.py`
Atualização confiável do Notion via outbox + receipts (sem “prova por log”).

**Funções principais**:

```python
# Buscar prospectos por query
mcp_search_prospects(query="Qualificado")

# Buscar dados de um prospecto específico
mcp_fetch_prospect(page_id="...")

# Atualizar prospecto com dados do site criado
build_site_ready_update(
    page_id="notion-uuid",
    slug="dra-laura-sanches",
    us_id="US-089",
    url_demo="https://www.pixelalchemy.com.br/site-demo/dra-laura-sanches/",
    site_created_date="2026-02-22",
    mensagem="Olá! Sou o André, fundador da Pixel Alchemy..."
)

# Marcar site como em criação
build_site_in_progress_update(page_id="notion-uuid")
```

**IMPORTANTE**: Após criar um site, o agente DEVE chamar `build_site_ready_update()` com a mensagem gerada para atualizar o Notion corretamente.

### `message_generator.py`
Módulo Python para geração programática de mensagens (referência).

**Uso**:
```python
from message_generator import generate_cold_message, infer_genero_from_nome

genero = infer_genero_from_nome("Dra. Laura Sanches")  # → "feminino"

mensagem = generate_cold_message(
    nome="Dra. Laura Sanches",
    nicho="Dentista",
    slug="dra-laura-sanches",
    genero=genero
)
```

**NOTA**: Este módulo serve como **referência**. Na prática, o **agente LLM é quem gera** a mensagem usando o `template-mensagem-outreach.md` porque ele tem mais contexto sobre o site criado e pode adaptar melhor o tom e conteúdo.

### `ralph_heartbeat_tui.py`
Monitor em Python com TUI moderna para acompanhar sessão ativa do `ralph-tui` com heartbeat periódico.

**Mostra em tempo real**:
- status da sessão (`running`, `paused`, `completed`, etc.)
- progresso de tarefas e iterações
- cauda de log da iteração mais recente
- sinais de erro e tempo de inatividade
- recomendação objetiva: **`CONTINUE`** ou **`STOP`** (inclui "Parar agora? SIM/NAO")

**Heartbeat**:
- padrão: **5 minutos** (`300s`)
- persistência em JSONL: `.ralph-tui/heartbeat/heartbeat.jsonl`

**Uso**:
```bash
# TUI em tempo real
python3 scripts/ralph_heartbeat_tui.py

# Snapshot único (debug/validação rápida)
python3 scripts/ralph_heartbeat_tui.py --once

# Heartbeat a cada 2 minutos
python3 scripts/ralph_heartbeat_tui.py --heartbeat-seconds 120
```

## Workflow Completo para Agentes

Quando você (agente) for criar um site para um prospecto:

### 1. Receber user story do `tasks/prd.json`
O user story já contém todos os dados necessários nos acceptance criteria.

### 2. Criar o site
- Seguir `prompt-modelo.md` rigorosamente
- Criar pasta `site-demo/<slug>/`
- Gerar `index.html` self-contained (CSS + JS inline)

### 3. Gerar mensagem de outreach
- **OBRIGATÓRIO**: Consultar `template-mensagem-outreach.md`
- Identificar tipo de negócio (pessoa física vs empresa)
- Adaptar tom ao nicho (formal para saúde, descontraído para outros)
- Usar pronomes corretos:
  - Pessoa física (Dra./Dr.): "dele/dela", "queria", "do consultório da"
  - Empresa: "vocês", "queriam", "da clínica/pizzaria/barbearia"
- Incluir URL completa do site demo
- Manter abaixo de 800 caracteres

### 4. Atualizar Notion CRM
- **OBRIGATÓRIO**: Atualizar via outbox (sem MCP) para ter receipt verificável.
- Campos a atualizar:
  - `Status` → **"Mensagem Pronta"** (não "Site Pronto")
  - `URL Demo` → URL completa do site
  - `Mensagem` → mensagem gerada no passo 3
  - `Slug` → slug do site
  - `US ID` → ID da user story (ex: "US-089")
  - `Site Criado Em` → data de hoje (YYYY-MM-DD)

**Exemplo**:
```bash
python3 scripts/notion_outbox_enqueue.py --us-id US-089 --page-id <NOTION_PAGE_ID> \\
  --status "Mensagem Pronta" --url-demo "https://www.pixelalchemy.com.br/site-demo/<slug>/" \\
  --slug "<slug>" --site-criado-em "2026-02-23" --mensagem-file /tmp/mensagem.txt
python3 scripts/notion_outbox_worker.py --once
```

**Alternativa (recomendado quando a story tem `notionPageId`)**:
```bash
python3 scripts/notion_update_from_prd.py --us-id US-089 --mensagem-file /tmp/mensagem.txt --site-criado-em 2026-02-23 --process
```

### 5. Commit
```bash
git add site-demo/<slug>/
git commit -m "feat: US-XXX - Nome do Cliente - Site Completo

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

### 6. Done Gate (OBRIGATORIO)
Antes de marcar `passes=true` no `tasks/prd.json`, valide a story:

```bash
python3 scripts/done_gate.py --us-id US-XXX
```

Se retornar `DONE GATE: PASS`, marque a story como concluida com:

```bash
python3 scripts/mark_story_done.py --us-id US-XXX
```

Se falhar, nao marque como concluida. Corrija os pontos reportados.

## Checklist de Conclusão

Antes de marcar uma user story como completa, verificar:

- [ ] Site criado em `site-demo/<slug>/index.html`
- [ ] Site testado localmente (responsivo 480/768/1024/1440px)
- [ ] Mensagem de outreach gerada seguindo template
- [ ] Notion atualizado com Status "Mensagem Pronta" + todos os campos
- [ ] Commit realizado com mensagem correta
- [ ] Push para repositório remoto
- [ ] `python3 scripts/done_gate.py --us-id US-XXX` retornou PASS

## Referências

- **Prompt de criação de sites**: `../prompt-modelo.md`
- **Template de mensagens**: `../template-mensagem-outreach.md`
- **Instruções gerais do projeto**: `../CLAUDE.md`
- **Notion CRM**: Database ID `2f76f51e-b8a5-8088-a52c-db29fc3c1f81`

## Troubleshooting

### "Site criado mas Notion não foi atualizado"
→ Certifique-se de chamar `build_site_ready_update()` com TODOS os parâmetros, incluindo `mensagem`.

### "Mensagem muito genérica"
→ Releia `template-mensagem-outreach.md` e adapte tom ao nicho específico.

### "Done gate falha em Notion receipt"
→ Verifique `NOTION_TOKEN`, rode `python3 scripts/notion_outbox_worker.py`, e inspecione `.notion-outbox/` (ver `docs/runbooks/notion-outbox.md`).

### "Erro ao gerar slug único"
→ Use `slug_utils.ensure_unique_slug()` para garantir que não haja colisão.
