// ========================================
// OPTIMIZATIONS.JS - UX/UI & Performance
// ========================================

// Mobile Performance Optimizer
const MobileOptimizer = {
    init() {
        this.detectDevice();
        this.optimizeForDevice();
    },

    detectDevice() {
        this.isMobile = /iPhone|iPad|Android/i.test(navigator.userAgent);
        this.isLowEnd = navigator.hardwareConcurrency <= 4;
        this.connection = navigator.connection?.effectiveType || '4g';
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    optimizeForDevice() {
        if (this.isMobile) {
            console.log('Mobile device detected - applying optimizations');

            // Reduzir animações pesadas em dispositivos low-end
            if (this.isLowEnd || this.prefersReducedMotion) {
                document.body.classList.add('reduced-motion');
                this.disableHeavyAnimations();
            }

            // Otimizar para conexão lenta
            if (this.connection === 'slow-2g' || this.connection === '2g') {
                this.enableDataSaver();
            }
        }
    },

    disableHeavyAnimations() {
        // Reduzir ou desabilitar animações pesadas
        const heavyAnimations = document.querySelectorAll('.animate-float, .animate-pulse-glow');
        heavyAnimations.forEach(el => {
            el.style.animation = 'none';
        });
    },

    enableDataSaver() {
        // Implementar modo economia de dados
        console.log('Data saver mode enabled');
    }
};

// Portfolio Filter System
const PortfolioFilter = {
    init() {
        this.filterButtons = document.querySelectorAll('.filter-btn');
        this.portfolioItems = document.querySelectorAll('.portfolio-item');

        if (this.filterButtons.length === 0) return;

        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFilter(e));
        });
    },

    handleFilter(e) {
        const filter = e.target.dataset.filter;

        // Update active button
        this.filterButtons.forEach(btn => {
            btn.classList.remove('active', 'bg-eterus-sage', 'text-eterus-charcoal');
        });
        e.target.classList.add('active', 'bg-eterus-sage', 'text-eterus-charcoal');

        // Filter items
        this.portfolioItems.forEach(item => {
            if (filter === 'all' || item.dataset.category === filter) {
                item.style.display = 'block';
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = 'translateY(0)';
                }, 10);
            } else {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    item.style.display = 'none';
                }, 300);
            }
        });
    }
};

// Scroll Reveal Animation
const ScrollReveal = {
    init() {
        this.elements = document.querySelectorAll('.section-reveal');

        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            this.elements.forEach(el => {
                this.observer.observe(el);
            });
        } else {
            // Fallback for browsers without IntersectionObserver
            this.elements.forEach(el => {
                el.classList.add('revealed');
            });
        }
    }
};

// Smooth Scroll for Anchor Links
const SmoothScroll = {
    init() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const href = anchor.getAttribute('href');
                if (href === '#') return;

                e.preventDefault();
                const target = document.querySelector(href);

                if (target) {
                    const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });

                    // Close mobile menu if open
                    const mobileMenu = document.getElementById('mobileMenu');
                    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                        mobileMenu.classList.add('hidden');
                    }
                }
            });
        });
    }
};

// Mobile Menu Toggle
const MobileMenu = {
    init() {
        this.menuBtn = document.getElementById('mobileMenuBtn');
        this.menu = document.getElementById('mobileMenu');

        if (!this.menuBtn || !this.menu) return;

        this.menuBtn.addEventListener('click', () => {
            this.menu.classList.toggle('hidden');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.menuBtn.contains(e.target) && !this.menu.contains(e.target)) {
                this.menu.classList.add('hidden');
            }
        });
    }
};

// Form Validation Enhancement
const FormEnhancement = {
    init() {
        const form = document.querySelector('#contact form');
        if (!form) return;

        const inputs = form.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            // Real-time validation
            input.addEventListener('blur', () => {
                this.validateField(input);
            });

            // Clear error on input
            input.addEventListener('input', () => {
                this.clearError(input);
            });
        });

        form.addEventListener('submit', (e) => {
            e.preventDefault();

            let isValid = true;
            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            if (isValid) {
                this.submitForm(form);
            }
        });
    },

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'Este campo é obrigatório';
        } else if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Por favor, insira um email válido';
            }
        }

        if (!isValid) {
            this.showError(field, errorMessage);
        } else {
            this.clearError(field);
        }

        return isValid;
    },

    showError(field, message) {
        field.classList.add('border-red-500');

        let errorEl = field.parentElement.querySelector('.error-message');
        if (!errorEl) {
            errorEl = document.createElement('span');
            errorEl.className = 'error-message text-red-400 text-sm mt-1 block';
            field.parentElement.appendChild(errorEl);
        }
        errorEl.textContent = message;
    },

    clearError(field) {
        field.classList.remove('border-red-500');
        const errorEl = field.parentElement.querySelector('.error-message');
        if (errorEl) {
            errorEl.remove();
        }
    },

    submitForm(form) {
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'glass-effect p-6 rounded-2xl text-center mt-8 animate-pulse-glow';
        successMessage.innerHTML = `
            <div class="text-eterus-sage text-4xl mb-4">✓</div>
            <h3 class="font-display font-bold text-xl mb-2 text-eterus-platinum">Mensagem Enviada!</h3>
            <p class="text-eterus-platinum opacity-80">Entraremos em contato em breve.</p>
        `;

        form.reset();
        form.parentElement.appendChild(successMessage);

        setTimeout(() => {
            successMessage.remove();
        }, 5000);
    }
};

// Scroll Progress Bar
const ScrollProgress = {
    init() {
        this.progressBar = document.getElementById('scrollProgress');
        if (!this.progressBar) return;

        window.addEventListener('scroll', () => {
            const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (window.scrollY / windowHeight) * 100;
            this.progressBar.style.width = scrolled + '%';
        });
    }
};

// Keyboard Navigation Enhancement
const KeyboardNavigation = {
    init() {
        // Trap focus in mobile menu when open
        const mobileMenu = document.getElementById('mobileMenu');
        if (!mobileMenu) return;

        const focusableElements = mobileMenu.querySelectorAll('a, button');
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        document.addEventListener('keydown', (e) => {
            if (mobileMenu.classList.contains('hidden')) return;

            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }

            if (e.key === 'Escape') {
                mobileMenu.classList.add('hidden');
            }
        });
    }
};

// Performance Monitor (Development Only)
const PerformanceMonitor = {
    init() {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.logPerformanceMetrics();
        }
    },

    logPerformanceMetrics() {
        if (window.performance) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                    const connectTime = perfData.responseEnd - perfData.requestStart;
                    const renderTime = perfData.domComplete - perfData.domLoading;

                    console.group('🚀 Performance Metrics');
                    console.log('Page Load Time:', pageLoadTime + 'ms');
                    console.log('Connect Time:', connectTime + 'ms');
                    console.log('Render Time:', renderTime + 'ms');
                    console.groupEnd();
                }, 0);
            });
        }
    }
};

// Initialize all modules when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    MobileOptimizer.init();
    PortfolioFilter.init();
    ScrollReveal.init();
    SmoothScroll.init();
    MobileMenu.init();
    FormEnhancement.init();
    ScrollProgress.init();
    KeyboardNavigation.init();
    PerformanceMonitor.init();

    console.log('✨ Pixel Alchemy Optimizations loaded successfully');
});

// Expose modules globally if needed
window.PixelAlchemyOptimizations = {
    MobileOptimizer,
    PortfolioFilter,
    ScrollReveal,
    SmoothScroll,
    MobileMenu,
    FormEnhancement
};
