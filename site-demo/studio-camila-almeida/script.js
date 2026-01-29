// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        navbar.classList.add('nav-scrolled');
    } else {
        navbar.classList.remove('nav-scrolled');
    }
});

// Mobile menu toggle
const menuBtn = document.getElementById('menu-btn');
let mobileMenu = null;

menuBtn.addEventListener('click', () => {
    if (!mobileMenu) {
        mobileMenu = document.createElement('div');
        mobileMenu.className = 'md:hidden fixed inset-0 bg-emerald-900 z-40 flex flex-col items-center justify-center space-y-8';
        mobileMenu.innerHTML = `
            <a href="#home" class="text-white text-2xl hover:text-emerald-300" onclick="closeMenu()">Início</a>
            <a href="#sobre" class="text-white text-2xl hover:text-emerald-300" onclick="closeMenu()">Sobre</a>
            <a href="#servicos" class="text-white text-2xl hover:text-emerald-300" onclick="closeMenu()">Serviços</a>
            <a href="#galeria" class="text-white text-2xl hover:text-emerald-300" onclick="closeMenu()">Galeria</a>
            <a href="#contato" class="text-white text-2xl hover:text-emerald-300" onclick="closeMenu()">Contato</a>
            <button onclick="closeMenu()" class="absolute top-6 right-6 text-white">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        `;
        document.body.appendChild(mobileMenu);
    } else {
        mobileMenu.style.display = 'flex';
    }
});

function closeMenu() {
    if (mobileMenu) {
        mobileMenu.style.display = 'none';
    }
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in-up');
            entry.target.style.opacity = '1';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('section h2, section p, .group').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
});
