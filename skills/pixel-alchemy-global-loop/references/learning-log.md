# Pixel Alchemy - Learning Log

Use o script `scripts/update_global_skill_memory.py` para atualizar este arquivo com deduplicação.

## 2026-02-24
- [seed-000001] 2026-02-24 00:00:00Z | seed | Fonte única operacional definida em `prd.json`; done_gate/mark devem usar `--prd ./prd.json`.
- [seed-000002] 2026-02-24 00:00:00Z | seed | Story com requisito de Notion não pode ser concluída sem receipt em `.notion-outbox/index/us_id/US-XXX.json`.
- [f11ec1ec417f] 2026-02-24 00:12:36Z | US-OPS | Padronizar done_gate/mark_story_done/notion_update_from_prd para --prd ./prd.json elimina divergência operacional entre sessão e PRD. | evidence: Patch em scripts/config.py, done_gate.py, mark_story_done.py e notion_update_from_prd.py
- [e5c2c7a98f34] 2026-02-24 00:22:05Z | US-OPS | Prompt de criação agora exige Notion via outbox e validação done_gate/mark_story_done com --prd ./prd.json antes de concluir story. | evidence: Atualizações em prompt-modelo.md, scripts/README.md e CLAUDE.md
- [notion-canonical-20260318] 2026-03-18 00:00:00Z | US-OPS | Notion passa a ser documentado como fonte absoluta da verdade; `prd.json` vira artefato operacional do loop e pesquisa de email entra como etapa padrão não bloqueante com `Status Email`. | evidence: Atualizações em AGENTS.md, NOTION-FIELDS-REFERENCE.md, CLAUDE.md, scripts/site_orchestrator.py e scripts/notion_update_from_prd.py

## 2026-03-18
- [7edc8db7e20b] 2026-03-18 16:11:56Z | US-OPS | Notion e a fonte absoluta da verdade; prd.json e artefato operacional do ralph-tui, e a pesquisa de email deve registrar Status Email sem bloquear a entrega. | evidence: Atualizacoes em AGENTS.md, NOTION-FIELDS-REFERENCE.md, CLAUDE.md, scripts/site_orchestrator.py, scripts/notion_update_from_prd.py e skill pixel-alchemy-global-loop
