---
name: pixel-alchemy-global-loop
description: Operar o fluxo Pixel Alchemy com Notion como fonte absoluta da verdade, execução ralph-tui via artefatos operacionais como `prd.json`, validação done_gate e atualização obrigatória de Notion via outbox com receipt verificável. Usar ao criar/revisar stories US-XXX, auditar divergências de progresso, evitar loops sem evidência e registrar/sincronizar aprendizados globais para Codex, Claude Code e FactoryAI Droid.
---

# Pixel Alchemy Global Loop

## Workflow Obrigatório

1. Confirmar fonte da verdade:
- Notion é a fonte absoluta da verdade para prospecto, pipeline, identificadores e estado de entrega
- `prd.json` é apenas artefato operacional de execução em massa
- Rodar gate/mark sempre com `--prd ./prd.json` quando o loop estiver usando esse artefato
- Se houver divergência entre Notion e `prd.json`, prevalece o Notion

2. Validar conclusão de story por evidência:
- Se a story exigir Notion, atualizar via outbox (nunca update MCP direto de produção)
- Pesquisar e registrar email no Notion quando o schema existir:
  - `Email Responsavel` se houver evidência explícita
  - senão `Email Negocio`
  - sempre registrar `Status Email`; se não achar, usar `Nao encontrado` ou `Duvidoso`
- Rodar `python3 scripts/done_gate.py --prd ./prd.json --us-id US-XXX --json`
- Somente após `PASS`, rodar `python3 scripts/mark_story_done.py --prd ./prd.json --us-id US-XXX`

3. Auditar saúde do loop:
- Verificar `.ralph-tui/session.json`, `.ralph-tui/heartbeat/heartbeat.jsonl`, `.notion-outbox/`
- Se houver sessão stale/inconsistente, preferir novo `ralph-tui run --prd ./prd.json --parallel 2 --force`

## Atualização Global de Aprendizados

Sempre que este skill for usado, registrar pelo menos 1 aprendizado novo (ou consolidado) e sincronizar globalmente:

```bash
python3 scripts/update_global_skill_memory.py \
  --learning "Aprendizado objetivo" \
  --us-id US-XXX \
  --evidence "Comando/log/artefato que comprovou"
```

Esse comando:
- adiciona entrada em `references/learning-log.md` (com deduplicação por hash)
- sincroniza o skill para:
- `~/.codex/skills/pixel-alchemy-global-loop`
- `~/.claude/skills/pixel-alchemy-global-loop`
- `~/.factory/skills/pixel-alchemy-global-loop`
- `~/.agents/skills/pixel-alchemy-global-loop`

## Referências

- Workflow completo: `references/pixel-workflow.md`
- Log contínuo de aprendizados: `references/learning-log.md`
- Script de sync e memória: `scripts/update_global_skill_memory.py`
