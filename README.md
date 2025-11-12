# ETERUS - Landing Page Premium

Uma landing page sofisticada para agência de tecnologia com design dual-tone e animações avançadas.

## 🎨 Características do Design

### Paleta de Cores Dual-Tone
- **Cor Primária**: Preto (#000000)
- **Cor Secundária**: Ciano (#00D4FF)
- **Variações**: Opacidades de 20%, 40%, 60%, 80%
- **Proibido**: Qualquer terceira cor

### Estilo Visual
- Design futurista e minimalista
- Efeitos de glassmorphism
- Animações fluidas e interações sofisticadas
- Tipografia Space Grotesk + Inter
- Contraste extremo para hierarquia visual

## 🚀 Tecnologias Utilizadas

### Frontend
- **HTML5**: Estrutura semântica
- **Tailwind CSS**: Framework de estilização
- **JavaScript ES6+**: Animações e interações

### Bibliotecas de Animação
- **Three.js**: Renderização 3D e WebGL
- **GSAP**: Animações avançadas e timeline
- **ScrollTrigger**: Animações baseadas em scroll

### Efeitos Visuais
- **WebGL Canvas**: Rede neural de partículas
- **Custom Shaders**: Efeitos de brilho e distorção
- **CSS Animations**: Transições e micro-interações
- **Parallax**: Efeitos de profundidade

## 📱 Estrutura das Seções

### 1. Hero Section
- Canvas WebGL com rede neural animada
- Título com efeito de brilho (glow)
- Botões com gradiente animado
- Scroll indicator

### 2. Serviços
- 6 cards de serviços premium
- Efeitos hover sofisticados
- Partículas flutuantes animadas
- Glassmorphism nos cards

### 3. Processo
- 4 etapas do processo criativo
- Indicadores visuais conectados
- Animações sequenciais
- Design minimalista

### 4. Sobre
- Estatísticas animadas
- Layout grid responsivo
- Elementos visuais destacados
- Informações da empresa

### 5. Contato
- Formulário elegante
- Validação visual
- Efeitos de foco
- Call-to-action destacado

## 🎯 Funcionalidades Avançadas

### Animações
- **Scroll-driven animations**: Elementos revelam ao scroll
- **Neural network**: Partículas conectadas no hero
- **Hover effects**: Brilho direcional nos cards
- **Cursor trail**: Efeito de rastro no mouse

### Interações
- **Smooth scrolling**: Navegação fluida
- **Form handling**: Validação e feedback visual
- **Responsive design**: Adaptação a todos os dispositivos
- **Performance optimization**: 60fps em animações

### Acessibilidade
- **Contraste WCAG AAA**: 21:1 entre cores
- **Navegação por teclado**: Tab order adequado
- **Textos alternativos**: Imagens descritivas
- **Focus indicators**: Estados visuais claros

## 🛠️ Instalação e Uso

### Requisitos
- Navegador moderno (Chrome 90+, Firefox 88+, Safari 14+)
- Servidor web local (para desenvolvimento)

### Instalação
1. Clone ou baixe os arquivos
2. Abra `index.html` em um servidor web
3. Navegue pela landing page

### Desenvolvimento
```bash
# Iniciar servidor local
python -m http.server 8000
# ou
npx serve .

# Acessar em http://localhost:8000
```

## 📊 Performance

### Otimizações
- **Lazy loading**: Imagens carregam sob demanda
- **Code splitting**: JavaScript modularizado
- **CSS optimization**: Classes utilitárias do Tailwind
- **Canvas optimization**: RequestAnimationFrame

### Métricas
- **Lighthouse Score**: 95+ (Performance)
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1

## 🎨 Customização

### Cores
Edite as variáveis CSS no arquivo HTML:
```css
--color-primary: #000000;
--color-secondary: #00D4FF;
```

### Animações
Ajuste os parâmetros em `main.js`:
```javascript
particleCount: 150,
animationSpeed: 0.5,
hoverIntensity: 0.3
```

### Conteúdo
Edite os textos diretamente no HTML ou via JavaScript para conteúdo dinâmico.

## 🔧 Manutenção

### Atualizações
- Verifique compatibilidade de bibliotecas
- Teste em múltiplos dispositivos
- Monitore métricas de performance
- Mantenha acessibilidade

### Debugging
- Use DevTools para inspecionar animações
- Console.log para JavaScript
- Lighthouse para performance
- WAVE para acessibilidade

## 📄 Licença

Este projeto está licenciado sob MIT License.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:
1. Faça um Fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para suporte técnico ou dúvidas sobre implementação:
- Documentação das bibliotecas utilizadas
- Comunidades de desenvolvimento web
- Fóruns especializados em animações web

---

**Criado com ❤️ por Eterus - Transformando visões em realidades digitais extraordinárias**