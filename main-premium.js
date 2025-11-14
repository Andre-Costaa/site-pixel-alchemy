// PIXEL ALCHEMY - Premium Hero Animation
// Refatoração completa: Elegância, Interatividade e Performance

// Splash Screen Manager
class SplashScreenManager {
    constructor() {
        this.splashScreen = document.getElementById('splashScreen');
        this.loaderPercentage = document.getElementById('loaderPercentage');
        this.loaderProgress = document.getElementById('loaderProgress');
        this.hasVisited = sessionStorage.getItem('pixelAlchemyVisited');

        this.init();
    }

    init() {
        // Skip splash if user already visited in this session
        if (this.hasVisited) {
            this.hideSplash(0);
            return;
        }

        // Animate loading percentage
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                this.hideSplash(500);
            }
            this.loaderPercentage.textContent = Math.floor(progress) + '%';
            if (this.loaderProgress) {
                this.loaderProgress.style.width = progress + '%';
            }
        }, 80);
    }

    hideSplash(delay) {
        setTimeout(() => {
            this.splashScreen.classList.add('hidden');
            sessionStorage.setItem('pixelAlchemyVisited', 'true');

            // Remove from DOM after transition
            setTimeout(() => {
                if (this.splashScreen.parentNode) {
                    this.splashScreen.remove();
                }
            }, 800);
        }, delay);
    }
}

class EterusPremiumHero {
    constructor(canvas) {
        this.canvas = canvas;
        this.breathingPhase = 0;
        this.networkBaseScale = 1;
        this.currentBreathScale = 1;
        this.lastTimestamp = performance.now();
        this.init();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );

        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            alpha: true,
            antialias: true,
            powerPreference: "high-performance"
        });

        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setClearColor(0x000000, 0);

        // Camera position
        this.camera.position.z = 40;
        this.baseCameraZ = 40;

        // Create particle system (network background)
        this.createParticleSystem();

        // Setup interactions
        this.setupInteractions();

        // Start animation loop
        this.animate();
    }

    createParticleSystem() {
        const isMobile = window.innerWidth < 768;
        const particleCount = isMobile ? 800 : 1500;

        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);
        const originalPositions = new Float32Array(particleCount * 3);

        // Distribute particles in elegant spherical pattern
        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            // Fibonacci sphere distribution for even spacing
            const y = 1 - (i / (particleCount - 1)) * 2;
            const radius = Math.sqrt(1 - y * y);
            const theta = Math.PI * (1 + Math.sqrt(5)) * i;

            const distance = 12 + Math.random() * 8;

            positions[i3] = Math.cos(theta) * radius * distance;
            positions[i3 + 1] = y * distance;
            positions[i3 + 2] = Math.sin(theta) * radius * distance;

            // Store original positions
            originalPositions[i3] = positions[i3];
            originalPositions[i3 + 1] = positions[i3 + 1];
            originalPositions[i3 + 2] = positions[i3 + 2];

            // Varied sizes for depth
            sizes[i] = 0.08 + Math.random() * 0.12;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            size: 0.12,
            color: 0xA8D5BA,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.particles = new THREE.Points(geometry, material);
        this.originalParticlePositions = originalPositions;
        this.scene.add(this.particles);

        // Connection lines between nearby particles
        this.createConnectionLines(particleCount);
        this.updateNetworkBaseScale();
    }

    createConnectionLines(particleCount) {
        const maxConnections = particleCount * 3;
        const positions = new Float32Array(maxConnections * 2 * 3);

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.LineBasicMaterial({
            color: 0xA8D5BA,
            transparent: true,
            opacity: 0.15,
            blending: THREE.AdditiveBlending
        });

        this.connections = new THREE.LineSegments(geometry, material);
        this.scene.add(this.connections);
    }

    setupInteractions() {
        // Window resize
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.updateNetworkBaseScale();
        });
    }

    updateParticleAttraction() {
        // Relax particles back to their original positions for stability
        const positions = this.particles.geometry.attributes.position.array;
        const original = this.originalParticlePositions;

        for (let i = 0; i < positions.length; i += 3) {
            positions[i] += (original[i] - positions[i]) * 0.05;
            positions[i + 1] += (original[i + 1] - positions[i + 1]) * 0.05;
            positions[i + 2] += (original[i + 2] - positions[i + 2]) * 0.05;
        }

        this.particles.geometry.attributes.position.needsUpdate = true;
    }

    updateConnectionLines() {
        // Update connection lines between nearby particles
        const particlePositions = this.particles.geometry.attributes.position.array;
        const linePositions = this.connections.geometry.attributes.position.array;
        const maxDistance = 6;
        const maxConnections = 3;

        let lineIndex = 0;
        const sampleRate = 4; // Sample every 4th particle for performance

        for (let i = 0; i < particlePositions.length; i += sampleRate * 3) {
            let connections = 0;

            for (let j = i + 3; j < particlePositions.length && connections < maxConnections; j += sampleRate * 3) {
                const dx = particlePositions[i] - particlePositions[j];
                const dy = particlePositions[i + 1] - particlePositions[j + 1];
                const dz = particlePositions[i + 2] - particlePositions[j + 2];
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (distance < maxDistance) {
                    linePositions[lineIndex * 6] = particlePositions[i];
                    linePositions[lineIndex * 6 + 1] = particlePositions[i + 1];
                    linePositions[lineIndex * 6 + 2] = particlePositions[i + 2];
                    linePositions[lineIndex * 6 + 3] = particlePositions[j];
                    linePositions[lineIndex * 6 + 4] = particlePositions[j + 1];
                    linePositions[lineIndex * 6 + 5] = particlePositions[j + 2];

                    lineIndex++;
                    connections++;
                }
            }
        }

        this.connections.geometry.attributes.position.needsUpdate = true;
    }

    updateAutoRotation(deltaTime) {
        // Constant, ultra-smooth autonomous rotation
        const rotationSpeedY = 0.00002 * deltaTime;
        const rotationSpeedX = 0.00001 * deltaTime;
        this.particles.rotation.y += rotationSpeedY;
        this.particles.rotation.x += rotationSpeedX;
        this.connections.rotation.y = this.particles.rotation.y;
        this.connections.rotation.x = this.particles.rotation.x;
    }

    updateBreathingEffect(deltaTime) {
        // Subtle organic breathing to keep network alive
        this.breathingPhase += 0.0015 * deltaTime;

        const breathStrength = Math.sin(this.breathingPhase) * 0.01;
        const breathe = 1 + breathStrength;
        this.particles.scale.set(breathe, breathe, breathe);
        this.currentBreathScale = breathe;
        this.applyNetworkScale();

        const particleGlow = 0.65 + breathStrength * 3.0;
        this.particles.material.opacity = particleGlow;

        const lineGlow = 0.12 + breathStrength * 1.5;
        this.connections.material.opacity = lineGlow;
    }

    updateNetworkBaseScale() {
        const isDesktop = window.innerWidth >= 1024;
        this.networkBaseScale = isDesktop ? 1.6 : 1.0;
        this.applyNetworkScale();
    }

    applyNetworkScale() {
        if (!this.particles || !this.connections) return;
        const totalScale = this.networkBaseScale * this.currentBreathScale;
        this.particles.scale.set(totalScale, totalScale, totalScale);
        this.connections.scale.set(totalScale, totalScale, totalScale);
    }

    animate() {
        const now = performance.now();
        const deltaTime = this.lastTimestamp ? (now - this.lastTimestamp) : 16;
        this.lastTimestamp = now;

        requestAnimationFrame(() => this.animate());

        this.updateBreathingEffect(deltaTime);
        this.updateAutoRotation(deltaTime);
        this.updateParticleAttraction();
        this.updateConnectionLines();

        // Render
        this.renderer.render(this.scene, this.camera);
    }
}

// About Metrics Animator
class AboutMetricsAnimator {
    constructor() {
        this.metrics = Array.from(document.querySelectorAll('[data-metric-target]'));
        if (!this.metrics.length) return;

        this.handleIntersect = this.handleIntersect.bind(this);

        this.observer = new IntersectionObserver(this.handleIntersect, {
            threshold: 0.5,
            rootMargin: '0px 0px -10% 0px'
        });

        this.metrics.forEach(metric => {
            const prefix = metric.dataset.metricPrefix || '';
            const suffix = metric.dataset.metricSuffix || '';
            metric.textContent = `${prefix}0${suffix}`;
            this.observer.observe(metric);
        });
    }

    handleIntersect(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                this.animateMetric(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }

    animateMetric(element) {
        if (element.dataset.metricAnimating === 'true') return;
        element.dataset.metricAnimating = 'true';

        const target = parseFloat(element.dataset.metricTarget || '0');
        const start = parseFloat(element.dataset.metricStart || '0');
        const prefix = element.dataset.metricPrefix || '';
        const suffix = element.dataset.metricSuffix || '';
        const duration = parseInt(element.dataset.metricDuration || '1600', 10);
        const decimals = parseInt(element.dataset.metricDecimals || '0', 10);

        const startTime = performance.now();

        const step = (now) => {
            const progress = Math.min((now - startTime) / duration, 1);
            const value = start + (target - start) * progress;
            element.textContent = `${prefix}${value.toFixed(decimals)}${suffix}`;
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                element.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
            }
        };

        requestAnimationFrame(step);
    }
}

// Scroll Progress Bar Manager
class ScrollProgressBar {
    constructor() {
        this.progressBar = document.getElementById('scrollProgress');
        if (this.progressBar) {
            this.init();
        }
    }

    init() {
        window.addEventListener('scroll', () => this.updateProgress());
        this.updateProgress();
    }

    updateProgress() {
        const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = (window.scrollY / windowHeight) * 100;
        this.progressBar.style.width = scrolled + '%';
    }
}

// Navbar Manager
class NavbarManager {
    constructor() {
        this.navbar = document.getElementById('navbar');
        this.mobileMenuBtn = document.getElementById('mobileMenuBtn');
        this.mobileMenu = document.getElementById('mobileMenu');

        if (this.navbar) {
            this.init();
        }
    }

    init() {
        // Scroll effect
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                this.navbar.classList.add('scrolled');
            } else {
                this.navbar.classList.remove('scrolled');
            }
        });

        // Mobile menu toggle
        if (this.mobileMenuBtn && this.mobileMenu) {
            this.mobileMenuBtn.addEventListener('click', () => {
                this.mobileMenu.classList.toggle('hidden');
            });

            // Close mobile menu when clicking a link
            this.mobileMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    this.mobileMenu.classList.add('hidden');
                });
            });
        }

        // Smooth scroll for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

// Section Reveal Animations Manager
class SectionRevealManager {
    constructor() {
        this.init();
    }

    init() {
        // Create intersection observer for section reveals
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                }
            });
        }, observerOptions);

        // Observe all sections with reveal animation
        document.querySelectorAll('.section-reveal').forEach(el => {
            observer.observe(el);
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize splash screen manager
    new SplashScreenManager();

    // Initialize scroll progress bar
    new ScrollProgressBar();

    // Initialize navbar
    new NavbarManager();

    // Initialize section reveals
    new SectionRevealManager();

    // Initialize hero animation
    const canvas = document.getElementById('heroCanvas');
    if (canvas) {
        new EterusPremiumHero(canvas);
    }

    // Initialize about metrics animation
    new AboutMetricsAnimator();
});

// Trigger initial animations on window load
window.addEventListener('load', () => {
    document.body.classList.add('loaded');

    // Trigger initial section reveals
    setTimeout(() => {
        document.querySelectorAll('.section-reveal').forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('revealed');
            }, index * 100);
        });
    }, 500);
});
