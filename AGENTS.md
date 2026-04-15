# AGENTS.md — Pixel Alchemy

## Quick Summary

Pixel Alchemy e uma agencia de web design brasileira. O sistema de automacao prospecta clientes automaticamente:
- Encontra negocios sem site bom
- Cria landing pages demo (ja criadas para a maioria)
- Faz outreach via WhatsApp/email
- Rastreia tudo no SQLite

## Read First

Antes de qualquer trabalho, leia estes arquivos:
1. `PROSPECTION.md` — workflow de prospeccao
2. `AUTOMATION.md` — credenciais e configuracao
3. `CLAUDE.md` — visao geral do projeto e Convencoes de codigo

## Project Structure

```
site-pixel-alchemy/
├── prospects.db          # Automation brain (SQLite) — FONTE UNICA DE VERDADE
├── site-demo/            # 136+ demo sites (deployed on Vercel)
├── scripts/
│   ├── sync_notion_csv_to_sqlite.py  # Import: Notion + CSV + JSON → SQLite
│   ├── generate_crm_data.py          # Dashboard: SQLite → dashboard-data.json
│   └── outreach.py       # Pipeline de outreach (WIP)
├── admin/dashboard/
│   ├── index.html        # Dashboard HTML (protegido com senha)
│   └── dashboard-data.json
├── harmonizacao.csv      # Fonte de dados (leitura apenas)
└── prospects-novos-batch.json  # Fonte de dados (leitura apenas)
└── template-mensagem-outreach.md    # Mensagem de outreach
```

## Fonte de Verdade: SQLite

**prospects.db e a UNICA fonte de verdade para prospeccao.**

| Fonte | Funcao |
|-------|--------|
| `prospects.db` (SQLite) | Escrita e leitura de automacao |
| Notion CRM | Historico / referencia manual (leitura apenas) |
| harmonizacao.csv | Seed data (leitura apenas) |
| prospects-novos-batch.json | Seed data (leitura apenas) |

### Atualizar o banco

```bash
cd ~/site-pixel-alchemy
NOTION_API_TOKEN='ntn_...' python3 scripts/sync_notion_csv_to_sqlite.py && \
  python3 scripts/generate_crm_data.py
```

## Prospect Pipeline (Status)

```
Lead → Contatado → Respondeu → Reuniao → Proposta → Fechado
```

| Estagio | Significado |
|---------|-------------|
| `Lead` | Identificado, sem contato ainda |
| `Contatado` | Mensagem/email/WhatsApp enviado |
| `Respondeu` | Prospect respondeu |
| `Reuniao` | Reuniao agendada/concluida |
| `Proposta` | Proposta comercial enviada |
| `Fechado` | Contrato fechado |

**Dados reais (2026-04-15)**: Lead=149, Contatado=159, Respondeu=0, Reuniao=0, Proposta=0, Fechado=0.

**Com telefone**: 279/308 (97% tem phone)
**Com email**: ~8/308 (2.6%) — **este e o bloqueio principal para outreach**

## Numeros Atuais

| Nicho | Qtd |
|-------|-----|
| Veterinaria | 71 |
| Beleza | 56 |
| Harmonizacao | 56 |
| Dentista | 53 |
| Outros | 18 |
| Pet Shop | 12 |
| Barbearia | 11 |
| Padaria | 11 |
| Pizzaria | 11 |
| Acougue | 8 |

**Total**: 308 prospects | **Com telefone**: 279 | **Com email**: ~8 (2.6%)

## Como Rodar Prospeccao

```bash
cd ~/site-pixel-alchemy

# Atualizar dados do CRM
NOTION_API_TOKEN='ntn_...' python3 scripts/sync_notion_csv_to_sqlite.py

# Ver status dos leads
python3 scripts/generate_crm_data.py

# Dashboard
# https://www.pixelalchemy.com.br/admin/dashboard/
# Senha: pixel2026
```

## Regras de Outreach

De `template-mensagem-outreach.md`:
- Max 800 caracteres
- Incluir demo URL: `https://www.pixelalchemy.com.br/site-demo/<slug>/`
- Pessoa fisica (Dr./Dra. + nome): "dele/dela", "queria"
- Empresa: "voces", "queriam"
- Healthcare (Dentista/Vet/Harmonizacao): "autoridade e sofisticacao", "pacientes"
- Beauty (Beleza/Barbearia): "estilo e profissionalismo", "clientes"
- Sem emojis

## Workflow Git (para Demo Creation)

Demos sao criados fazendo push no GitHub → Vercel faz deploy automaticamente.

```bash
git add site-demo/<slug>/
git commit -m "feat: US-XXX - Client Name - Site Completo"
git push origin main
```

**O push automatizado usa PAT.** Token esta no AUTOMATION.md.

## Regras Importantes

1. **SQLite e a fonte de verdade** — todo trabalho de automacao le e escreve no prospects.db
2. **Notion e leitura apenas** — nunca escrever diretamente no Notion via automacao
3. **Limite de email**: ~20-30/dia para evitar spam
4. **Commits**: sempre usar `feat: US-XXX - Name - action`
5. **Sem emojis** em codigo ou conteudo
6. **Demos auto-contidas**: arquivo HTML unico com CSS/JS inline
7. **Nao inventar numeros** — se nao tem dado, mostrar 0
8. **Nao fazer push de tokens** — usar variaveis de ambiente

## Subagent Template

Ao delegar para subagente, incluir:

```
Contexto:
- Prospect: {nome}, {nicho}
- Demo URL: https://www.pixelalchemy.com.br/site-demo/{slug}/
- Telefone: {telefone} (WhatsApp)
- Email: {email} (raro — 97% nao tem)
- Credenciais: ver AUTOMATION.md

Tarefa: [descricao]
```

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| Deploy falha | Verificar Vercel dashboard, fazer push para retrigger |
| Prospect nao esta no SQLite | Rodar sync_notion_csv_to_sqlite.py |
| Banco SQLite vazio | Verificar se sync rodou corretamente |
| Dashboard nao atualiza | Rodar generate_crm_data.py depois do sync |

## Stack

- Python 3 (scripts)
- SQLite (database — fonte unica)
- Mailgun API (email, 100/dia)
- Vercel API (deploy validation)
- GitHub PAT (push access)
