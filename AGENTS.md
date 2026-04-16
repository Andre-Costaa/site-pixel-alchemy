# AGENTS.md — Pixel Alchemy

## Quando Ler Este Documento

- Antes de QUALQUER trabalho neste repositorio
- Ao receber uma tarefa de prospeccao, outreach ou automacao
- Ao criar novos sites demo para clientes
- Ao atualizar o CRM ou dashboard

**Doc complementares (leia depois deste):**
- `AUTOMATION.md` — credenciais, cron, scripts
- `CLAUDE.md` — convencoes de codigo e arquitetura de sites
- `scripts/README.md` — inventario e uso de cada script

---

## Quick Summary

Pixel Alchemy e uma agencia de web design brasileira. O sistema de automacao prospecta clientes automaticamente:
- Encontra negocios SEM site (cliente ideal) via SERP Maps
- Cria landing pages demo
- Faz outreach via WhatsApp (canal primario) ou email
- Rastreia tudo no Supabase PostgreSQL (fonte unica cloud — multi-agente)

---

## Fonte de Verdade: Supabase

**`public.prospects` no Supabase e a UNICA fonte de verdade para prospeccao e automacao.**

| Fonte | Funcao |
|-------|---------|
| `public.prospects` (Supabase) | Escrita e leitura de toda automacao |
| Notion CRM | Historico / referencia manual (leitura apenas) |
| `harmonizacao.csv` | Seed data (leitura apenas) |
| `prospects-novos-batch.json` | Seed data (leitura apenas) |

**Credenciais de acesso (multi-agente):**
```
SUPABASE_URL=https://iedltqijikyptxkpequc.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZGx0cWlqaWt5cHR4a3BlcXVjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDg3MzksImV4cCI6MjA5MTkyNDczOX0.lR94oA864AH_3k3TiqTX-sfjLAsKVdAopA8r7F8r2uw
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZGx0cWlqaWt5cHR4a3BlcXVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjM0ODczOSwiZXhwIjoyMDkxOTI0NzM5fQ.fmmHshdepKR_Gnj-7UxLwrcJaj-8BuN4_ymOcogSBkk
```
- `anon key` — leitura e escrita (todos os agentes)
- `service_role` — criar/drop tabelas, operacoes admin (NUNCA exposr em logs)

---

## Prospect Pipeline — Duas Camadas (Reconciliadas)

### SQLite Funnel (automacao e scripts)
```
Lead → Contatado → Respondeu → Reuniao → Proposta → Fechado
```
Usado por: `sync_notion_csv_to_sqlite.py`, `lead_discovery_maps.py`, `generate_crm_data.py`

| Estagio | Significado |
|---------|-------------|
| `Lead` | Identificado, sem contato ainda |
| `Contatado` | WhatsApp/email enviado |
| `Respondeu` | Prospect respondeu |
| `Reuniao` | Reuniao agendada/concluida |
| `Proposta` | Proposta comercial enviada |
| `Fechado` | Contrato fechado |

### Notion Pipeline (operacional detalhado)
```
Lead → Qualificado → Site em Criacao → Mensagem Pronta → Enviado → Respondeu → Reuniao → Proposta → Fechado / Perdido / Descartado
```
Usado por: Notion CRM, `notion_outbox_enqueue.py`, `notion_outbox_worker.py`

**Mapeamento SQLite ← Notion:**
- `Lead` → SQLite `Lead`
- `Qualificado / Site em Criacao / Mensagem Pronta / Enviado` → SQLite `Contatado`
- `Respondeu / Reuniao / Proposta` → mapeia diretamente
- `Fechado / Perdido / Descartado` → SQLite `Fechado` ou fora do funnel

---

## Numeros Atuais (2026-04-16)

| Metrica | Valor |
|---------|-------|
| Total prospects | 565 |
| Com telefone | ~420 |
| Com email | ~8 (1.4%) — **bloqueio principal** |
| Pipeline: Lead | 406 |
| Pipeline: Contatado | 159 |
| Respondeu/Reuniao/Proposta/Fechado | 0 |

| Nicho | Qtd |
|-------|-----|
| Veterinaria | 17+ |
| Harmonizacao | 28 |
| Beleza | 4 |
| Barbearia | 2 |
| Pet Shop | 1 |
| Dentista | 1 |
| Padaria | 1 |
| Outros | restantes |

---

## Project Structure

```
site-pixel-alchemy/
├── site-demo/                # 136+ demo sites (Vercel)
├── scripts/
│   ├── sync_supabase.py              # Sync: Notion + CSV → Supabase (NOVO)
│   ├── sync_notion_csv_to_sqlite.py   # Sync: Notion + CSV → SQLite (legado)
│   ├── lead_discovery_maps.py          # Discovery: SERP Maps (clientes SEM site)
│   ├── email_discovery.py              # Email: extrair de sites descobertos
│   ├── email_discovery_v2.py           # Email: via SERPer search (NOVO)
│   ├── generate_crm_data.py            # Dashboard: Supabase → dashboard-data.json
│   ├── done_gate.py                    # Valida deploy real
│   ├── notion_outbox_enqueue.py        # Bota update do Notion em fila
│   ├── notion_outbox_worker.py        # Consome fila e atualiza Notion
│   ├── mark_story_done.py             # Marca story como done
│   ├── message_generator.py            # Gera mensagem outreach
│   └── site_orchestrator.py            # Orquestra criacao de site
├── admin/dashboard/
│   ├── index.html           # Dashboard (senha: pixel2026)
│   └── dashboard-data.json
├── .env.example             # Template de configuracao (copie para .env)
├── .env                     # Tokens reais (NAO fazer commit)
├── template-mensagem-outreach.md   # Template de outreach
├── AUTOMATION.md            # Credenciais, cron, scripts
├── AGENTS.md                # Este arquivo (multi-agente)
└── CLAUDE.md               # Convencoes de codigo
```

**Supabase — Fonte Unica Cloud:**
```
postgresql://postgres:Pixel2026!%23@db.iedltqijikyptxkpequc.supabase.co:5432/postgres
REST: https://iedltqijikyptxkpequc.supabase.co/rest/v1/prospects
```

---

## Como Rodar Prospeccao

```bash
cd ~/site-pixel-alchemy

# 1. Carregar tokens (de .env)
source .env 2>/dev/null || true

# 2. Sync Notion + CSV → SQLite
NOTION_API_TOKEN="$NOTION_API_TOKEN" python3 scripts/sync_notion_csv_to_sqlite.py

# 3. Discovery de novos leads (SERP Maps)
SERP_API_KEY="$SERP_API_KEY" python3 scripts/lead_discovery_maps.py --niche "Veterinaria" --limit 20

# 4. Refresh dashboard
python3 scripts/generate_crm_data.py

# Dashboard
# https://www.pixelalchemy.com.br/admin/dashboard/
# Senha: pixel2026
```

---

## Regras de Outreach

De `template-mensagem-outreach.md`:
- Max 800 caracteres
- Incluir demo URL: `https://www.pixelalchemy.com.br/site-demo/<slug>/`
- Pessoa fisica (Dr./Dra.): "dele/dela", "queria"
- Empresa: "voces", "queriam"
- Healthcare: "autoridade e sofisticacao", "pacientes"
- Beauty: "estilo e profissionalismo", "clientes"
- Sem emojis

---

## Workflow Git (Demo Creation)

```bash
git add site-demo/<slug>/
git commit -m "feat: US-XXX - Client Name - Site Completo"
git push origin main
```

---

## Regras Importantes

1. **Supabase e a fonte de verdade** — toda automacao le e escreve no Supabase via REST API
2. **Nao escrever no Notion via automacao** — usar outbox pattern
3. **Tokens: SEMPRE em .env** — nunca hardcoded ou em docs
4. **Commits**: `feat: US-XXX - Name - action`
5. **Sem emojis** em codigo ou conteudo
6. **Demos auto-contidos**: HTML unico com CSS/JS inline
7. **Nao inventar numeros** — se nao tem dado, mostrar 0
8. **WhatsApp e canal primario** — 97% dos prospects tem telefone

---

## Subagent Template

Ao delegar para subagente, incluir:

```
Contexto:
- Prospect: {nome}, {nicho}
- Pipeline status: {pipeline_status}
- Demo URL: https://www.pixelalchemy.com.br/site-demo/{slug}/
- Telefone: {telefone} (WhatsApp: https://wa.me/55{ddd}{numero})
- Email: {email} (raro — 97% nao tem)
- Credenciais: ver AUTOMATION.md (tokens em .env)

Tarefa: [descricao clara do que fazer]
```

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| Prospect nao esta no Supabase | Verificar se sync_supabase.py rodou corretamente |
| Banco Supabase vazio | Verificar SUPABASE_SERVICE_ROLE_KEY no .env |
| Dashboard nao atualiza | Rodar generate_crm_data.py depois do sync |
| SERP sem credits | Verificar SERP_API_KEY em .env |
| Script token error | `cp .env.example .env` e preencha |
| Porta 5432 bloqueada | Usar REST API: https://iedltqijikyptxkpequc.supabase.co/rest/v1 |

---

## Stack

- Python 3 (scripts de automacao)
- Supabase PostgreSQL (banco — fonte unica cloud, multi-agente)
- SERPer API (Google Maps discovery)
- Vercel (hosting de demos)
- WhatsApp (canal primario de outreach)
- GitHub PAT (deploy via push)
