# Runbook: Done Gate (Sem Log)

## Objetivo
Bloquear `passes=true` sem evidência objetiva:
- artefato existe
- commit real do artefato existe e referencia a US
- commit está em `origin/main` (opcional)
- Notion update comprovado por receipt + read-after-write (quando aplicável)

## Execução
```bash
python3 scripts/done_gate.py --us-id US-090
```

JSON:
```bash
python3 scripts/done_gate.py --us-id US-090 --json
```

Ignorar verificação de `origin/main`:
```bash
python3 scripts/done_gate.py --us-id US-090 --no-require-origin-main
```

## Notion
Quando a story exige “Atualizar Notion”, o done gate:
1. exige `NOTION_TOKEN`
2. exige receipt em `.notion-outbox/index/us_id/US-XXX.json`
3. faz fetch no Notion e compara com `expected_properties` do receipt

