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

### REV-012 - Dra. Katia Miyoshi
- **ID da revisão**: REV-012
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dra. Katia Miyoshi
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dra-katia-miyoshi/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Sua Melhor Versão" (problem-solution), "Tratamentos Especializados" (services), "Depoimentos" (testimonials), "Por Que Escolher a Dra. Katia" (features) e "Agende Sua Consulta" (contact) estão completamente vazias/invisíveis em todos os breakpoints. Os cards de problemas ("Perda de contorno facial", "Rugas e linhas de expressão", etc.), soluções ("Contorno facial definido", "Pele mais lisa", etc.), cards de serviços ("Preenchimento Facial", "Toxina Botulínica", "Harmonização Labial", "Bioestimuladores", "Fios de PDO", "Protocolos Personalizados"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev-012-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-013 - Dra. Miriam Baldin
- **ID da revisão**: REV-013
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dra. Miriam Baldin
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dra-miriam-baldin/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Por Que Escolher a Dra. Miriam" (problem-solution), "Tratamentos Especializados" (services), "Depoimentos" (testimonials), "Diferenciais" (features) e "Contato" estão completamente vazias/invisíveis em todos os breakpoints. Os cards de problemas ("Dor e Desconforto", "Sorriso Inseguro", "Tratamentos Complexos"), solução ("Solução Completa"), cards de serviços ("Clareamento Dental", "Implantes Dentários", "Ortodontia", "Facetas de Porcelana", "Restaurações Estéticas", "Limpeza e Prevenção"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente. Isso ocorre porque os elementos possuem a classe `fade-in` que define `opacity: 0`, mas a classe `visible` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `fade-in` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `visible` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `visible` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev013-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-015 - Laura Bullamah Stoll
- **ID da revisão**: REV-015
- **ID do PRD original**: US-015
- **Nome do cliente**: Laura Bullamah Stoll
- **URL do demo**: https://pixelalchemy.com.br/site-demo/laura-bullamah-stoll/index.html
- **Breakpoint(s) afetado(s)**: N/A
- **Problema**: O site não existe. A story US-015 está marcada como "passes": true e "completionNotes": "Completed by agent" no prd.json, mas o diretório 'site-demo/laura-bullamah-stoll' não foi encontrado localmente e o URL de produção retorna erro 404 (NOT_FOUND). Não é possível realizar a revisão Playwright sem o site estar disponível.
- **Correção sugerida**: Verificar se o site foi realmente criado e enviado para produção. Se não foi criado, executar a story US-015 para criar o site. Se foi criado mas não foi enviado, fazer o deploy. Se o diretório foi removido acidentalmente, restaurá-lo.
- **Evidências**:
  - Erro 404 ao acessar https://pixelalchemy.com.br/site-demo/laura-bullamah-stoll/index.html
  - Diretório /site-demo/laura-bullamah-stoll não existe localmente
  - `ls site-demo/ | grep laura` retorna apenas 'dra-laura-sanches'

### REV-016 - Dr. Ritchelle Henrique
- **ID da revisão**: REV-016
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dr. Ritchelle Henrique
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dr-ritchelle-henrique/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Por que escolher a Dra. Ritchelle" (problem-solution), "Nossos Tratamentos" (services), "Depoimentos Reais" (testimonials), "Nossos Diferenciais" (features) e "Agende Sua Consulta" (contact) estão completamente vazias/invisíveis em todos os breakpoints. Os cards de desafios ("O Desafio Diário"), soluções ("A Solução Definitiva"), cards de serviços ("Implantes Dentários", "Facetas de Porcelana", "Clareamento Dental", "Próteses Dentárias", "Ortodontia Estética", "Periodontia"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente na carga inicial da página. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer só é aplicada quando os elementos entram na viewport durante o scroll. Em uma carga inicial, todo o conteúdo abaixo da dobra fica invisível.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML. Outra opção é usar uma media query `prefers-reduced-motion` ou adicionar uma classe de fallback.
- **Evidências**: Screenshots em `.playwright-mcp/rev016-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-017 - Dr. Felipe Garcia
- **ID da revisão**: REV-017
- **ID do PRD original**: US-017
- **Nome do cliente**: Dr. Felipe Garcia
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dr-felipe-garcia/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "O Diferencial Dr. Felipe Garcia" (problem-solution), "Tratamentos Oferecidos" (services), "O Que Dizem Nossos Pacientes" (testimonials), "Por Que Nos Escolher" (features) e "Agende Sua Consulta" (contact) estão completamente vazias/invisíveis em todos os breakpoints. Os cards de desafios ("Dor e desconforto ao mastigar", "Insegurança ao sorrir", "Medo de procedimentos dolorosos", "Resultados insatisfatórios anteriores"), soluções ("Tratamentos indolores com tecnologia avançada", "Planos de tratamento personalizados", "Ambiente acolhedor e profissional", "Resultados naturais e duradouros"), cards de serviços ("Implantes Dentários", "Clareamento Dental", "Facetas de Porcelana", "Ortodontia", "Próteses Dentárias", "Clínico Geral"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/review-017-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-018 - Mônica Z. Bordoni Odontologia
- **ID da revisão**: REV-018
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Mônica Z. Bordoni Odontologia
- **URL do demo**: https://pixelalchemy.com.br/site-demo/monica-bordoni-odontologia/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Por que escolher a endodontia especializada?" (problem-solution), "Tratamentos especializados" (services), "Depoimentos" (testimonials), "Por que escolher a Dra. Mônica?" (features) e "Contato" estão completamente vazias/invisíveis em todos os breakpoints. Os cards de problemas ("O Problema": Dor intensa, Sensibilidade, Inchaço, Risco de perda), soluções ("A Solução": Tecnologia de ponta, Procedimento confortável, Recuperação rápida, Dente preservado), cards de serviços ("Tratamento de Canal", "Retratamento de Canal", "Cirurgia Peraapical", "Localização de Canal", "Obturação de Canal", "Avaliação e Diagnóstico"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev018-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-019 - Dra. Camila Zanirato
- **ID da revisão**: REV-019
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Dra. Camila Zanirato
- **URL do demo**: https://pixelalchemy.com.br/site-demo/dra-camila-zanirato/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Transforme Seu Sorriso" (problem-solution), "Nossos Serviços" (services), "O Que Dizem Nossos Pacientes" (testimonials), "Por Que Escolher a Dra. Camila?" (features) e "Agende Sua Consulta" (contact) estão completamente vazias/invisíveis em todos os breakpoints. Os cards de problemas ("Sente-se inseguro ao sorrir", "Dores de dente constantes", etc.), soluções ("Sorriso confiante e bonito", "Tratamentos sem dor", etc.), cards de serviços ("Clínico Geral", "Estética Dental", "Clareamento", "Implantes", "Ortodontia", "Próteses"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente na carga inicial da página. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev019-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-014 - Edu Gomes Odontologia
- **ID da revisão**: REV-014
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Edu Gomes Odontologia
- **URL do demo**: https://pixelalchemy.com.br/site-demo/edu-gomes-odontologia/index.html
- **Breakpoint(s) afetado(s)**: 768px, 480px
- **Problema**: As estatísticas do hero ("10+ Anos de Experiência", "5000+ Sorrisos Transformados", "100% Satisfação") estão sobrepondo o texto de descrição no hero em breakpoints menores (768px e 480px). O layout não está responsivo adequadamente, causando sobreposição entre as estatísticas e o parágrafo de descrição do serviço.
- **Correção sugerida**: Ajustar o CSS do hero para que as estatísticas se reposicionem abaixo do texto de descrição em telas menores, ou reduzir o tamanho das estatísticas, ou adicionar um `clear: both` ou `display: block` adequado para evitar a sobreposição. Verificar as media queries para breakpoints 768px e 480px.
- **Evidências**: Screenshots em `.playwright-mcp/edu-gomes-768-top.png` e `.playwright-mcp/edu-gomes-480-top.png` - notar que os números "10+", "5000+" e "100%" estão sobrepondo o texto "Clínico Geral, Implantes, Lentes Dentais, Ortodontia e Endodontia..."

### REV-020 - Carvalho Odontologia
- **ID da revisão**: REV-020
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Carvalho Odontologia
- **URL do demo**: https://pixelalchemy.com.br/site-demo/carvalho-odontologia/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Você Sabe Que Merece" (problem-solution), "Nossos Serviços" (services), "O Que Nossos Pacientes Dizem" (testimonials), "Números que Inspiram Confiança" (stats) e "Entre em Contato" (contact) estão completamente vazias/invisíveis em todos os breakpoints. Os cards de problemas ("Se Envergonha de Sorrir", "Dor e Desconforto", "Medo do Dentista", "Autoestima Baixa"), solução ("Nós Temos a Solução"), cards de serviços ("Implantes Dentários", "Estética Dental", "Ortodontia", "Próteses Dentárias", "Periodontia", "Clínica Geral"), depoimentos, estatísticas e formulário de contato não estão sendo renderizados visualmente na carga inicial da página. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/carvalho-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-022 - Grupo Orto
- **ID da revisão**: REV-022
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Grupo Orto
- **URL do demo**: https://pixelalchemy.com.br/site-demo/grupo-orto/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: As seções "Por que Escolher a Ortodontia?" (problem-solution), "Nossos Tratamentos" (services), "Depoimentos" (testimonials), "Diferenciais" (features) e "Contato" estão completamente vazias/invisíveis em todos os breakpoints. Os cards de desafios ("Dificuldade na higienização dos dentes", "Problemas de mastigação e fala", "Desgaste irregular dos dentes", "Insegurança ao sorrir"), soluções ("Sorriso harmonioso e confiante", "Melhora na saúde bucal geral", "Correta função mastigatória", "Autoestima elevada"), cards de serviços ("Aparelhos Auto-ligados", "Aparelhos Estéticos", "Alinhadores Invisíveis", "Ortodontia Preventiva", "Ortodontia para Adultos", "Manutenção e Contenção"), depoimentos, diferenciais e formulário de contato não estão sendo renderizados visualmente na carga inicial da página. Isso ocorre porque os elementos possuem a classe `animate-on-scroll` que define `opacity: 0`, mas a classe `animated` que deveria ser adicionada via Intersection Observer não está sendo aplicada corretamente na carga inicial da página.
- **Correção sugerida**: Modificar o CSS para que os elementos com `animate-on-scroll` tenham `opacity: 1` por padrão e apenas adicionem a animação quando a classe `animated` for aplicada. Alternativamente, garantir que o Intersection Observer dispare imediatamente para elementos visíveis ou adicionar a classe `animated` por padrão no HTML.
- **Evidências**: Screenshots em `.playwright-mcp/rev022-grupo-orto-*.png` - notar as grandes áreas em branco entre o hero e o footer onde deveriam estar todas as seções de conteúdo.

### REV-021 - Tooth Clinic
- **ID da revisão**: REV-021
- **ID do PRD original**: N/A (Site Pixel Alchemy - template base)
- **Nome do cliente**: Tooth Clinic
- **URL do demo**: https://pixelalchemy.com.br/site-demo/tooth-clinic/index.html
- **Breakpoint(s) afetado(s)**: Todos (1440px, 1024px, 768px, 480px)
- **Problema**: ~~A imagem do serviço "Próteses Dentais" não estava carregando (404 Not Found) devido a uma URL do Unsplash inválida. A imagem exibia o texto alternativo "Próteses" em vez da imagem do serviço.~~ ✅ **CORRIGIDO**
- **Correção aplicada**: Substituída a URL da imagem quebrada `https://images.unsplash.com/photo-1575685608721-4f75981aaa28?w=400&h=250&fit=crop` por uma URL válida `https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=400&h=250&fit=crop` no arquivo `site-demo/tooth-clinic/index.html`.
- **Status**: ✅ Aprovado após correção. Layout validado em todos os breakpoints (1440px, 1024px, 768px, 480px). Todas as seções visíveis e bem formatadas. Imagens carregando corretamente. Navegação e CTAs funcionando. Console limpo de erros críticos.
