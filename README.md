# Pixel Alchemy - Site Institucional

Site premium desenvolvido com design **Organic/Blobmorphism**, criando uma experiência visual sofisticada e moderna para a Pixel Alchemy.

## Características do Design

### Estética Organic Blobmorphism

- **Formas Orgânicas**: Blobs fluidos e assimétricos inspirados na natureza
- **Animações Suaves**: Movimentos respiratórios e transições naturais
- **Profundidade Visual**: Camadas sobrepostas com blur e transparência
- **Design Responsivo**: Otimizado para todos os dispositivos (desktop, tablet, mobile)

### Paleta de Cores

Tons terrosos modernos que transmitem sofisticação e confiança:

- **Charcoal** (#1a1f2e): Base escura e profissional
- **Cream** (#faf8f4): Fundo claro e acolhedor
- **Terracotta** (#e07856): Acento principal vibrante
- **Sage** (#8ba888): Verde natural e calmo
- **Lavender** (#b5a6c8): Toque de sofisticação
- **Clay** (#c4a68a): Terra neutro e quente

### Tipografia

- **Display**: Bricolage Grotesque (cabeçalhos)
- **Body**: Plus Jakarta Sans (texto corrido)

## Estrutura do Site

### Seções Incluídas

1. **Hero Section**
   - Título impactante com gradiente
   - CTAs otimizados para conversão
   - Cards flutuantes animados
   - Blobs animados em background

2. **Services** (6 serviços)
   - Identidade Visual
   - Web Design Premium
   - Aplicações Mobile
   - E-commerce Elite
   - Consultoria Digital
   - Manutenção Premium

3. **Process** (4 etapas)
   - Descoberta e Estratégia
   - Design e Prototipagem
   - Desenvolvimento e Testes
   - Lançamento e Crescimento

4. **About**
   - Estatísticas animadas (contador numérico)
   - História da empresa
   - Valores principais

5. **Testimonials**
   - 3 depoimentos de clientes
   - Avaliações com estrelas
   - Design em card com blobs

6. **FAQ**
   - Accordion interativo
   - 6 perguntas frequentes

7. **Contact**
   - Formulário de contato completo
   - Informações de contato
   - Links sociais

8. **Footer**
   - Navegação completa
   - Links úteis
   - Informações legais

## Funcionalidades Técnicas

### Animações e Interações

- **WoW Animations**: Elementos aparecem ao scroll com fade-up
- **Blob Floating**: Animação contínua dos blobs em background
- **Parallax Sutil**: Movimentação diferenciada dos elementos ao scroll
- **Contador Animado**: Números da seção About animam ao aparecer
- **Tilt Effect**: Cards de serviços respondem ao movimento do mouse
- **Ripple Effect**: Efeito de onda nos botões ao hover
- **FAQ Accordion**: Expansão suave das respostas
- **Auto-hide Navigation**: Menu some ao scroll down, aparece ao scroll up
- **Mobile Menu**: Hamburger menu responsivo

### Otimizações

- **Performance**:
  - CSS otimizado com variáveis
  - Animações usando GPU (transform, opacity)
  - Intersection Observer para animações lazy
  - Throttling em eventos de scroll

- **Acessibilidade**:
  - Suporte a `prefers-reduced-motion`
  - ARIA labels em elementos interativos
  - Contraste adequado de cores
  - Navegação via teclado

- **SEO**:
  - Meta tags otimizadas
  - Estrutura semântica HTML5
  - Heading hierarchy correta
  - Alt texts preparados (adicionar conforme necessário)

- **Mobile-First**:
  - Design responsivo em todas as seções
  - Breakpoints: 1024px, 768px, 480px
  - Touch-friendly (botões e áreas clicáveis adequadas)
  - Menu mobile otimizado

### CRO (Conversion Rate Optimization)

- **CTAs Estratégicos**:
  - Botões primários em destaque
  - Cores contrastantes
  - Textos orientados a ação
  - Hierarquia visual clara

- **Formulário de Contato**:
  - Campos otimizados
  - Validação nativa HTML5
  - Feedback visual ao usuário
  - Design não-intimidador

- **Social Proof**:
  - Depoimentos com avaliações
  - Estatísticas de sucesso
  - Logos/avatares de clientes

## Como Usar

### Instalação

1. Clone ou baixe os arquivos
2. Abra `index.html` em um navegador moderno
3. Não requer build ou compilação

### Personalização

#### Alterar Cores

Edite as variáveis CSS em `styles.css`:

```css
:root {
    --color-charcoal: #1a1f2e;
    --color-cream: #faf8f4;
    --color-terracotta: #e07856;
    /* ... */
}
```

#### Modificar Conteúdo

Todo o conteúdo está em `index.html` de forma clara e organizada por seções.

#### Configurar Formulário

No arquivo `script.js`, localize a seção "Form Handling" e configure o endpoint do seu backend:

```javascript
contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    // Adicione aqui a integração com seu backend
});
```

### Integração de Analytics

Configure o tracking de eventos na seção "Analytics Event Tracking" do `script.js`:

```javascript
function trackEvent(category, action, label) {
    // Adicione Google Analytics, Mixpanel, etc.
}
```

## Tecnologias Utilizadas

- **HTML5**: Estrutura semântica
- **CSS3**: Estilização avançada com variáveis, gradientes, animações
- **JavaScript Vanilla**: Sem dependências externas
- **Google Fonts**: Bricolage Grotesque e Plus Jakarta Sans

## Compatibilidade

- Chrome/Edge (versões recentes)
- Firefox (versões recentes)
- Safari (versões recentes)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Próximos Passos Recomendados

1. **Adicionar Imagens Reais**:
   - Logo da empresa
   - Fotos de projetos
   - Fotos de equipe
   - Imagens de clientes (para testimonials)

2. **Integrar Backend**:
   - API para formulário de contato
   - Sistema de newsletter
   - CMS para gestão de conteúdo

3. **Analytics e Tracking**:
   - Google Analytics 4
   - Hotjar/Clarity para heatmaps
   - Facebook Pixel

4. **Performance Adicional**:
   - Minificar CSS/JS para produção
   - Otimizar e comprimir imagens
   - Implementar CDN
   - Service Worker para PWA

5. **SEO Avançado**:
   - Schema.org markup
   - Open Graph tags
   - Sitemap XML
   - robots.txt

## Licença

Projeto desenvolvido para Pixel Alchemy - Todos os direitos reservados.

---

**Desenvolvido com paixão e atenção aos detalhes** 🎨
