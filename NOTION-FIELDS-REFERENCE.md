# Notion CRM - Referência Rápida de Campos

**Database**: "Controle" (`2f76f51e-b8a5-8088-a52c-db29fc3c1f81`)
**Data Source**: `collection://2f76f51e-b8a5-800b-8c7e-000bf9f86798`

## ⚠️ CRITICAL: Campos Obrigatórios Após Criar Site

Quando você terminar de criar um site para um cliente, você **DEVE** atualizar estes campos no Notion:

| Campo | Tipo | Valor Exato | Exemplo |
|---|---|---|---|
| **Status** | select | `"Mensagem Pronta"` | Exatamente este valor, NÃO "Site Pronto" |
| **URL Demo** | url | `https://www.pixelalchemy.com.br/site-demo/<slug>/` | `https://www.pixelalchemy.com.br/site-demo/dra-laura-sanches/` |
| **Mensagem** | text | Mensagem personalizada gerada | Ver `template-mensagem-outreach.md` |
| **Slug** | text | Slug da pasta site-demo | `dra-laura-sanches` |
| **US ID** | text | ID da user story | `US-090` |
| **Site Criado Em** | date | Data de hoje (YYYY-MM-DD) | `2026-02-22` |

## 🔍 Schema Completo do Database

### Campos de Identificação

- **Nome** (title) — Nome do cliente/negócio
- **ID** (text) — Identificador interno
- **Nicho** (select) — `Dentista`, `Veterinária`, `Harmonização`, `Beleza`, `Pizzaria`, `Barbearia`, `Padaria`, `Açougue`, `Pet Shop`

### Campos de Contato

- **Telefone** (text) — Com DDD: `(16) 99876-5432`
- **Endereço** (text) — Endereço completo
- **Instagram** (text) — Handle ou URL
- **Facebook** (text) — URL da página
- **Site** (text) — Website existente (se houver)

### Campos de Pipeline

- **Status** (select) — Ver seção "Pipeline de Status" abaixo
- **Aprovado** (select) — `Aprovado`, `Reprovado`, `Pendente`
- **Venda** (select) — `Sim`, `Não`, `Em negociação`
- **Valor** (number) — Valor em R$

### Campos de Outreach

- **Mensagem** (text) — **CAMPO CRÍTICO**: Mensagem personalizada gerada após criar o site
- **Resposta** (text) — Resposta do prospecto
- **Observações** (text) — Notas internas

### Campos Técnicos (Site)

- **URL Demo** (url) — **CAMPO CRÍTICO**: Link completo do site demo
- **Slug** (text) — **CAMPO CRÍTICO**: Slug usado na URL (sem espaços, lowercase)
- **US ID** (text) — **CAMPO CRÍTICO**: ID da user story no prd.json
- **Site Criado Em** (date) — **CAMPO CRÍTICO**: Data de criação do site
- **Descrição** (text) — Descrição do negócio (usado na criação do site)

### Campos de Tracking

- **Origem** (select) — `Dentistas`, `Veterinária`, `harmonizacao`, `Pesquisa`, `Notion (Beleza)`
- **Data 1º Contato** (date) — Data do primeiro contato
- **Data Follow-up** (date) — Data do follow-up
- **Horário** (date) — Horário agendado

## 📊 Pipeline de Status

```
Lead → Qualificado → Site em Criação → Mensagem Pronta → Enviado → Respondeu → Reunião → Proposta → Fechado/Perdido/Descartado
```

**Descrição de cada status**:

| Status | Significado |
|---|---|
| **Lead** | Prospecto identificado, dados iniciais coletados |
| **Qualificado** | Prospecto aprovado para criação de site |
| **Site em Criação** | User story gerada, agente está criando o site |
| **Mensagem Pronta** | ✅ **Site criado + mensagem gerada + Notion atualizado** (PRONTO PARA ENVIAR) |
| **Enviado** | Mensagem de outreach enviada via WhatsApp/Instagram |
| **Respondeu** | Prospecto respondeu ao outreach |
| **Reunião** | Reunião agendada ou realizada |
| **Proposta** | Proposta comercial enviada |
| **Fechado** | Venda fechada (verificar `Venda = Sim`) |
| **Perdido** | Prospecto recusou ou não respondeu |
| **Descartado** | Prospecto desqualificado |

## 🔧 Como Atualizar o Notion (Python)

### Usar a Função Helper (Recomendado)

```python
from scripts.notion_client import build_site_ready_update

# Para pessoa física (Dra./Dr.)
update = build_site_ready_update(
    page_id="2f76f51e-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
    slug="dra-laura-sanches",
    us_id="US-090",
    url_demo="https://www.pixelalchemy.com.br/site-demo/dra-laura-sanches/",
    site_created_date="2026-02-22",
    mensagem="""[mensagem personalizada gerada]"""
)

# Execute via MCP
# notion-update-page com os parâmetros retornados
```

### Campos Atualizados Automaticamente

A função `build_site_ready_update()` atualiza:

1. ✅ `Status` → `"Mensagem Pronta"`
2. ✅ `URL Demo` → URL completa do site
3. ✅ `Mensagem` → Mensagem de outreach personalizada
4. ✅ `Slug` → Slug da pasta
5. ✅ `US ID` → ID da user story
6. ✅ `Site Criado Em` → Data de criação (formato `YYYY-MM-DD`, `is_datetime: 0`)

## ❌ Erros Comuns a Evitar

### ❌ Status Errado
```python
# ERRADO
"Status": "Site Pronto"  # ❌ Este status não existe no pipeline

# CORRETO
"Status": "Mensagem Pronta"  # ✅ Status correto após criar site
```

### ❌ URL Demo Incompleta
```python
# ERRADO
"URL Demo": "/site-demo/dra-laura-sanches/"  # ❌ Faltando domínio

# CORRETO
"URL Demo": "https://www.pixelalchemy.com.br/site-demo/dra-laura-sanches/"  # ✅
```

### ❌ Data com Formato Errado
```python
# ERRADO
"Site Criado Em": "22/02/2026"  # ❌ Formato brasileiro
"date:Site Criado Em:start": "2026-02-22T00:00:00"  # ❌ Com timestamp

# CORRETO
"date:Site Criado Em:start": "2026-02-22"  # ✅ YYYY-MM-DD
"date:Site Criado Em:is_datetime": 0  # ✅ Marcar como date-only
```

### ❌ Slug com Caracteres Inválidos
```python
# ERRADO
"Slug": "Dra. Laura Sanches"  # ❌ Espaços e pontos
"Slug": "dra_laura_sanches"  # ❌ Underscores (use hífens)

# CORRETO
"Slug": "dra-laura-sanches"  # ✅ Lowercase, hífens, sem acentos
```

### ❌ Mensagem Não Personalizada
```python
# ERRADO - Mensagem genérica
mensagem = "Olá, criamos um site para você. Veja em [URL]"  # ❌

# CORRETO - Mensagem personalizada
mensagem = """Olá! Tudo bem? Sou o André, fundador da Pixel Alchemy.

Estávamos analisando a presença digital do consultório da Dra. Laura Sanches e percebemos que ela ainda não tem um website. Tomamos a liberdade de rascunhar um layout demo:

https://www.pixelalchemy.com.br/site-demo/dra-laura-sanches/

O objetivo foi criar uma experiência que transmita mais autoridade e sofisticação aos seus pacientes..."""
```

## 📝 Checklist Antes de Marcar como Completo

Antes de considerar uma user story concluída:

- [ ] Site criado em `site-demo/<slug>/index.html`
- [ ] Mensagem gerada seguindo `template-mensagem-outreach.md`
- [ ] Pronomes corretos (pessoa física vs empresa)
- [ ] Tom apropriado ao nicho
- [ ] **Status** = `"Mensagem Pronta"` (exato)
- [ ] **URL Demo** = URL completa com `https://`
- [ ] **Mensagem** = texto completo da mensagem personalizada
- [ ] **Slug** = slug lowercase com hífens
- [ ] **US ID** = ID correto da user story
- [ ] **Site Criado Em** = data no formato `YYYY-MM-DD`
- [ ] Commit criado e push realizado

## 🚨 Se o Agente Falhar

Se o agente não conseguir atualizar o Notion:

1. **Verificar page_id**: Certifique-se de ter o UUID correto do prospecto
2. **Verificar campos obrigatórios**: Todos os 6 campos críticos devem estar presentes
3. **Verificar formato de data**: Deve ser `YYYY-MM-DD` com `is_datetime: 0`
4. **Verificar Status**: Deve ser exatamente `"Mensagem Pronta"`
5. **Ver logs**: Checar mensagens de erro do MCP Notion

## 📚 Referências

- `CLAUDE.md` — Instruções completas do projeto
- `scripts/README.md` — Documentação do workflow de automação
- `scripts/notion_client.py` — Funções helper para Notion
- `template-mensagem-outreach.md` — Template de mensagens por nicho
