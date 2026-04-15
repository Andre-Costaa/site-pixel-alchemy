# PROSPECTION.md — Pixel Alchemy

## Quando Ler Este Documento

- Quando quiser entender o fluxo de prospeccao completo
- Quando quiser descobrir novos leads
- Quando quiser fazer outreach em escala

**Leia primeiro:** `AGENTS.md` (pipeline canonico) e `AUTOMATION.md` (scripts e cron).

---

## Estrategia: Clientes SEM Site = Ideal

A estrategia inverte a lgica habitual:

- **Cliente IDEAL**: negocio SEM site ou com site ruim
- **Ferramenta**: SERP Google Maps para encontrar esses negocios
- **Scoring**: negocios com alta nota = sem site + tem telefone + rating bom
- **Canal primario**: WhatsApp (97% dos prospects tem telefone)

| Score | Criterio |
|-------|----------|
| +50 | SEM site (nosso cliente ideal) |
| +20 | Tem telefone (pode WhatsApp) |
| +15-20 | Rating 4.0+ |
| +5-15 | Reviews 50+ |

---

## Pipeline Canonico

```
Lead → Contatado → Respondeu → Reuniao → Proposta → Fechado
```

| Estagio | Significado |
|---------|-------------|
| `Lead` | Prospect identificado, nao contactado |
| `Contatado` | WhatsApp/email enviado |
| `Respondeu` | Prospect respondeu |
| `Reuniao` | Reuniao agendada/concluida |
| `Proposta` | Proposta enviada |
| `Fechado` | Venda fechada |

---

## Fluxo Completo de Prospeccao

```
┌──────────────────────────────────────────────────────────────┐
│                    PROSPECTION PIPELINE                       │
│                                                               │
│  1. DISCOVERY        SERP Maps → negocios sem site          │
│  2. EMAIL FIND       Google search → extrair email do site   │
│  3. SCORING          Score = sem_site(50) + telefone(20)    │
│  4. INSERT           SQLite (dedup por telefone + nome)        │
│  5. OUTREACH         WhatsApp (link direto) ou email         │
│  6. UPDATE           SQLite pipeline_status                   │
│  7. NOTION           Outbox pattern (opcional)                │
│  8. REPORT           Telegram para Andre                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Scripts Disponiveis

| Script | Funcao | Status |
|--------|--------|--------|
| `lead_discovery_maps.py` | Discovery via SERP Maps (clientes SEM site) | OPERACIONAL |
| `email_discovery.py` | Extrair emails de sites descobertos | OPERACIONAL |
| `sync_notion_csv_to_sqlite.py` | Sincroniza Notion + CSV para SQLite | OPERACIONAL |
| `generate_crm_data.py` | Gera dashboard-data.json | OPERACIONAL |
| `message_generator.py` | Gera mensagem outreach | OPERACIONAL |
| `notion_outbox_enqueue.py` | Bota update Notion em fila | OPERACIONAL |
| `notion_outbox_worker.py` | Consome fila e atualiza Notion | OPERACIONAL |

---

## Como Rodar — Passo a Passo

### 1. Discovery de Leads (SERP Maps)

```bash
cd ~/site-pixel-alchemy
source .env 2>/dev/null || cp .env.example .env

# Discovery de um nicho especifico
SERP_API_KEY="$SERP_API_KEY" python3 scripts/lead_discovery_maps.py \
  --niche "Veterinaria" --city "Ribeirao Preto" --limit 30

# Discovery de TODOS os nichos (9 nichos, 30 cada)
for nicho in "Veterinaria" "Clínica de Harmonizacao" "Dentista" "Clínica de Beleza" \
             "Pet Shop" "Barbearia" "Padaria" "Pizzaria" "Acougue"; do
  SERP_API_KEY="$SERP_API_KEY" python3 scripts/lead_discovery_maps.py \
    --niche "$nicho" --limit 30
  sleep 10
done
```

### 2. Encontrar Emails

```bash
# Para prospects descobertos (sem email)
SERP_API_KEY="$SERP_API_KEY" python3 scripts/email_discovery.py --limit 50
```

### 3. Refresh Dashboard

```bash
python3 scripts/generate_crm_data.py
```

### 4. Verificar no Dashboard

```
https://www.pixelalchemy.com.br/admin/dashboard/
Senha: pixel2026
```

---

## Cron — Execucao Diaria Real

Adicionar ao crontab (`crontab -e`):

```crontab
# Discovery: Seg-Sex 9h BRT (12h UTC)
0 12 * * 1-5 cd /opt/data/home/site-pixel-alchemy && \
  SERP_API_KEY="$SERP_API_KEY" \
  python3 scripts/lead_discovery_maps.py --niche "Veterinaria" --limit 20 \
  >> /var/log/pixel-alchemy/discovery.log 2>&1

# Sync: Seg-Sex 9h30 BRT
30 12 * * 1-5 cd /opt/data/home/site-pixel-alchemy && \
  NOTION_API_TOKEN="$NOTION_API_TOKEN" \
  python3 scripts/sync_notion_csv_to_sqlite.py \
  >> /var/log/pixel-alchemy/sync.log 2>&1

# Dashboard: Seg-Sex 10h BRT
0 13 * * 1-5 cd /opt/data/home/site-pixel-alchemy && \
  python3 scripts/generate_crm_data.py \
  >> /var/log/pixel-alchemy/dashboard.log 2>&1

# Email discovery: Seg 8h BRT
0 11 * * 1 cd /opt/data/home/site-pixel-alchemy && \
  SERP_API_KEY="$SERP_API_KEY" \
  python3 scripts/email_discovery.py --limit 50 \
  >> /var/log/pixel-alchemy/email_discovery.log 2>&1
```

Criar log directory:
```bash
sudo mkdir -p /var/log/pixel-alchemy
sudo chown $USER /var/log/pixel-alchemy
```

---

## Limites Diarios

| Canal | Limite | Risco |
|-------|--------|-------|
| WhatsApp | ~50/hora | Ban temporario se exceder |
| Email (Gmail) | 20-30/dia | Spam se exceder |
| SERP Maps | ~1 credit/busca | 50k credits = ~50k searches |

---

## Quando Andre Recebe Resposta

1. Verificar email/WhatsApp
2. Atualizar pipeline em SQLite:
```sql
UPDATE prospects SET pipeline_status='Respondeu' WHERE id=?;
UPDATE prospects SET resposta='texto da resposta' WHERE id=?;
```
3. Se deal fechado: `pipeline_status='Fechado'`

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| SERP 402/429 | Credits esgotados — verificar em serper.dev |
| Prospect duplicado | Telefone ja existe no banco (dedup automatico) |
| SEM email encontrado | Normal — 97% nao tem. Usar WhatsApp como canal. |
| Script erro de token | Verificar `.env` existe e tokens estao preenchidos |
| WhatsApp ban | Pausar 24h, reduzir limite para 30/hora |
