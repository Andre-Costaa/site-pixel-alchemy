/**
 * Studio Gui Poncciano - Beauty Salon
 * Main JavaScript File
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavbar();
    initMobileMenu();
    initScrollReveal();
    initCounters();
    initSmoothScroll();
    initParallax();
    initBackToTop();
    initGallery();
});

/**
 * Navbar scroll effect
 */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    let lastScroll = 0;

    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        // Add scrolled class when scroll > 50px
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Hide/show navbar on scroll direction (optional)
        if (currentScroll > lastScroll && currentScroll > 200) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }

        lastScroll = currentScroll;
    });

    // Smooth transition for navbar
    navbar.style.transition = 'transform 0.3s ease, background-color 0.3s ease';
}

/**
 * Mobile menu toggle
 */
function initMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!menuBtn || !mobileMenu) return;

    menuBtn.addEventListener('click', function() {
        mobileMenu.classList.toggle('hidden');
        mobileMenu.classList.toggle('open');

        // Change icon
        const icon = menuBtn.querySelector('i');
        if (mobileMenu.classList.contains('open')) {
            icon.setAttribute('data-lucide', 'x');
        } else {
            icon.setAttribute('data-lucide', 'menu');
        }
        lucide.createIcons();
    });

    // Close menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileMenu.classList.add('hidden');
            mobileMenu.classList.remove('open');
            const icon = menuBtn.querySelector('i');
            icon.setAttribute('data-lucide', 'menu');
            lucide.createIcons();
        });
    });
}

/**
 * Scroll reveal animation using Intersection Observer
 */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal-up, .reveal-left, .reveal-right');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add delay based on data attribute or default
                const delay = entry.target.style.animationDelay || '0s';
                
                setTimeout(() => {
                    entry.target.classList.add('revealed');
                }, parseFloat(delay) * 1000);

                // Unobserve after revealing
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    revealElements.forEach(el => {
        revealObserver.observe(el);
    });
}

/**
 * Counter animation for stats
 */
function initCounters() {
    const counters = document.querySelectorAll('.counter');

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-target'));
                const duration = 2000; // 2 seconds
                const step = target / (duration / 16); // 60fps
                let current = 0;

                const updateCounter = () => {
                    current += step;
                    if (current < target) {
                        counter.textContent = Math.floor(current).toLocaleString('pt-BR');
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target.toLocaleString('pt-BR');
                    }
                };

                updateCounter();
                counterObserver.unobserve(counter);
            }
        });
    }, {
        threshold: 0.5
    });

    counters.forEach(counter => {
        counterObserver.observe(counter);
    });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                
                const navbarHeight = document.getElementById('navbar').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Parallax effect for hero background
 */
function initParallax() {
    const heroBg = document.getElementById('hero-bg');
    if (!heroBg) return;

    let ticking = false;

    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                const scrolled = window.pageYOffset;
                const rate = scrolled * 0.3;
                
                if (scrolled < window.innerHeight) {
                    heroBg.style.transform = `scale(1.1) translateY(${rate * 0.1}px)`;
                }
                
                ticking = false;
            });

            ticking = true;
        }
    });
}

/**
 * Back to top button
 */
function initBackToTop() {
    // Create back to top button
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>';
    backToTop.className = 'back-to-top';
    backToTop.setAttribute('aria-label', 'Voltar ao topo');
    document.body.appendChild(backToTop);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 500) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });

    backToTop.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * Gallery lightbox
 */
function initGallery() {
    const galleryItems = document.querySelectorAll('#galeria .group');

    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            // Find the image
            const img = this.querySelector('img');
            if (!img) return;

            // Create lightbox
            const lightbox = document.createElement('div');
            lightbox.className = 'lightbox';
            lightbox.innerHTML = `
                <button class="lightbox-close">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
                <img src="${img.src}" alt="${img.alt}">
            `;

            document.body.appendChild(lightbox);

            // Fade in
            requestAnimationFrame(() => {
                lightbox.classList.add('active');
            });

            // Close on click
            lightbox.addEventListener('click', function(e) {
                if (e.target === lightbox || e.target.closest('.lightbox-close')) {
                    lightbox.classList.remove('active');
                    setTimeout(() => {
                        lightbox.remove();
                    }, 300);
                }
            });

            // Close on escape
            document.addEventListener('keydown', function handleEscape(e) {
                if (e.key === 'Escape' && lightbox.parentNode) {
                    lightbox.classList.remove('active');
                    setTimeout(() => {
                        lightbox.remove();
                    }, 300);
                    document.removeEventListener('keydown', handleEscape);
                }
            });
        });
    });
}

/**
 * Toast notification function (for future use)
 */
function showToast(message, type = 'success') {
    // Implementation can be added if needed
    console.log(message, type);
}

/**
 * Form validation helper (for future use)
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-red-500');
            
            // Add shake animation
            input.classList.add('animate-shake');
            setTimeout(() => {
                input.classList.remove('animate-shake');
            }, 500);
        } else {
            input.classList.remove('border-red-500');
        }
    });

    return isValid;
}

/**
 * Lazy loading images (for future optimization)
 */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                img.classList.add('loaded');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

/**
 * Shake animation keyframes injection
 */
const shakeKeyframes = `
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

.animate-shake {
    animation: shake 0.3s ease-in-out;
}
`;

// Inject shake styles
const styleSheet = document.createElement('style');
styleSheet.textContent = shakeKeyframes;
document.head.appendChild(styleSheet);

/**
 * Service card click handler
 */
document.addEventListener('click', function(e) {
    // Handle service card clicks
    const serviceCard = e.target.closest('.glass-card');
    if (serviceCard) {
        // Add click animation
        serviceCard.style.transform = 'scale(0.98)';
        setTimeout(() => {
            serviceCard.style.transform = '';
        }, 150);
    }
});

/**
 * Navbar link active state
 */
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    const currentScroll = window.pageYOffset + 100;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');

        if (currentScroll >= sectionTop && currentScroll < sectionTop + sectionHeight) {
            navLinks.forEach(link => {
                link.classList.remove('text-turquoise-500', 'font-semibold');
                if (link.getAttribute('href') === `#${sectionId}`) {
                    link.classList.add('text-turquoise-500', 'font-semibold');
                }
            });
        }
    });
}

window.addEventListener('scroll', updateActiveNavLink);

/**
 * Mobile navigation close on resize
 */
window.addEventListener('resize', function() {
    const mobileMenu = document.getElementById('mobile-menu');
    const menuBtn = document.getElementById('mobile-menu-btn');

    if (window.innerWidth >= 768 && mobileMenu) {
        mobileMenu.classList.add('hidden');
        mobileMenu.classList.remove('open');
        if (menuBtn) {
            const icon = menuBtn.querySelector('i');
            if (icon) icon.setAttribute('data-lucide', 'menu');
            lucide.createIcons();
        }
    }
});

/**
 * Performance: Debounce function
 */
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

/**
 * Performance: Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Apply throttle to scroll events for better performance
const throttledScroll = throttle(() => {
    // Throttled scroll operations
}, 100);

window.addEventListener('scroll', throttledScroll);

/**
 * Service card price hover effect
 */
document.querySelectorAll('.glass-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        const price = this.querySelector('.text-coral-300');
        if (price) {
            price.style.transform = 'translateY(0)';
            price.style.opacity = '1';
        }
    });

    card.addEventListener('mouseleave', function() {
        const price = this.querySelector('.text-coral-300');
        if (price) {
            price.style.transform = '';
            price.style.opacity = '';
        }
    });
});

/**
 * Initialize Lucide icons on DOM load
 */
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
});

/**
 * Console welcome message
 */
console.log('%c Studio Gui Poncciano ', 'background: linear-gradient(90deg, #14B8A6, #F97316); color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;');
console.log('Transformando vidas através da beleza.');
