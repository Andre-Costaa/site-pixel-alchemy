// Eterus - Main JavaScript File
// Advanced animations and interactions for premium tech agency website

const FEATURE_FLAGS = {
    // Toggle for the new refractive portal hero centerpiece
    refractivePortal: true,
};

// Splash Screen Controller
class SplashScreen {
    constructor() {
        this.splashScreen = document.getElementById('splashScreen');
        this.loaderPercentage = document.getElementById('loaderPercentage');
        this.hasVisited = sessionStorage.getItem('eterusVisited');

        this.init();
    }

    init() {
        // Skip splash if user already visited in this session
        if (this.hasVisited) {
            this.splashScreen.classList.add('hidden');
            return;
        }

        // Animate loading percentage
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                this.hideSplash();
            }
            this.loaderPercentage.textContent = Math.floor(progress) + '%';
        }, 100);
    }

    hideSplash() {
        setTimeout(() => {
            this.splashScreen.classList.add('hidden');
            sessionStorage.setItem('eterusVisited', 'true');

            // Remove from DOM after transition
            setTimeout(() => {
                this.splashScreen.remove();
            }, 800);
        }, 500);
    }
}

// Scroll Progress Bar
class ScrollProgressBar {
    constructor() {
        this.progressBar = document.getElementById('scrollProgress');
        this.init();
    }

    init() {
        window.addEventListener('scroll', () => this.updateProgress());
        this.updateProgress(); // Initial update
    }

    updateProgress() {
        const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = (window.scrollY / windowHeight) * 100;
        this.progressBar.style.width = scrolled + '%';
    }
}

// Magnetic Button Effect
class MagneticButtons {
    constructor() {
        this.buttons = document.querySelectorAll('.magnetic-btn');
        this.init();
    }

    init() {
        this.buttons.forEach(button => {
            button.addEventListener('mousemove', (e) => this.handleMouseMove(e, button));
            button.addEventListener('mouseleave', () => this.handleMouseLeave(button));
            button.addEventListener('click', (e) => this.createRipple(e, button));
        });
    }

    handleMouseMove(e, button) {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        // Magnetic effect - button follows cursor within 100px radius
        const distance = Math.sqrt(x * x + y * y);
        const maxDistance = 80;

        if (distance < maxDistance) {
            const strength = (maxDistance - distance) / maxDistance;
            const moveX = x * strength * 0.4;
            const moveY = y * strength * 0.4;

            button.style.transform = `translate(${moveX}px, ${moveY}px)`;

            // Inner element movement (parallax effect)
            const inner = button.querySelector('.magnetic-btn-inner');
            if (inner) {
                inner.style.transform = `translate(${moveX * 0.5}px, ${moveY * 0.5}px)`;
            }
        }
    }

    handleMouseLeave(button) {
        button.style.transform = 'translate(0, 0)';
        const inner = button.querySelector('.magnetic-btn-inner');
        if (inner) {
            inner.style.transform = 'translate(0, 0)';
        }
    }

    createRipple(e, button) {
        const ripple = document.createElement('span');
        ripple.className = 'ripple';

        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        button.appendChild(ripple);

        // Remove ripple after animation
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
}

class EterusAnimations {
    constructor() {
        this.heroCanvas = null;
        this.particles = [];
        this.mouse = { x: 0, y: 0 };
        this.scrollY = 0;
        this.cursorTrail = document.getElementById('cursorTrail');

        this.init();
    }

    init() {
        this.setupCursorTrail();
        this.setupHeroAnimation();
        this.setupScrollAnimations();
        this.setupParticleSystem();
        this.setupAboutAnimation();
        this.setupNavbar();
        this.setupFormHandling();

        // Initialize all animations
        this.animate();
    }
    
    setupCursorTrail() {
        // Track mouse position for interaction effects
        document.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
    }
    
    setupHeroAnimation() {
        const canvas = document.getElementById('heroCanvas');
        if (!canvas) return;

        // Initialize Three.js hero scene
        this.initHero3D(canvas);
    }

    initHero3D(canvas) {
        // Scene setup
        this.hero3D = {
            scene: new THREE.Scene(),
            camera: new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000),
            renderer: new THREE.WebGLRenderer({
                canvas: canvas,
                alpha: true,
                antialias: true
            })
        };

        const { scene, camera, renderer } = this.hero3D;

        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x000000, 0);

        // === DIGITAL CRYSTALLIZATION SYSTEM ===
        // Three-state progression: VISION → REFINEMENT → EXCELLENCE

        // State machine
        this.hero3D.states = {
            VISION: 0,
            REFINEMENT: 1,
            EXCELLENCE: 2
        };

        this.hero3D.currentState = this.hero3D.states.VISION;
        this.hero3D.stateProgress = 0;
        this.hero3D.stateDurations = [7000, 6000, 7000]; // milliseconds per state
        this.hero3D.lastTimestamp = performance.now();

        // Crystal geometry - unique ETERUS signature shape
        const crystalGeometry = new THREE.IcosahedronGeometry(8, 2);
        this.hero3D.crystalGeometry = crystalGeometry;

        // Enhanced materials for premium look
        const wireframeMaterial = new THREE.MeshBasicMaterial({
            color: 0xA8D5BA,
            wireframe: true,
            transparent: true,
            opacity: 0,
            metalness: 0.8
        });

        this.hero3D.mainMesh = new THREE.Mesh(crystalGeometry.clone(), wireframeMaterial);
        scene.add(this.hero3D.mainMesh);

        // Solid inner core for depth (frosted glass effect)
        const coreMaterial = new THREE.MeshBasicMaterial({
            color: 0xA8D5BA,
            transparent: true,
            opacity: 0,
            side: THREE.BackSide
        });
        this.hero3D.coreMesh = new THREE.Mesh(crystalGeometry.clone(), coreMaterial);
        this.hero3D.coreMesh.scale.set(0.95, 0.95, 0.95);
        scene.add(this.hero3D.coreMesh);

        // Glow outline layer
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: 0xB8B9D3,
            wireframe: true,
            transparent: true,
            opacity: 0
        });
        this.hero3D.glowMesh = new THREE.Mesh(crystalGeometry.clone(), glowMaterial);
        this.hero3D.glowMesh.scale.set(1.05, 1.05, 1.05);
        scene.add(this.hero3D.glowMesh);

        if (FEATURE_FLAGS.refractivePortal) {
            this.createRefractivePortal(scene);
        }

        // Particle system with target positions for crystallization
        const particlesGeometry = new THREE.BufferGeometry();
        const isMobile = window.innerWidth < 768;
        const particlesCount = isMobile ? 1000 : 2000;
        this.hero3D.particlesCount = particlesCount;

        const posArray = new Float32Array(particlesCount * 3);
        const velocityArray = new Float32Array(particlesCount * 3);
        const targetArray = new Float32Array(particlesCount * 3);
        const sizeArray = new Float32Array(particlesCount);

        // Get crystal vertices for particle targets
        const crystalVertices = crystalGeometry.attributes.position.array;
        const vertexCount = crystalVertices.length / 3;

        for (let i = 0; i < particlesCount; i++) {
            const i3 = i * 3;

            // Random starting positions in spherical distribution
            const radius = 15 + Math.random() * 20;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            posArray[i3] = radius * Math.sin(phi) * Math.cos(theta);
            posArray[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            posArray[i3 + 2] = radius * Math.cos(phi);

            // Brownian motion velocities
            velocityArray[i3] = (Math.random() - 0.5) * 0.03;
            velocityArray[i3 + 1] = (Math.random() - 0.5) * 0.03;
            velocityArray[i3 + 2] = (Math.random() - 0.5) * 0.03;

            // Assign target position (crystal vertex)
            const targetVertex = (i % vertexCount) * 3;
            targetArray[i3] = crystalVertices[targetVertex];
            targetArray[i3 + 1] = crystalVertices[targetVertex + 1];
            targetArray[i3 + 2] = crystalVertices[targetVertex + 2];

            // Varied particle sizes
            sizeArray[i] = 0.05 + Math.random() * 0.15;
        }

        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizeArray, 1));

        const particlesMaterial = new THREE.PointsMaterial({
            size: 0.1,
            color: 0xA8D5BA,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true
        });

        this.hero3D.particles = new THREE.Points(particlesGeometry, particlesMaterial);
        this.hero3D.particleVelocities = velocityArray;
        this.hero3D.particleTargets = targetArray;
        this.hero3D.particleSizes = sizeArray;
        scene.add(this.hero3D.particles);

        // Connection lines between particles (constellation effect)
        const maxConnections = 5;
        const maxConnectionsTotal = particlesCount * maxConnections;
        const connectionPositions = new Float32Array(maxConnectionsTotal * 2 * 3);

        const connectionsGeometry = new THREE.BufferGeometry();
        connectionsGeometry.setAttribute('position', new THREE.BufferAttribute(connectionPositions, 3));

        const connectionsMaterial = new THREE.LineBasicMaterial({
            color: 0xA8D5BA,
            transparent: true,
            opacity: 0,
            blending: THREE.AdditiveBlending
        });

        this.hero3D.connections = new THREE.LineSegments(connectionsGeometry, connectionsMaterial);
        this.hero3D.maxConnectionDistance = 8;
        this.hero3D.maxConnections = maxConnections;
        scene.add(this.hero3D.connections);

        // Orbiting smaller geometries
        this.hero3D.orbitMeshes = [];
        for (let i = 0; i < 5; i++) {
            const orbitGeometry = new THREE.OctahedronGeometry(1.5, 0);
            const orbitMaterial = new THREE.MeshBasicMaterial({
                color: 0xD4A5A5,
                wireframe: true,
                transparent: true,
                opacity: 0.6
            });
            const orbitMesh = new THREE.Mesh(orbitGeometry, orbitMaterial);

            // Random orbital positions
            const angle = (i / 5) * Math.PI * 2;
            const radius = 20;
            orbitMesh.position.x = Math.cos(angle) * radius;
            orbitMesh.position.z = Math.sin(angle) * radius;
            orbitMesh.userData = { angle, radius, speed: 0.001 + Math.random() * 0.002 };

            this.hero3D.orbitMeshes.push(orbitMesh);
            scene.add(orbitMesh);
        }

        camera.position.z = 40;
        this.hero3D.baseCameraZ = 40;

        // Mouse interaction variables
        this.hero3D.targetRotationX = 0;
        this.hero3D.targetRotationY = 0;

        // Energy pulse for refinement state
        this.hero3D.pulseRings = [];
        for (let i = 0; i < 3; i++) {
            const ringGeometry = new THREE.RingGeometry(0.1, 0.2, 32);
            const ringMaterial = new THREE.MeshBasicMaterial({
                color: 0xB8B9D3,
                transparent: true,
                opacity: 0,
                side: THREE.DoubleSide
            });
            const ring = new THREE.Mesh(ringGeometry, ringMaterial);
            this.hero3D.pulseRings.push(ring);
            scene.add(ring);
        }

        // Click to advance state
        canvas.addEventListener('click', () => {
            this.advanceToNextState();
        });

        // Resize handler
        window.addEventListener('resize', () => this.onHero3DResize());

        // Gyroscope for mobile
        if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission === 'function') {
            // iOS 13+ requires permission
            canvas.addEventListener('click', () => {
                DeviceOrientationEvent.requestPermission()
                    .then(response => {
                        if (response === 'granted') {
                            window.addEventListener('deviceorientation', (e) => this.handleGyroscope(e));
                        }
                    });
            }, { once: true });
        } else if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', (e) => this.handleGyroscope(e));
        }
    }

    createRefractivePortal(scene) {
        // Self-contained group so we can remove it quickly if needed
        const portalGroup = new THREE.Group();
        portalGroup.name = 'RefractivePortal';
        scene.add(portalGroup);

        const portalUniforms = {
            uTime: { value: 0 },
            uMouse: { value: new THREE.Vector2(0.5, 0.5) },
            uGlowIntensity: { value: 0.85 }
        };

        const portalCoreMaterial = new THREE.ShaderMaterial({
            uniforms: portalUniforms,
            transparent: true,
            side: THREE.DoubleSide,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            vertexShader: `
                uniform float uTime;
                varying vec2 vUv;
                varying vec3 vPosition;

                void main() {
                    vUv = uv;
                    vPosition = position;
                    float wave = sin(uTime * 0.8 + position.y * 6.0) * 0.18;
                    vec3 displaced = position + normal * wave;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
                }
            `,
            fragmentShader: `
                uniform float uTime;
                uniform vec2 uMouse;
                uniform float uGlowIntensity;
                varying vec2 vUv;
                varying vec3 vPosition;

                float hash(float n) { return fract(sin(n) * 43758.5453); }

                float noise(vec3 x) {
                    vec3 p = floor(x);
                    vec3 f = fract(x);
                    f = f * f * (3.0 - 2.0 * f);

                    float n = p.x + p.y * 57.0 + p.z * 113.0;
                    float res = mix(mix(mix(hash(n + 0.0), hash(n + 1.0), f.x),
                                        mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y),
                                    mix(mix(hash(n + 113.0), hash(n + 114.0), f.x),
                                        mix(hash(n + 170.0), hash(n + 171.0), f.x), f.y), f.z);
                    return res;
                }

                void main() {
                    vec2 centeredUv = vUv - 0.5;
                    float radial = length(centeredUv);
                    float swirl = atan(centeredUv.y, centeredUv.x);
                    float refractMask = smoothstep(0.7, 0.2, radial);

                    float noiseSample = noise(vec3(radial * 6.0, swirl * 0.5, uTime * 0.15));
                    float caustics = sin(radial * 25.0 - uTime * 2.0) * 0.4;
                    vec3 baseColor = mix(vec3(0.66, 0.84, 0.73), vec3(0.72, 0.73, 0.83), refractMask);
                    vec3 highlights = vec3(0.83, 0.65, 0.65) * (noiseSample * 0.6 + caustics);

                    vec2 mouse = vec2(uMouse.x, 1.0 - uMouse.y) - vUv;
                    float mouseGlow = exp(-40.0 * dot(mouse, mouse));

                    vec3 color = baseColor + highlights + vec3(0.72, 0.73, 0.83) * mouseGlow * uGlowIntensity;
                    float alpha = 0.25 + refractMask * 0.55;
                    gl_FragColor = vec4(color, alpha);
                }
            `
        });

        const portalCore = new THREE.Mesh(new THREE.SphereGeometry(6.5, 128, 128), portalCoreMaterial);
        portalGroup.add(portalCore);

        const glassShell = new THREE.Mesh(
            new THREE.SphereGeometry(7, 64, 64),
            new THREE.MeshPhysicalMaterial({
                color: 0xB8B9D3,
                transmission: 1,
                thickness: 1.4,
                roughness: 0.08,
                metalness: 0.2,
                transparent: true,
                opacity: 0.95,
                clearcoat: 1,
                clearcoatRoughness: 0.02,
                ior: 1.35,
                emissive: new THREE.Color(0x2C3E50),
                emissiveIntensity: 0.35
            })
        );
        glassShell.renderOrder = 1;
        portalGroup.add(glassShell);

        const flareMaterial = new THREE.SpriteMaterial({
            color: new THREE.Color(0xD4A5A5),
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const flares = [];
        for (let i = 0; i < 4; i++) {
            const flare = new THREE.Sprite(flareMaterial.clone());
            flare.scale.set(2 + Math.random() * 2.5, 2 + Math.random() * 2.5, 1);
            portalGroup.add(flare);
            flares.push(flare);
        }

        portalGroup.rotation.x = 0.35;

        this.hero3D.portalGroup = portalGroup;
        this.hero3D.portalUniforms = portalUniforms;
        this.hero3D.portalGlass = glassShell;
        this.hero3D.portalFlares = flares;
    }

    onHero3DResize() {
        if (!this.hero3D) return;

        const { camera, renderer } = this.hero3D;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }

    handleGyroscope(event) {
        if (!this.hero3D) return;

        // Convert device orientation to rotation
        const beta = event.beta || 0; // X axis (-180 to 180)
        const gamma = event.gamma || 0; // Y axis (-90 to 90)

        this.hero3D.targetRotationX = (beta / 180) * Math.PI;
        this.hero3D.targetRotationY = (gamma / 90) * Math.PI;
    }

    // === STATE MACHINE METHODS ===

    advanceToNextState() {
        if (!this.hero3D) return;

        const currentState = this.hero3D.currentState;

        if (currentState === this.hero3D.states.VISION) {
            // Jump to refinement with particle acceleration
            this.hero3D.currentState = this.hero3D.states.REFINEMENT;
            this.hero3D.stateProgress = 0;
        } else if (currentState === this.hero3D.states.REFINEMENT) {
            // Speed up crystallization
            this.hero3D.stateProgress = Math.min(this.hero3D.stateProgress + 3000, this.hero3D.stateDurations[1]);
        } else if (currentState === this.hero3D.states.EXCELLENCE) {
            // Shatter and restart cycle
            this.shatterAndReset();
        }
    }

    shatterAndReset() {
        if (!this.hero3D) return;

        // Explosion effect
        const particles = this.hero3D.particles.geometry.attributes.position.array;
        const velocities = this.hero3D.particleVelocities;

        for (let i = 0; i < particles.length; i += 3) {
            // Add explosive velocity
            const centerDist = Math.sqrt(
                particles[i] ** 2 +
                particles[i + 1] ** 2 +
                particles[i + 2] ** 2
            );

            if (centerDist > 0) {
                const explosionForce = 0.5;
                velocities[i] += (particles[i] / centerDist) * explosionForce;
                velocities[i + 1] += (particles[i + 1] / centerDist) * explosionForce;
                velocities[i + 2] += (particles[i + 2] / centerDist) * explosionForce;
            }
        }

        // Reset to VISION state
        setTimeout(() => {
            this.hero3D.currentState = this.hero3D.states.VISION;
            this.hero3D.stateProgress = 0;
        }, 800);
    }

    crystallizationEase(t) {
        // Custom easing: starts slow (organic), ends sharp (geometric)
        return t < 0.5
            ? 2 * t * t
            : -1 + (4 - 2 * t) * t;
    }

    updateHero3D() {
        if (!this.hero3D) return;

        const { scene, camera, renderer, mainMesh, glowMesh, coreMesh, particles, orbitMeshes, portalGroup, portalGlass } = this.hero3D;
        const portalUniforms = this.hero3D.portalUniforms;
        const portalFlares = this.hero3D.portalFlares;

        // Update state progress based on time
        const currentTime = performance.now();
        const deltaTime = currentTime - this.hero3D.lastTimestamp;
        this.hero3D.lastTimestamp = currentTime;

        this.hero3D.stateProgress += deltaTime;

        // Check for state transition
        const currentDuration = this.hero3D.stateDurations[this.hero3D.currentState];
        if (this.hero3D.stateProgress >= currentDuration) {
            // Advance to next state
            this.hero3D.currentState = (this.hero3D.currentState + 1) % 3;
            this.hero3D.stateProgress = 0;
        }

        // Calculate progress within current state (0 to 1)
        const stateProgressNormalized = this.hero3D.stateProgress / currentDuration;

        // Update based on current state
        switch(this.hero3D.currentState) {
            case this.hero3D.states.VISION:
                this.updateVisionState(stateProgressNormalized);
                break;
            case this.hero3D.states.REFINEMENT:
                this.updateRefinementState(stateProgressNormalized);
                break;
            case this.hero3D.states.EXCELLENCE:
                this.updateExcellenceState(stateProgressNormalized);
                break;
        }

        // Common updates for all states

        // Mouse parallax (strength varies by state)
        const parallaxStrength = [0.3, 0.15, 0.08][this.hero3D.currentState];
        const mouseInfluenceX = (this.mouse.x / window.innerWidth - 0.5) * 2;
        const mouseInfluenceY = (this.mouse.y / window.innerHeight - 0.5) * 2;

        if (portalUniforms) {
            portalUniforms.uTime.value += deltaTime * 0.0015;
            portalUniforms.uMouse.value.set(
                Math.max(0, Math.min(1, this.mouse.x / window.innerWidth)),
                Math.max(0, Math.min(1, this.mouse.y / window.innerHeight))
            );
            const glowBoost = this.hero3D.currentState === this.hero3D.states.EXCELLENCE ? 1.15 : 0.85;
            portalUniforms.uGlowIntensity.value = glowBoost;
        }

        this.hero3D.targetRotationX += mouseInfluenceY * 0.001 * parallaxStrength;
        this.hero3D.targetRotationY += mouseInfluenceX * 0.001 * parallaxStrength;

        // Smooth interpolation
        mainMesh.rotation.x += (this.hero3D.targetRotationX - mainMesh.rotation.x) * 0.05;
        mainMesh.rotation.y += (this.hero3D.targetRotationY - mainMesh.rotation.y) * 0.05;

        // Auto rotation
        mainMesh.rotation.x += 0.001;
        mainMesh.rotation.y += 0.002;

        // Glow and core follow main mesh
        glowMesh.rotation.x = mainMesh.rotation.x;
        glowMesh.rotation.y = mainMesh.rotation.y;
        glowMesh.rotation.z = mainMesh.rotation.z;

        coreMesh.rotation.x = mainMesh.rotation.x * 0.9;
        coreMesh.rotation.y = mainMesh.rotation.y * 0.9;
        coreMesh.rotation.z += 0.001;

        if (portalGroup) {
            const scalePulse = 1 + Math.sin(currentTime * 0.002) * 0.015;
            portalGroup.rotation.y += 0.003;
            portalGroup.scale.set(scalePulse, scalePulse, scalePulse);
        }

        if (portalGlass) {
            portalGlass.rotation.y += 0.0015;
            portalGlass.material.emissiveIntensity = 0.25 + Math.sin(currentTime * 0.0015) * 0.2;
        }

        if (portalFlares) {
            portalFlares.forEach((sprite, index) => {
                const angle = currentTime * 0.00065 * (index + 1) + index * Math.PI * 0.5;
                const radius = 7.2 + Math.sin(currentTime * 0.0009 + index) * 0.8;
                sprite.position.set(
                    Math.cos(angle) * radius,
                    Math.sin(angle * 1.8) * 1.5,
                    Math.sin(angle) * radius
                );
                const mouseEnergy = 1 - Math.min(1, Math.abs(mouseInfluenceX) + Math.abs(mouseInfluenceY));
                sprite.material.opacity = 0.25 + Math.abs(Math.sin(angle * 2.0)) * 0.5 + mouseEnergy * 0.3;
                sprite.material.rotation += 0.01;
            });
        }

        // Animate orbiting meshes
        orbitMeshes.forEach(mesh => {
            mesh.userData.angle += mesh.userData.speed;
            mesh.position.x = Math.cos(mesh.userData.angle) * mesh.userData.radius;
            mesh.position.z = Math.sin(mesh.userData.angle) * mesh.userData.radius;
            mesh.rotation.x += 0.01;
            mesh.rotation.y += 0.02;
        });

        // Scroll influence on camera
        const scrollInfluence = this.scrollY * 0.001;
        camera.position.y = scrollInfluence * 5;
        mainMesh.position.y = -scrollInfluence * 2;

        renderer.render(scene, camera);
    }

    // === STATE UPDATE METHODS ===

    updateVisionState(progress) {
        const particles = this.hero3D.particles.geometry.attributes.position;
        const positions = particles.array;
        const velocities = this.hero3D.particleVelocities;

        // Brownian motion with centripetal force
        for (let i = 0; i < positions.length; i += 3) {
            // Add velocity
            positions[i] += velocities[i];
            positions[i + 1] += velocities[i + 1];
            positions[i + 2] += velocities[i + 2];

            // Calculate distance from center
            const distance = Math.sqrt(
                positions[i] ** 2 +
                positions[i + 1] ** 2 +
                positions[i + 2] ** 2
            );

            // Centripetal force (subtle pull to center)
            if (distance > 35) {
                positions[i] *= 0.98;
                positions[i + 1] *= 0.98;
                positions[i + 2] *= 0.98;
            }

            // Add slight turbulence
            velocities[i] += (Math.random() - 0.5) * 0.001;
            velocities[i + 1] += (Math.random() - 0.5) * 0.001;
            velocities[i + 2] += (Math.random() - 0.5) * 0.001;

            // Damping to prevent excessive speed
            velocities[i] *= 0.99;
            velocities[i + 1] *= 0.99;
            velocities[i + 2] *= 0.99;
        }

        particles.needsUpdate = true;

        // Update connection lines
        this.updateConnectionLines();

        // Hide crystal mesh
        this.hero3D.mainMesh.material.opacity = 0;
        this.hero3D.glowMesh.material.opacity = 0;
        this.hero3D.coreMesh.material.opacity = 0;

        // Show particles with varied opacity
        this.hero3D.particles.material.opacity = 0.4 + Math.sin(progress * Math.PI * 2) * 0.2;

        // Hide pulse rings
        this.hero3D.pulseRings.forEach(ring => {
            ring.material.opacity = 0;
        });
    }

    updateRefinementState(progress) {
        const particles = this.hero3D.particles.geometry.attributes.position;
        const positions = particles.array;
        const targets = this.hero3D.particleTargets;
        const velocities = this.hero3D.particleVelocities;

        // Custom easing for organic-to-geometric transition
        const ease = this.crystallizationEase(progress);

        // Move particles toward crystal vertex positions
        for (let i = 0; i < positions.length; i += 3) {
            // Interpolate toward target
            const dx = targets[i] - positions[i];
            const dy = targets[i + 1] - positions[i + 1];
            const dz = targets[i + 2] - positions[i + 2];

            positions[i] += dx * ease * 0.08;
            positions[i + 1] += dy * ease * 0.08;
            positions[i + 2] += dz * ease * 0.08;

            // Reduce velocity as particles lock into place
            velocities[i] *= (1 - ease * 0.5);
            velocities[i + 1] *= (1 - ease * 0.5);
            velocities[i + 2] *= (1 - ease * 0.5);
        }

        particles.needsUpdate = true;

        // Fade in crystal wireframe
        this.hero3D.mainMesh.material.opacity = ease * 0.95;
        this.hero3D.coreMesh.material.opacity = ease * 0.15;
        this.hero3D.glowMesh.material.opacity = ease * 0.7;

        // Color transition from sage to lavender
        const startColor = new THREE.Color(0xA8D5BA);
        const endColor = new THREE.Color(0xB8B9D3);
        const currentColor = new THREE.Color().lerpColors(startColor, endColor, ease);

        this.hero3D.mainMesh.material.color = currentColor;
        this.hero3D.particles.material.color = currentColor;
        this.hero3D.connections.material.color = currentColor;

        // Particle opacity transitions
        this.hero3D.particles.material.opacity = 0.6 - (ease * 0.4);

        // Update connection lines with increasing structure
        this.updateConnectionLines(ease);

        // Energy pulse effect
        this.updateEnergyPulse(progress);
    }

    updateExcellenceState(progress) {
        const particles = this.hero3D.particles.geometry.attributes.position;
        const positions = particles.array;
        const targets = this.hero3D.particleTargets;

        // Keep particles locked to crystal vertices
        for (let i = 0; i < positions.length; i += 3) {
            positions[i] = targets[i];
            positions[i + 1] = targets[i + 1];
            positions[i + 2] = targets[i + 2];
        }

        particles.needsUpdate = true;

        // Fully formed crystal with breathing glow
        this.hero3D.mainMesh.material.opacity = 0.95;
        this.hero3D.coreMesh.material.opacity = 0.15;

        // Breathing glow effect
        const glowPulse = 0.6 + Math.sin(progress * Math.PI * 4) * 0.2;
        this.hero3D.glowMesh.material.opacity = glowPulse;

        // Maintain lavender color
        const lavenderColor = new THREE.Color(0xB8B9D3);
        this.hero3D.mainMesh.material.color = lavenderColor;
        this.hero3D.glowMesh.material.color = lavenderColor;

        // Hide particles
        this.hero3D.particles.material.opacity = 0.2;

        // Hide connections
        this.hero3D.connections.material.opacity = 0;

        // Camera subtle push in
        const zoomAmount = progress * 2;
        this.hero3D.camera.position.z = this.hero3D.baseCameraZ - zoomAmount;

        // Vertex highlights (subtle pulsing)
        this.updateVertexHighlights(progress);

        // Hide pulse rings
        this.hero3D.pulseRings.forEach(ring => {
            ring.material.opacity = 0;
        });
    }

    updateConnectionLines(structureFactor = 1.0) {
        const particles = this.hero3D.particles.geometry.attributes.position.array;
        const connections = this.hero3D.connections.geometry.attributes.position.array;
        const maxDistance = this.hero3D.maxConnectionDistance;
        const maxConnections = this.hero3D.maxConnections;

        let connectionIndex = 0;

        // Sample every Nth particle for performance
        const sampleRate = 3;

        for (let i = 0; i < particles.length; i += sampleRate * 3) {
            let connectionsForParticle = 0;

            // Check nearby particles
            for (let j = i + 3; j < particles.length && connectionsForParticle < maxConnections; j += sampleRate * 3) {
                const dx = particles[i] - particles[j];
                const dy = particles[i + 1] - particles[j + 1];
                const dz = particles[i + 2] - particles[j + 2];
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (distance < maxDistance) {
                    // Add connection line
                    connections[connectionIndex * 6] = particles[i];
                    connections[connectionIndex * 6 + 1] = particles[i + 1];
                    connections[connectionIndex * 6 + 2] = particles[i + 2];
                    connections[connectionIndex * 6 + 3] = particles[j];
                    connections[connectionIndex * 6 + 4] = particles[j + 1];
                    connections[connectionIndex * 6 + 5] = particles[j + 2];

                    connectionIndex++;
                    connectionsForParticle++;
                }
            }
        }

        this.hero3D.connections.geometry.attributes.position.needsUpdate = true;

        // Opacity based on state (VISION has visible connections, REFINEMENT increases)
        const baseOpacity = this.hero3D.currentState === this.hero3D.states.VISION ? 0.3 : 0.3 * structureFactor;
        this.hero3D.connections.material.opacity = baseOpacity;
    }

    updateEnergyPulse(progress) {
        // Energy pulse rings expanding from center
        this.hero3D.pulseRings.forEach((ring, index) => {
            const delay = index * 0.2;
            const adjustedProgress = (progress + delay) % 1;

            // Scale expands
            const scale = 1 + adjustedProgress * 10;
            ring.scale.set(scale, scale, scale);

            // Fade out as it expands
            ring.material.opacity = Math.max(0, 0.5 - adjustedProgress);

            // Rotate for visual interest
            ring.rotation.z += 0.01;
        });
    }

    updateVertexHighlights(progress) {
        // Subtle sequential vertex highlights
        // This creates a "scanning" effect across the crystal vertices
        const highlightIntensity = 0.2 + Math.sin(progress * Math.PI * 8) * 0.1;

        // Apply subtle scale pulsation to main mesh
        const scalePulse = 1 + Math.sin(progress * Math.PI * 2) * 0.01;
        this.hero3D.mainMesh.scale.set(scalePulse, scalePulse, scalePulse);
        this.hero3D.glowMesh.scale.set(scalePulse * 1.05, scalePulse * 1.05, scalePulse * 1.05);
        this.hero3D.coreMesh.scale.set(scalePulse * 0.95, scalePulse * 0.95, scalePulse * 0.95);
    }
    
    setupScrollAnimations() {
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
        
        // Update scroll position
        window.addEventListener('scroll', () => {
            this.scrollY = window.scrollY;
            this.updateNavbar();
        });
    }
    
    setupParticleSystem() {
        const particleContainer = document.getElementById('serviceParticles');
        if (!particleContainer) return;
        
        // Create floating particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
            particleContainer.appendChild(particle);
        }
    }
    
    setupAboutAnimation() {
        const canvas = document.getElementById('aboutCanvas');
        if (!canvas) return;
        
        // Setup Three.js scene for about section
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, canvas.width / canvas.height, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true });
        
        renderer.setSize(canvas.width, canvas.height);
        renderer.setClearColor(0x000000, 0);
        
        // Create 3D geometry
        const geometry = new THREE.IcosahedronGeometry(2, 1);
        const material = new THREE.MeshBasicMaterial({
            color: 0x7FA8A8,
            wireframe: true,
            transparent: true,
            opacity: 0.8
        });
        
        const icosahedron = new THREE.Mesh(geometry, material);
        scene.add(icosahedron);
        
        // Add particle system
        const particlesGeometry = new THREE.BufferGeometry();
        const particlesCount = 1000;
        const posArray = new Float32Array(particlesCount * 3);
        
        for (let i = 0; i < particlesCount * 3; i++) {
            posArray[i] = (Math.random() - 0.5) * 20;
        }
        
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        const particlesMaterial = new THREE.PointsMaterial({
            size: 0.005,
            color: 0x7FA8A8,
            transparent: true,
            opacity: 0.5
        });
        
        const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
        scene.add(particlesMesh);
        
        camera.position.z = 8;
        
        // Animation loop
        const animateAbout = () => {
            requestAnimationFrame(animateAbout);
            
            // Rotate main geometry
            icosahedron.rotation.x += 0.01;
            icosahedron.rotation.y += 0.005;
            
            // Rotate particles
            particlesMesh.rotation.x += 0.0005;
            particlesMesh.rotation.y += 0.0003;
            
            // Mouse interaction
            icosahedron.rotation.x += this.mouse.y * 0.00005;
            icosahedron.rotation.y += this.mouse.x * 0.00005;
            
            renderer.render(scene, camera);
        };
        
        animateAbout();
        
        // Handle resize
        const handleResize = () => {
            const width = canvas.clientWidth;
            const height = canvas.clientHeight;
            
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };
        
        window.addEventListener('resize', handleResize);
        handleResize(); // Initial size
    }
    
    setupNavbar() {
        const navbar = document.getElementById('navbar');
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const mobileMenu = document.getElementById('mobileMenu');

        // Toggle mobile menu
        if (mobileMenuBtn && mobileMenu) {
            mobileMenuBtn.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });

            // Close mobile menu when clicking a link
            mobileMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    mobileMenu.classList.add('hidden');
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
    
    updateNavbar() {
        const navbar = document.getElementById('navbar');
        
        if (this.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
    
    setupFormHandling() {
        const form = document.querySelector('form');
        if (!form) return;
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Show success message
            this.showNotification('Proposta enviada com sucesso! Entraremos em contato em breve.', 'success');
            
            // Reset form
            form.reset();
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg glass-effect glow-effect ${type === 'success' ? 'border-eterus-sage' : 'border-red-500'}`;
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-3">${type === 'success' ? '✓' : '!'}</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
    
    animate() {
        // Update hero 3D animation
        if (this.hero3D) {
            this.updateHero3D();
        }

        // Continue animation loop
        requestAnimationFrame(() => this.animate());
    }
}

// Advanced hover effects for service cards
class HoverEffects {
    constructor() {
        this.serviceCards = document.querySelectorAll('.service-card');
        this.setupHoverEffects();
    }
    
    setupHoverEffects() {
        this.serviceCards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                this.createHoverEffect(e.target);
            });
            
            card.addEventListener('mouseleave', (e) => {
                this.removeHoverEffect(e.target);
            });
            
            card.addEventListener('mousemove', (e) => {
                this.updateHoverEffect(e.target, e);
            });
        });
    }
    
    createHoverEffect(card) {
        const glow = document.createElement('div');
        glow.className = 'card-glow absolute inset-0 rounded-2xl pointer-events-none';
        glow.style.background = 'radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(184, 185, 211, 0.1) 0%, transparent 50%)';
        card.appendChild(glow);
        card.glowElement = glow;
    }
    
    removeHoverEffect(card) {
        if (card.glowElement) {
            card.removeChild(card.glowElement);
            card.glowElement = null;
        }
    }
    
    updateHoverEffect(card, e) {
        if (!card.glowElement) return;
        
        const rect = card.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        
        card.glowElement.style.setProperty('--mouse-x', x + '%');
        card.glowElement.style.setProperty('--mouse-y', y + '%');
    }
}

// Parallax effects for enhanced visual depth
class ParallaxEffects {
    constructor() {
        this.layers = document.querySelectorAll('[data-parallax]');
        this.setupParallax();
    }
    
    setupParallax() {
        window.addEventListener('scroll', () => {
            const scrollY = window.scrollY;
            
            this.layers.forEach(layer => {
                const speed = parseFloat(layer.dataset.parallax) || 0.5;
                const yPos = -(scrollY * speed);
                layer.style.transform = `translateY(${yPos}px)`;
            });
        });
    }
}

// Typing effect for hero text
class TypewriterEffect {
    constructor(element, texts, speed = 100) {
        this.element = element;
        this.texts = texts;
        this.speed = speed;
        this.textIndex = 0;
        this.charIndex = 0;
        this.isDeleting = false;
        
        this.type();
    }
    
    type() {
        const currentText = this.texts[this.textIndex];
        
        if (this.isDeleting) {
            this.element.textContent = currentText.substring(0, this.charIndex - 1);
            this.charIndex--;
        } else {
            this.element.textContent = currentText.substring(0, this.charIndex + 1);
            this.charIndex++;
        }
        
        let typeSpeed = this.speed;
        
        if (this.isDeleting) {
            typeSpeed /= 2;
        }
        
        if (!this.isDeleting && this.charIndex === currentText.length) {
            typeSpeed = 2000;
            this.isDeleting = true;
        } else if (this.isDeleting && this.charIndex === 0) {
            this.isDeleting = false;
            this.textIndex = (this.textIndex + 1) % this.texts.length;
            typeSpeed = 500;
        }
        
        setTimeout(() => this.type(), typeSpeed);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize splash screen
    const splash = new SplashScreen();

    // Initialize scroll progress bar
    const scrollProgress = new ScrollProgressBar();

    // Initialize magnetic buttons
    const magneticButtons = new MagneticButtons();

    // Initialize main animations
    const animations = new EterusAnimations();

    // Initialize hover effects
    const hoverEffects = new HoverEffects();

    // Initialize parallax effects
    const parallax = new ParallaxEffects();
    
    // Add parallax data attributes to elements
    document.querySelectorAll('.animate-float').forEach(el => {
        el.setAttribute('data-parallax', '0.3');
    });
    
    // Add smooth reveal animations
    const style = document.createElement('style');
    style.textContent = `
        .card-glow {
            transition: opacity 0.3s ease;
        }
        
        .service-card:hover .card-glow {
            opacity: 1;
        }
        
        .nav-blur.scrolled {
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(30px);
        }
        
        @media (max-width: 768px) {
            .process-step::before {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Add loading animation
    window.addEventListener('load', () => {
        document.body.classList.add('loaded');
        
        // Trigger initial animations
        setTimeout(() => {
            document.querySelectorAll('.section-reveal').forEach((el, index) => {
                setTimeout(() => {
                    el.classList.add('revealed');
                }, index * 100);
            });
        }, 500);
    });
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EterusAnimations, HoverEffects, ParallaxEffects, TypewriterEffect };
}
