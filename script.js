// ============================================
// Navigation Scroll Effect
// ============================================

const nav = document.getElementById('nav');
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');

let navScrollTicking = false;
let lastNavScrollY = 0;

window.addEventListener('scroll', () => {
    lastNavScrollY = window.scrollY;

    if (!navScrollTicking) {
        window.requestAnimationFrame(() => {
            if (lastNavScrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
            navScrollTicking = false;
        });
        navScrollTicking = true;
    }
}, { passive: true });

// Mobile Menu Toggle
navToggle.addEventListener('click', () => {
    const isActive = navMenu.classList.toggle('active');
    navToggle.classList.toggle('active');
    document.body.style.overflow = isActive ? 'hidden' : '';

    // Avoid breaking the fixed menu layout: transforms on the nav create a containing block
    // that clips the mobile menu. Force the nav to stay untransformed while the menu is open.
    if (isActive) {
        nav.style.transform = 'none';
    } else {
        nav.style.transform = '';
    }
});

// Close mobile menu when clicking on a link
navMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
        document.body.style.overflow = '';
    });
});

// ============================================
// Smooth Scroll
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const navHeight = nav.offsetHeight;
            const targetPosition = target.offsetTop - navHeight;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// ============================================
// WoW (Scroll Animations)
// ============================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Get delay from data attribute
            const delay = entry.target.dataset.delay || 0;

            setTimeout(() => {
                entry.target.classList.add('animated');
            }, parseInt(delay));

            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all elements with wow classes
document.querySelectorAll('.wow-fade-up, .wow-fade-in').forEach(el => {
    observer.observe(el);
});

// ============================================
// Counter Animation (About Section Stats)
// ============================================

const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const target = parseInt(entry.target.dataset.target);
            animateCounter(entry.target, target);
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number').forEach(stat => {
    statsObserver.observe(stat);
});

function animateCounter(element, target) {
    let current = 0;
    const increment = target / 60; // 60 frames for smooth animation
    const duration = 2000; // 2 seconds
    const stepTime = duration / 60;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, stepTime);
}

// ============================================
// FAQ Accordion
// ============================================

const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');

    question.addEventListener('click', () => {
        const isActive = item.classList.contains('active');

        // Close all items
        faqItems.forEach(faqItem => {
            faqItem.classList.remove('active');
        });

        // Open clicked item if it wasn't active
        if (!isActive) {
            item.classList.add('active');
        }
    });
});

// ============================================
// Form Handling
// ============================================

const contactForm = document.querySelector('.contact-form');

if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Get form data
        const formData = new FormData(contactForm);
        const data = Object.fromEntries(formData);

        // Here you would typically send the data to your backend
        console.log('Form submitted:', data);

        // Show success message (you can customize this)
        alert('Mensagem enviada com sucesso! Entraremos em contato em breve.');

        // Reset form
        contactForm.reset();
    });
}

// ============================================
// Parallax Effect for Blobs
// ============================================

let lastScrollY = window.scrollY;
const blobs = document.querySelectorAll('.blob');

function updateBlobPositions() {
    const scrollY = window.scrollY;
    const deltaY = scrollY - lastScrollY;

    blobs.forEach((blob, index) => {
        const speed = 0.5 + (index * 0.1); // Different speeds for each blob
        const currentTransform = getComputedStyle(blob).transform;

        // Extract current translate values or use 0 if none
        let currentY = 0;
        if (currentTransform !== 'none') {
            const matrix = currentTransform.match(/matrix.*\((.+)\)/);
            if (matrix) {
                const values = matrix[1].split(', ');
                currentY = parseFloat(values[5] || 0);
            }
        }

        const newY = currentY + (deltaY * speed);
        blob.style.transform = `translateY(${newY}px)`;
    });

    lastScrollY = scrollY;
}

// Throttle parallax for performance
let ticking = false;
window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            updateBlobPositions();
            ticking = false;
        });
        ticking = true;
    }
});

// ============================================
// Hero Animation on Load
// ============================================

window.addEventListener('load', () => {
    // Animate hero content
    const heroText = document.querySelector('.hero-text');
    const heroVisual = document.querySelector('.hero-visual');

    if (heroText && heroVisual) {
        setTimeout(() => {
            heroText.classList.add('animated');
        }, 100);

        setTimeout(() => {
            heroVisual.classList.add('animated');
        }, 300);
    }
});

// ============================================
// Enhanced Button Interactions
// ============================================

const buttons = document.querySelectorAll('.btn');

buttons.forEach(btn => {
    btn.addEventListener('mouseenter', function(e) {
        createRipple(e, this);
    });
});

function createRipple(event, button) {
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple-effect');

    const existingRipple = button.querySelector('.ripple-effect');
    if (existingRipple) {
        existingRipple.remove();
    }

    button.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Add ripple effect styles dynamically
const style = document.createElement('style');
style.textContent = `
    .btn {
        overflow: hidden;
    }

    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }

    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================
// Service Cards Tilt Effect
// ============================================

const serviceCards = document.querySelectorAll('.service-card');

serviceCards.forEach(card => {
    card.addEventListener('mousemove', handleTilt);
    card.addEventListener('mouseleave', resetTilt);
});

function handleTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = (y - centerY) / 20;
    const rotateY = (centerX - x) / 20;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
}

function resetTilt(e) {
    const card = e.currentTarget;
    card.style.transform = '';
}

// ============================================
// Testimonial Cards Hover Effect
// ============================================

const testimonialCards = document.querySelectorAll('.testimonial-card');

testimonialCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        const blob = this.querySelector('.testimonial-blob');
        if (blob) {
            blob.style.transform = 'scale(1.3) rotate(15deg)';
            blob.style.opacity = '0.2';
        }
    });

    card.addEventListener('mouseleave', function() {
        const blob = this.querySelector('.testimonial-blob');
        if (blob) {
            blob.style.transform = '';
            blob.style.opacity = '';
        }
    });
});

// ============================================
// Cursor Trail Effect (Subtle)
// ============================================

let cursorTrail = [];
const trailLength = 5;

document.addEventListener('mousemove', (e) => {
    // Only create trail on larger screens
    if (window.innerWidth < 768) return;

    cursorTrail.push({
        x: e.clientX,
        y: e.clientY,
        timestamp: Date.now()
    });

    // Keep only recent positions
    if (cursorTrail.length > trailLength) {
        cursorTrail.shift();
    }
});

// ============================================
// Image Lazy Loading Enhancement
// ============================================

if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.src = img.dataset.src || img.src;
    });
} else {
    // Fallback for browsers that don't support lazy loading
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// ============================================
// Performance Optimization: Reduce Motion
// ============================================

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (prefersReducedMotion.matches) {
    // Disable animations for users who prefer reduced motion
    document.documentElement.style.setProperty('--transition-fast', '0s');
    document.documentElement.style.setProperty('--transition-base', '0s');
    document.documentElement.style.setProperty('--transition-slow', '0s');
}

// ============================================
// Auto-hide Navigation on Scroll Down
// ============================================

let lastKnownScrollY = 0;
let currentScrollY = 0;
let scrollTicking = false;

function updateNavVisibility() {
    // Disable auto-hide transform on small screens to avoid clipping the mobile menu
    if (window.innerWidth <= 768) {
        nav.style.transform = 'translateY(0)';
        scrollTicking = false;
        return;
    }

    // Keep nav pinned when the mobile menu is open to prevent clipping
    if (navMenu.classList.contains('active')) {
        nav.style.transform = 'none';
        scrollTicking = false;
        return;
    }

    currentScrollY = window.scrollY;

    if (currentScrollY > 100) {
        if (currentScrollY > lastKnownScrollY) {
            // Scrolling down
            nav.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            nav.style.transform = 'translateY(0)';
        }
    } else {
        nav.style.transform = 'translateY(0)';
    }

    lastKnownScrollY = currentScrollY;
    scrollTicking = false;
}

window.addEventListener('scroll', () => {
    if (!scrollTicking) {
        window.requestAnimationFrame(updateNavVisibility);
        scrollTicking = true;
    }
});

// Add smooth transform to nav
nav.style.transition = 'transform 0.3s ease, background 0.3s ease, box-shadow 0.3s ease';

// ============================================
// Intersection Observer for Service Cards
// ============================================

const serviceCardsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
});

serviceCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    serviceCardsObserver.observe(card);
});

// ============================================
// Analytics Event Tracking (placeholder)
// ============================================

function trackEvent(category, action, label) {
    // Placeholder for analytics tracking
    // Replace with your analytics solution (GA4, Mixpanel, etc.)
    console.log('Event:', category, action, label);
}

// Track CTA clicks
document.querySelectorAll('.btn-primary').forEach(btn => {
    btn.addEventListener('click', () => {
        trackEvent('CTA', 'Click', btn.textContent.trim());
    });
});

// Track service card interactions
serviceCards.forEach(card => {
    card.addEventListener('click', () => {
        const serviceName = card.querySelector('h3').textContent;
        trackEvent('Service', 'Click', serviceName);
    });
});

// ============================================
// Console Message
// ============================================

console.log(
    '%c🎨 Pixel Alchemy',
    'font-size: 24px; font-weight: bold; color: #e07856;'
);
console.log(
    '%cCriando experiências digitais extraordinárias',
    'font-size: 14px; color: #8ba888;'
);
console.log(
    '%c💼 Interessado em trabalhar conosco? Entre em contato!',
    'font-size: 12px; color: #1a1f2e;'
);

/* ============================================
   Cookie Consent Logic
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
    const cookieConsent = document.getElementById('cookieConsent');
    const acceptBtn = document.getElementById('acceptCookies');
    const declineBtn = document.getElementById('declineCookies');

    // Check if user has already made a choice
    const hasConsented = localStorage.getItem('cookieConsent');

    if (!hasConsented) {
        // Show popup after a short delay
        setTimeout(() => {
            cookieConsent.classList.add('show');
        }, 1000);
    }

    // Accept Cookies
    acceptBtn.addEventListener('click', () => {
        localStorage.setItem('cookieConsent', 'true');
        cookieConsent.classList.remove('show');
        
        // Optional: Initialize analytics here if needed
        // initAnalytics();
    });

    // Decline Cookies
    declineBtn.addEventListener('click', () => {
        localStorage.setItem('cookieConsent', 'false');
        cookieConsent.classList.remove('show');
    });
});
