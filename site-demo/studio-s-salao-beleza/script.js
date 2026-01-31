// ============================================
// STUDIO S - SALÃO DE BELEZA
// JavaScript - Interactivity
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // ============================================
    // Navigation
    // ============================================
    
    const navbar = document.getElementById('navbar');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMobileMenu = document.getElementById('closeMobileMenu');
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let lastScroll = 0;
    let scrollTimeout;
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        // Add/remove scrolled class
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Hide/show navbar on scroll
        if (currentScroll > lastScroll && currentScroll > 200) {
            navbar.classList.add('hidden-nav');
        } else {
            navbar.classList.remove('hidden-nav');
        }
        
        lastScroll = currentScroll;
        
        // Clear previous timeout
        clearTimeout(scrollTimeout);
        
        // Reset to visible after scroll stops
        scrollTimeout = setTimeout(() => {
            navbar.classList.remove('hidden-nav');
        }, 1500);
    });
    
    // Mobile menu toggle
    mobileMenuBtn.addEventListener('click', function() {
        mobileMenu.classList.add('open');
        document.body.style.overflow = 'hidden';
    });
    
    closeMobileMenu.addEventListener('click', function() {
        mobileMenu.classList.remove('open');
        document.body.style.overflow = '';
    });
    
    // Close mobile menu on link click
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileMenu.classList.remove('open');
            document.body.style.overflow = '';
        });
    });
    
    // Close mobile menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            mobileMenu.classList.remove('open');
            document.body.style.overflow = '';
        }
    });
    
    // ============================================
    // Smooth Scroll
    // ============================================
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerOffset = 80;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // ============================================
    // Scroll Animations (Intersection Observer)
    // ============================================
    
    const fadeElements = document.querySelectorAll('.fade-on-scroll');
    
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Start counters when visible
                if (entry.target.querySelector('.counter')) {
                    startCounters(entry.target);
                }
                
                fadeObserver.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    });
    
    fadeElements.forEach(el => {
        fadeObserver.observe(el);
    });
    
    // ============================================
    // Counter Animation
    // ============================================
    
    function startCounters(container) {
        const counters = container.querySelectorAll('.counter');
        
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target'));
            const duration = 2000; // 2 seconds
            const step = target / (duration / 16); // 60 FPS
            let current = 0;
            
            const updateCounter = () => {
                current += step;
                if (current < target) {
                    counter.textContent = Math.floor(current) + '+';
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target + '+';
                }
            };
            
            updateCounter();
        });
    }
    
    // ============================================
    // Parallax Effect
    // ============================================
    
    const heroSection = document.getElementById('inicio');
    const heroImage = heroSection ? heroSection.querySelector('img') : null;
    
    if (heroImage) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const parallaxSpeed = 0.3;
            const maxScroll = 300;
            
            if (scrolled < maxScroll) {
                heroImage.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
            }
        });
    }
    
    // ============================================
    // Scroll to Top Button
    // ============================================
    
    const scrollTopBtn = document.getElementById('scrollTop');
    
    if (scrollTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 500) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }
        });
        
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // ============================================
    // Service Card Hover Effects
    // ============================================
    
    const serviceCards = document.querySelectorAll('.service-card');
    
    serviceCards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
        });
    });
    
    // ============================================
    // WhatsApp Button Analytics
    // ============================================
    
    const whatsappLinks = document.querySelectorAll('a[href*="wa.me"]');
    
    whatsappLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add tracking or analytics here
            console.log('WhatsApp clicked:', this.getAttribute('href'));
            
            // You can add Google Analytics, Facebook Pixel, etc.
            // Example: gtag('event', 'click', { 'event_category': 'WhatsApp', 'event_label': 'Contact' });
        });
    });
    
    // ============================================
    // Image Lazy Loading
    // ============================================
    
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports lazy loading
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.classList.add('loaded');
        });
    } else {
        // Fallback for older browsers
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // ============================================
    // Preloader (Optional - can be enabled if needed)
    // ============================================
    
    window.addEventListener('load', function() {
        // Add any preloader removal code here
        // document.getElementById('preloader').style.display = 'none';
    });
    
    // ============================================
    // Dynamic Year in Footer
    // ============================================
    
    const yearElements = document.querySelectorAll('footer p');
    yearElements.forEach(el => {
        const currentYear = new Date().getFullYear();
        el.textContent = el.textContent.replace('2026', currentYear);
    });
    
    // ============================================
    // Form Validation (if form is added)
    // ============================================
    
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const inputs = form.querySelectorAll('input, textarea');
            let isValid = true;
            
            inputs.forEach(input => {
                if (input.required && !input.value.trim()) {
                    isValid = false;
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });
            
            if (isValid) {
                // Form submission logic here
                console.log('Form submitted successfully');
                // You can add AJAX submission here
            }
        });
    });
    
    // ============================================
    // Keyboard Navigation
    // ============================================
    
    document.addEventListener('keydown', function(e) {
        // Arrow keys for scroll
        if (e.key === 'ArrowDown') {
            window.scrollBy({ top: 300, behavior: 'smooth' });
        } else if (e.key === 'ArrowUp') {
            window.scrollBy({ top: -300, behavior: 'smooth' });
        }
    });
    
    // ============================================
    // Performance Optimization
    // ============================================
    
    // Throttle scroll events
    function throttle(callback, delay) {
        let lastCall = 0;
        return function(...args) {
            const now = new Date().getTime();
            if (now - lastCall < delay) return;
            lastCall = now;
            return callback(...args);
        };
    }
    
    // Debounce resize events
    function debounce(callback, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => callback.apply(this, args), delay);
        };
    }
    
    // Apply throttling to scroll event
    window.addEventListener('scroll', throttle(() => {
        // Throttled scroll actions
    }, 100));
    
    // Apply debouncing to resize event
    window.addEventListener('resize', debounce(() => {
        // Debounced resize actions
    }, 250));
    
    // ============================================
    // Service Workers (Optional - for PWA)
    // ============================================
    
    if ('serviceWorker' in navigator) {
        // Uncomment to register service worker
        // navigator.serviceWorker.register('/sw.js')
        //     .then(reg => console.log('Service Worker registered'))
        //     .catch(err => console.log('Service Worker registration failed', err));
    }
    
    // ============================================
    // Console Greeting
    // ============================================
    
    console.log('%c🌟 Studio S - Salão de Beleza 🌟', 'font-size: 20px; font-weight: bold; color: #14B8A6;');
    console.log('%cTransforme sua beleza com carinho e profissionalismo', 'font-size: 14px; color: #F97316;');
    console.log('%cDesenvolvido com 💜 | Powered by Pixel Alchemy', 'font-size: 12px; color: #6b7280;');
    
    // ============================================
    // Accessibility Enhancements
    // ============================================
    
    // Respect prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    if (prefersReducedMotion.matches) {
        document.documentElement.style.setProperty('--scroll-behavior', 'auto');
        document.documentElement.style.scrollBehavior = 'auto';
    }
    
    // ============================================
    // Debug Mode (Optional - remove in production)
    // ============================================
    
    // Set window.debugMode = true to enable debug messages
    window.debugMode = false;
    
    function debugLog(message, data) {
        if (window.debugMode) {
            console.log('[DEBUG]', message, data);
        }
    }
    
    debugLog('Studio S website initialized', {
        scrollY: window.pageYOffset,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight
    });
    
    // ============================================
    // End of Script
    // ============================================
});
