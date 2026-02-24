# Pixel Alchemy - Learning Log

Use o script `scripts/update_global_skill_memory.py` para atualizar este arquivo com deduplicação.

## 2026-02-24
- [seed-000001] 2026-02-24 00:00:00Z | seed | Fonte única operacional definida em `prd.json`; done_gate/mark devem usar `--prd ./prd.json`.
- [seed-000002] 2026-02-24 00:00:00Z | seed | Story com requisito de Notion não pode ser concluída sem receipt em `.notion-outbox/index/us_id/US-XXX.json`.
- [f11ec1ec417f] 2026-02-24 00:12:36Z | US-OPS | Padronizar done_gate/mark_story_done/notion_update_from_prd para --prd ./prd.json elimina divergência operacional entre sessão e PRD. | evidence: Patch em scripts/config.py, done_gate.py, mark_story_done.py e notion_update_from_prd.py
- [e5c2c7a98f34] 2026-02-24 00:22:05Z | US-OPS | Prompt de criação agora exige Notion via outbox e validação done_gate/mark_story_done com --prd ./prd.json antes de concluir story. | evidence: Atualizações em prompt-modelo.md, scripts/README.md e CLAUDE.md
