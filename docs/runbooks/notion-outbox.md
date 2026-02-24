# Runbook: Notion Outbox (Sem MCP)

## Objetivo
Garantir atualizações confiáveis no Notion sem depender de MCP e sem “prova por log”.

O padrão é:
1. Enfileirar um evento de update (outbox)
2. Processar com worker (retry/backoff com limite)
3. Gerar receipt verificado (read-after-write)
4. Done gate valida por receipt + fetch do Notion

## Pré-requisitos
- `NOTION_TOKEN` configurado no `.env` do projeto ou no ambiente do processo.
- Os scripts Python carregam automaticamente o `.env` do root do projeto.

## Enfileirar Update
Exemplo (marcar Mensagem Pronta com campos críticos):
```bash
python3 scripts/notion_outbox_enqueue.py \
  --us-id US-090 \
  --page-id <NOTION_PAGE_ID> \
  --status "Mensagem Pronta" \
  --url-demo "https://www.pixelalchemy.com.br/site-demo/<slug>/" \
  --slug "<slug>" \
  --site-criado-em "2026-02-23" \
  --mensagem-file /tmp/mensagem.txt
```

## Enfileirar a Partir do PRD (Recomendado)
Se a story tiver `notionPageId` preenchido:
```bash
python3 scripts/notion_update_from_prd.py \
  --us-id US-090 \
  --mensagem-file /tmp/mensagem.txt \
  --site-criado-em 2026-02-23 \
  --process
```

## Processar Fila
Rodar uma vez:
```bash
python3 scripts/notion_outbox_worker.py --once
```

Rodar até esvaziar:
```bash
python3 scripts/notion_outbox_worker.py
```

## Inspecionar Estado / Reconciliação
```bash
python3 scripts/notion_sync/reconcile.py
```

## Artefatos Locais
Criados em `.notion-outbox/`:
- `queue/` eventos pendentes
- `processing/` evento em processamento
- `receipts/` receipts por idempotency_key
- `dead-letter/` falhas permanentes (após limite)
- `audit/*.jsonl` trilha append-only
- `index/us_id/US-XXX.json` atalho para done_gate
