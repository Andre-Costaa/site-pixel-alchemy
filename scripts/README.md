# Scripts de Automação — Pixel Alchemy

Este diretório contém scripts Python para automação do workflow de criação de sites e gestão do Notion CRM.

## Visão Geral do Workflow

```
Prospecto no Notion (Status: "Qualificado")
    ↓
[1] site_orchestrator.py gera user story no prd.json
    ↓
[2] Ralph TUI / Agente cria o site usando prompt-modelo.md
    ↓
[3] Agente pesquisa email de contato do negocio e registra no campo Email do Notion
    ↓
[4] Agente gera mensagem de outreach (template-mensagem-outreach.md)
    ↓
[5] Agente enfileira update no Notion (outbox) e processa com worker (sem MCP)
    Status → "Mensagem Pronta"
    URL Demo, Mensagem, Slug, US ID, Site Criado Em, Email (quando encontrado)
    ↓
[6] Commit: "feat: US-XXX - Nome Cliente - Site Completo"
```

## Arquivos

### `config.py`
Configuração centralizada com:
- Autoload de `.env` no root do projeto (sem precisar `source .env` manual)
- Variáveis já definidas no ambiente têm prioridade sobre `.env`
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
Gera user stories no `prd.json` a partir de prospectos exportados do Notion (JSON).

**Uso**:
```bash
# Ver o que seria gerado (dry run)
python3 scripts/site_orchestrator.py --dry-run

# Gerar user stories de todos os prospectos qualificados
python3 scripts/site_orchestrator.py --from-json prospects.json

# Gerar para um prospecto específico
python3 scripts/site_orchestrator.py --from-json prospects.json --name "Dra. Laura"
```

**Output**: Adiciona user stories ao `prd.json` com acceptance criteria completo, incluindo:
- Criação do site seguindo `prompt-modelo.md`
- **Pesquisa e registro de email** de contato do negócio
- **Geração de mensagem de outreach** (ver `template-mensagem-outreach.md`)
- **Atualização do Notion** com URL Demo, Mensagem, Slug, US ID, Site Criado Em
- Commit e push

### `notion_client.py`
Wrapper para Notion:
- geração de payloads MCP (quando rodando dentro do Claude Code)
- cliente REST standalone (`NotionAPIClient`) para execução sem MCP

### `notion_outbox_enqueue.py` / `notion_outbox_worker.py`
Atualização confiável do Notion via outbox + receipts (sem “prova por log”).

**Comandos principais (produção)**:

```bash
# Atualização a partir da story (recomendado quando há notionPageId)
python3 scripts/notion_update_from_prd.py --us-id US-089 --prd ./prd.json --mensagem-file /tmp/mensagem.txt --site-criado-em 2026-02-23 --process

# Com email pesquisado
python3 scripts/notion_update_from_prd.py --us-id US-089 --prd ./prd.json --mensagem-file /tmp/mensagem.txt \
  --site-criado-em 2026-02-23 --email "contato@exemplo.com" --process

# Atualização manual via outbox (uso excepcional; prefira manter notionPageId no PRD)
python3 scripts/notion_outbox_enqueue.py --us-id US-089 --page-id <NOTION_PAGE_ID> \
  --status "Mensagem Pronta" --url-demo "https://www.pixelalchemy.com.br/site-demo/<slug>/" \
  --slug "<slug>" --site-criado-em "2026-02-23" --mensagem-file /tmp/mensagem.txt
python3 scripts/notion_outbox_worker.py --once
```

**IMPORTANTE**: Após criar um site, o agente DEVE atualizar o Notion via outbox para gerar receipt verificável.

### `reconcile_prd_notion_links.py`
Reconcilia stories legadas do `prd.json` com páginas reais do Notion por `slug`.

Comportamento:
- `dry-run` por padrão
- grava em `prd.json` somente com `--apply`
- aplica apenas matches únicos e seguros
- gera relatório JSON em `.sinfonia/reports/`

```bash
# Relatório completo sem alterar o PRD
python3 scripts/reconcile_prd_notion_links.py

# Relatório + escrita no PRD apenas para matches únicos
python3 scripts/reconcile_prd_notion_links.py --apply

# Reconciliar uma story específica
python3 scripts/reconcile_prd_notion_links.py --us-id US-090
python3 scripts/reconcile_prd_notion_links.py --us-id US-090 --apply
```

### `sync_story_identity_to_notion.py`
Sincroniza campos de identidade da story para a página já vinculada no Notion.

Uso recomendado para corrigir conflitos em que a story já tem `notionPageId`, mas a página do Notion está sem `Slug` ou `US ID`, ou com `Slug` divergente.

Comportamento:
- `dry-run` por padrão
- grava no Notion somente com `--apply`
- usa outbox + worker para gerar receipt e verificar leitura após escrita

```bash
# Relatório sem alterar o Notion
python3 scripts/sync_story_identity_to_notion.py

# Aplicar updates seguros no Notion
python3 scripts/sync_story_identity_to_notion.py --apply

# Limitar a uma story específica
python3 scripts/sync_story_identity_to_notion.py --us-id US-166
python3 scripts/sync_story_identity_to_notion.py --us-id US-166 --apply
```

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

### `ralph_autoclose.py`
Sidecar de auto-conclusão: observa `session.json` do Ralph e executa
`mark_story_done.py` automaticamente quando uma task fica `completed`.

```bash
# Rodar em paralelo ao ralph-tui
python3 scripts/ralph_autoclose.py --prd ./prd.json

# Rodar uma varredura única
python3 scripts/ralph_autoclose.py --prd ./prd.json --once
```

### `ralph_run_auto.py`
Comando único para rodar `ralph-tui` + sidecar de auto-conclusão.

```bash
# Fluxo recomendado (sem retrabalho)
python3 scripts/ralph_run_auto.py --prd ./prd.json --parallel 1

# Smoke test
python3 scripts/ralph_run_auto.py --prd ./prd.smoke.json --parallel 1 --force
```

## Workflow Completo para Agentes

Quando você (agente) for criar um site para um prospecto:

### 1. Receber user story do `prd.json`
O user story já contém os dados necessários nos acceptance criteria e deve conter `notionPageId` quando exigir update no Notion.

Se a story exigir Notion e `notionPageId` estiver ausente:

```bash
python3 scripts/reconcile_prd_notion_links.py --us-id US-XXX
python3 scripts/reconcile_prd_notion_links.py --us-id US-XXX --apply
```

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

### 4. Pesquisar e registrar email
- Procurar email de contato do negocio (site oficial, Google, Instagram, Facebook)
- Nunca inferir email por padrao de dominio sem prova
- Registrar no campo `Email` do Notion quando encontrar
- Se nao houver email, o fluxo **nao bloqueia**: seguir com WhatsApp/Instagram normalmente

### 5. Atualizar Notion CRM
- **OBRIGATÓRIO**: Atualizar via outbox (sem MCP) para ter receipt verificável.
- Campos a atualizar:
  - `Status` → **"Mensagem Pronta"** (não "Site Pronto")
  - `URL Demo` → URL completa do site
  - `Mensagem` → mensagem gerada no passo 3
  - `Slug` → slug do site
  - `US ID` → ID da user story (ex: "US-089")
  - `Site Criado Em` → data de hoje (YYYY-MM-DD)
  - `Email` quando encontrado durante pesquisa

**Exemplo**:
```bash
python3 scripts/notion_outbox_enqueue.py --us-id US-089 --page-id <NOTION_PAGE_ID> \\
  --status "Mensagem Pronta" --url-demo "https://www.pixelalchemy.com.br/site-demo/<slug>/" \\
  --slug "<slug>" --site-criado-em "2026-02-23" --mensagem-file /tmp/mensagem.txt \\
  --email "contato@exemplo.com"
python3 scripts/notion_outbox_worker.py --once
```

**Comando preferido quando a story tem `notionPageId`**:
```bash
python3 scripts/notion_update_from_prd.py --us-id US-089 --mensagem-file /tmp/mensagem.txt --site-criado-em 2026-02-23 --process
```

**Importante**: para novas stories, `notionPageId` nao e opcional. O `site_orchestrator.py` deve bloquear criacao de story sem esse campo no payload do prospect.

### 6. Commit
```bash
git add site-demo/<slug>/
git commit -m "feat: US-XXX - Nome do Cliente - Site Completo

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

### 7. Done Gate (OBRIGATORIO)
Antes de marcar `passes=true` no `prd.json`, valide a story:

```bash
python3 scripts/done_gate.py --us-id US-XXX
```

Se retornar `DONE GATE: PASS`, marque a story como concluida com:

```bash
python3 scripts/mark_story_done.py --us-id US-XXX
```

Se falhar, nao marque como concluida. Corrija os pontos reportados.

**Modo automático equivalente ao fluxo manual**:
```bash
python3 scripts/ralph_run_auto.py --prd ./prd.json --parallel 1
```

## Checklist de Conclusão

Antes de marcar uma user story como completa, verificar:

- [ ] Site criado em `site-demo/<slug>/index.html`
- [ ] Site testado localmente (responsivo 480/768/1024/1440px)
- [ ] Mensagem de outreach gerada seguindo template
- [ ] Story contains `notionPageId` before Notion update
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
→ Use o pipeline outbox (`notion_outbox_enqueue.py` + `notion_outbox_worker.py`) ou `notion_update_from_prd.py --process`.

### "Mensagem muito genérica"
→ Releia `template-mensagem-outreach.md` e adapte tom ao nicho específico.

### "Done gate falha em Notion receipt"
→ Verifique `NOTION_TOKEN`, rode `python3 scripts/notion_outbox_worker.py`, e inspecione `.notion-outbox/` (ver `docs/runbooks/notion-outbox.md`).

### "Erro ao gerar slug único"
→ Use `slug_utils.ensure_unique_slug()` para garantir que não haja colisão.
