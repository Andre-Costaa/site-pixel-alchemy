# Checkpoint - Revisão Playwright

## Objetivo
Registrar apenas reprovações encontradas durante a revisão com Playwright dos sites do PRD original.

## Regras de uso
- Adicionar conteúdo SOMENTE quando o site não passar na revisão.
- Descrever claramente o problema, o impacto e a correção necessária.
- Se o site estiver aprovado, não registrar nada aqui.

## Como registrar uma reprovação
Inclua uma entrada com:
- ID da revisão (REV-XXX) e ID do PRD original (US-XXX)
- Nome do cliente
- URL do demo
- Breakpoint(s) afetado(s)
- Descrição do problema
- Correção sugerida
- Evidências (ex: screenshot Playwright)

## Registros de reprovação

### REV-003 - Dra. Laura Sanches
- **ID da revisão**: REV-003
- **ID do PRD original**: US-043
- **Nome do cliente**: Dra. Laura Sanches
- **URL do demo**: /site-demo/dra-laura-sanches/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: A imagem do hero mostra um dentista homem, mas o site é para "Dra. Laura Sanches" (uma mulher). Isso cria uma inconsistência entre o conteúdo visual e o nome da profissional.
- **Correção sugerida**: Substituir a imagem do hero por uma foto de uma dentista mulher. Sugestão: usar uma imagem de uma profissional feminina em consultório odontológico.
- **Evidências**: Screenshot em `.playwright-mcp/dra-laura-sanches-final-1440.png` - notar que a imagem no hero mostra um homem de jaleco branco, não uma mulher.

