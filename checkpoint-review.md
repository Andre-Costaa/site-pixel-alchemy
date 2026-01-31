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

### REV-005 - Dra. Ana Carolina Orlanda Junqueira Defina
- **ID da revisão**: REV-005
- **ID do PRD original**: US-033
- **Nome do cliente**: Dra. Ana Carolina Orlanda Junqueira Defina
- **URL do demo**: /site-demo/dra-ana-carolina-orlanda/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "A Experiência que Você Merece" (problem-solution), "Tratamentos que Transformam" (services), "Depoimentos", "Diferenciais" e "Contato" estão com conteúdo invisível (opacity: 0) devido à classe CSS `animate-on-scroll`. Os elementos só ficam visíveis quando a classe `animated` é adicionada via JavaScript/Intersection Observer, mas isso não está acontecendo corretamente na carga inicial da página. Isso resulta em áreas em branco onde deveria haver conteúdo.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, adicionar uma classe `animated` por padrão no HTML ou garantir que o Intersection Observer dispare imediatamente para elementos visíveis.
- **Evidências**: Screenshots em `.playwright-mcp/dra-ana-carolina-*.png` - notar as áreas em branco nas seções intermediárias da página.

### REV-003 - Dra. Laura Sanches
- **ID da revisão**: REV-003
- **ID do PRD original**: US-043
- **Nome do cliente**: Dra. Laura Sanches
- **URL do demo**: /site-demo/dra-laura-sanches/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: A imagem do hero mostra um dentista homem, mas o site é para "Dra. Laura Sanches" (uma mulher). Isso cria uma inconsistência entre o conteúdo visual e o nome da profissional.
- **Correção sugerida**: Substituir a imagem do hero por uma foto de uma dentista mulher. Sugestão: usar uma imagem de uma profissional feminina em consultório odontológico.
- **Evidências**: Screenshot em `.playwright-mcp/dra-laura-sanches-final-1440.png` - notar que a imagem no hero mostra um homem de jaleco branco, não uma mulher.

