# Pixel Workflow (Fonte de Verdade)

## 1) Fonte única
- Usar Notion como fonte absoluta da verdade.
- Usar `prd.json` apenas como artefato operacional do loop `ralph-tui`.
- Executar gate/mark com `--prd ./prd.json` quando a execução estiver baseada nesse artefato.
- Tratar `tasks/prd.json` apenas como espelho legado.
- Se houver divergência entre Notion e `prd.json`, prevalece o Notion.

## 2) Conclusão de story (sem círculo)
1. Criar/ajustar site.
2. Pesquisar e registrar email no Notion:
- Priorizar `Email Responsavel` se houver evidência explícita.
- Senão usar `Email Negocio`.
- Sempre registrar `Status Email`; se não achar email confiável, usar `Nao encontrado` ou `Duvidoso`.
3. Gerar mensagem de outreach.
4. Atualizar Notion via outbox:
- Preferencial: `python3 scripts/notion_update_from_prd.py --us-id US-XXX --prd ./prd.json --mensagem-file /tmp/mensagem.txt --site-criado-em YYYY-MM-DD --process`
- Alternativa: `notion_outbox_enqueue.py` + `notion_outbox_worker.py --once`
5. Validar:
- `python3 scripts/done_gate.py --prd ./prd.json --us-id US-XXX --json`
6. Só então:
- `python3 scripts/mark_story_done.py --prd ./prd.json --us-id US-XXX`

## 3) Auditoria anti-loop
- Se `passes=true` e `notion.receipt` ausente: considerar story inválida para conclusão real.
- Se sessão `running` sem novos logs/iteração: considerar stale.
- Em sessão inconsistente, reiniciar limpo:
- `ralph-tui run --prd ./prd.json --parallel 2 --force`

## 4) Evidência mínima
- `done_gate` PASS.
- Receipt Notion em `.notion-outbox/index/us_id/US-XXX.json`.
- Commit local do artefato e push esperado pelo gate.
