/**
 * CR Beauty Lounge - JavaScript
 * Funcionalidades: Navbar scroll, Mobile menu, Smooth scroll, Animações, WhatsApp
 */

(function () {
  'use strict';

  // ============================================
  // DOM ELEMENTS
  // ============================================
  const navbar = document.querySelector('.navbar');
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navLinkItems = document.querySelectorAll('.nav-links a');
  const whatsappButton = document.querySelector('.whatsapp-button');

  // ============================================
  // 1. NAVBAR SCROLL EFFECT
  // ============================================
  function handleNavbarScroll() {
    if (!navbar) return;

    const scrollY = window.scrollY || window.pageYOffset;
    const triggerPoint = 100;

    if (scrollY > triggerPoint) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  // ============================================
  // 2. MOBILE MENU TOGGLE
  // ============================================
  function toggleMobileMenu() {
    if (!menuToggle || !navLinks) return;

    menuToggle.classList.toggle('active');
    navLinks.classList.toggle('active');
    document.body.classList.toggle('menu-open');
  }

  function closeMobileMenu() {
    if (!menuToggle || !navLinks) return;

    menuToggle.classList.remove('active');
    navLinks.classList.remove('active');
    document.body.classList.remove('menu-open');
  }

  // ============================================
  // 3. SMOOTH SCROLL PARA ANCHOR LINKS
  // ============================================
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');

        // Ignora links vazios ou apenas #
        if (targetId === '#' || !targetId) return;

        const targetElement = document.querySelector(targetId);

        if (targetElement) {
          e.preventDefault();

          // Fecha menu mobile se estiver aberto
          closeMobileMenu();

          // Calcula offset considerando a navbar fixa
          const navbarHeight = navbar ? navbar.offsetHeight : 0;
          const targetPosition = targetElement.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;

          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // ============================================
  // 4. INTERSECTION OBSERVER - ANIMAÇÕES AO SCROLL
  // ============================================
  function initScrollAnimations() {
    const animatedElements = document.querySelectorAll(
      '.service-card, .benefit-item, .testimonial-card, .step-item, .price-card, .gallery-item'
    );

    if (!('IntersectionObserver' in window)) {
      // Fallback para navegadores sem suporte
      animatedElements.forEach(el => el.classList.add('animate'));
      return;
    }

    const observerOptions = {
      root: null,
      rootMargin: '0px 0px -50px 0px',
      threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Adiciona delay escalonado para elementos múltiplos
          const delay = index % 3 * 100;
          setTimeout(() => {
            entry.target.classList.add('animate');
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }, delay);

          // Desconecta após animar uma vez
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    animatedElements.forEach((el, index) => {
      // Prepara estado inicial
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px)';
      el.style.transition = `opacity 0.6s ease ${index % 3 * 0.1}s, transform 0.6s ease ${index % 3 * 0.1}s`;
      observer.observe(el);
    });
  }

  // ============================================
  // 5. BOTÃO WHATSAPP FIXO - COMPORTAMENTO
  // ============================================
  function initWhatsAppButton() {
    if (!whatsappButton) return;

    // Mostra botão após scroll de 300px
    function toggleWhatsAppButton() {
      const scrollY = window.scrollY || window.pageYOffset;

      if (scrollY > 300) {
        whatsappButton.classList.add('visible');
      } else {
        whatsappButton.classList.remove('visible');
      }
    }

    // Efeito de pulso ao carregar a página
    setTimeout(() => {
      whatsappButton.classList.add('pulse');
    }, 2000);

    // Remove pulso após interação
    whatsappButton.addEventListener('mouseenter', () => {
      whatsappButton.classList.remove('pulse');
    });

    whatsappButton.addEventListener('click', (e) => {
      // Tracking opcional (descomente se usar Google Analytics)
      // if (typeof gtag !== 'undefined') {
      //   gtag('event', 'click', { event_category: 'WhatsApp', event_label: 'Botão Flutuante' });
      // }

      console.log('WhatsApp button clicked');
    });

    window.addEventListener('scroll', toggleWhatsAppButton, { passive: true });
    toggleWhatsAppButton(); // Verifica estado inicial
  }

  // ============================================
  // UTILITÁRIOS
  // ============================================

  // Debounce para otimizar eventos de scroll
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Fecha menu ao clicar fora
  function handleClickOutside(e) {
    if (!menuToggle || !navLinks) return;

    if (!menuToggle.contains(e.target) && !navLinks.contains(e.target)) {
      closeMobileMenu();
    }
  }

  // Fecha menu ao pressionar Escape
  function handleEscapeKey(e) {
    if (e.key === 'Escape') {
      closeMobileMenu();
    }
  }

  // ============================================
  // INICIALIZAÇÃO
  // ============================================
  function init() {
    // Event Listeners
    if (menuToggle) {
      menuToggle.addEventListener('click', toggleMobileMenu);
    }

    // Fecha menu ao clicar em um link
    navLinkItems.forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });

    // Scroll events (com debounce)
    window.addEventListener('scroll', debounce(handleNavbarScroll, 10), { passive: true });

    // Click outside
    document.addEventListener('click', handleClickOutside);

    // Teclado
    document.addEventListener('keydown', handleEscapeKey);

    // Inicializa funcionalidades
    handleNavbarScroll();
    initSmoothScroll();
    initScrollAnimations();
    initWhatsAppButton();
  }

  // Aguarda DOM carregar
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Preloader simples (opcional)
  window.addEventListener('load', () => {
    document.body.classList.add('loaded');
  });

})();
