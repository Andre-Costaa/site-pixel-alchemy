# Checkpoint - Revisão Playwright

## Objetivo
Registrar apenas reprovações encontradas durante a revisão com Playwright dos sites do PRD original.

## Regras de uso
- Adicionar conteúdo SOMENTE quando o site não passar na revisão.
- Descrever claramente o problema, o impacto e a correção necessária.
- Se o site estiver aprovado, não registrar nada aqui.
- Revisar apenas a página do story (index.html do demo); não navegar nem validar home, termos de uso, política de privacidade ou outras páginas.

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

### REV-006 - Hikari Odontologia
- **ID da revisão**: REV-006
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Hikari Odontologia
- **URL do demo**: http://localhost:9000/index.html
- **Breakpoint(s) afetado(s)**: Todas as páginas secundárias
- **Problema**: ~~Erro JavaScript "Cannot read properties of null (reading 'addEventListener')" ocorre nas páginas de Política de Privacidade e Termos de Uso. O código em script.js:565 tenta adicionar event listeners aos botões de cookie (acceptBtn e declineBtn), mas esses elementos não existem nas páginas secundárias, causando um erro que pode afetar outras funcionalidades JavaScript.~~ ✅ **CORRIGIDO**
- **Correção aplicada**: Adicionada verificação de existência dos elementos antes de adicionar os event listeners em script.js:
  ```javascript
  if (acceptBtn && cookieConsent) {
      acceptBtn.addEventListener('click', () => { ... });
  }
  if (declineBtn && cookieConsent) {
      declineBtn.addEventListener('click', () => { ... });
  }
  ```
  Também adicionada verificação para cookieConsent antes de mostrar o banner: `if (!hasConsented && cookieConsent)`
- **Status**: ✅ Aprovado após correção. Layout validado em todos os breakpoints (1440px, 1024px, 768px, 480px). Imagens carregando corretamente. Navegação e CTAs funcionando. Console limpo de erros críticos (apenas warning de apple-touch-icon.png não crítico).

### REV-005 - Dra. Ana Carolina Orlanda Junqueira Defina
- **ID da revisão**: REV-005
- **ID do PRD original**: US-033
- **Nome do cliente**: Dra. Ana Carolina Orlanda Junqueira Defina
- **URL do demo**: /site-demo/dra-ana-carolina-orlanda/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "A Experiência que Você Merece" (problem-solution), "Tratamentos que Transformam" (services), "Depoimentos", "Diferenciais" e "Contato" estão com conteúdo invisível (opacity: 0) devido à classe CSS `animate-on-scroll`. Os elementos só ficam visíveis quando a classe `animated` é adicionada via JavaScript/Intersection Observer, mas isso não está acontecendo corretamente na carga inicial da página. Isso resulta em áreas em branco onde deveria haver conteúdo.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, adicionar uma classe `animated` por padrão no HTML ou garantir que o Intersection Observer dispare imediatamente para elementos visíveis.
- **Evidências**: Screenshots em `.playwright-mcp/dra-ana-carolina-*.png` - notar as áreas em branco nas seções intermediárias da página.

### REV-008 - Dr. Felipe Anderson Sousa Nunes
- **ID da revisão**: REV-008
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dr. Felipe Anderson Sousa Nunes
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dr-felipe-anderson-nunes/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: A seção "Por que escolher o Dr. Felipe?" (problem-solution) está completamente vazia/invisível em todos os breakpoints. Os 6 cards (3 problemas: "Dentes Amarelados", "Dor ao Sorrir", "Profissionais Impessoais" e 3 soluções: "Sorriso Brilhante", "Conforto Total", "Atendimento Humanizado") não estão sendo renderizados visualmente. Apenas o texto "VS" aparece no centro da seção. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev008-*.png` - notar as áreas em branco na seção "Por que escolher o Dr. Felipe?" onde deveriam estar os cards de problemas e soluções.

### REV-003 - Dra. Laura Sanches
- **ID da revisão**: REV-003
- **ID do PRD original**: US-043
- **Nome do cliente**: Dra. Laura Sanches
- **URL do demo**: /site-demo/dra-laura-sanches/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: A imagem do hero mostra um dentista homem, mas o site é para "Dra. Laura Sanches" (uma mulher). Isso cria uma inconsistência entre o conteúdo visual e o nome da profissional.
- **Correção sugerida**: Substituir a imagem do hero por uma foto de uma dentista mulher. Sugestão: usar uma imagem de uma profissional feminina em consultório odontológico.
- **Evidências**: Screenshot em `.playwright-mcp/dra-laura-sanches-final-1440.png` - notar que a imagem no hero mostra um homem de jaleco branco, não uma mulher.

### REV-011 - Dra. Andrea Leal
- **ID da revisão**: REV-011
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dra. Andrea Leal
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dra-andrea-leal/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Superando Desafios Odontológicos" (problem-solution), "Tratamentos Personalizados" (services), "Depoimentos", "Diferenciais" e "Contato" estão completamente vazias/invisíveis em todos os breakpoints. Os cards de desafios ("Dor e Desconforto", "Insegurança ao Sorrir", "Tratamentos Complexos"), soluções ("Alívio Imediato", "Sorriso Transformador", "Abordagem Integrada"), cards de serviços ("Implantes Dentários", "Ortodontia", "Clareamento Dental", "Facetas de Porcelana", "Restaurações Estéticas", "Periodontia"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev011-andrea-leal-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.
