// Fallback animation for about section - guaranteed to work on all browsers
class AboutAnimationFallback {
    constructor() {
        this.canvas = document.getElementById('aboutCanvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.time = 0;
        
        this.init();
    }
    
    init() {
        // Check if canvas context is available
        if (!this.ctx) {
            console.warn('Canvas context not available for aboutCanvas');
            return;
        }

        this.resizeCanvas();
        this.createParticles();
        this.animate();

        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }
    
    createParticles() {
        const particleCount = 50;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: centerX + (Math.random() - 0.5) * 200,
                y: centerY + (Math.random() - 0.5) * 200,
                radius: Math.random() * 3 + 1,
                speed: Math.random() * 2 + 1,
                angle: (Math.PI * 2 * i) / particleCount,
                distance: Math.random() * 100 + 50,
                opacity: Math.random() * 0.8 + 0.2
            });
        }
    }
    
    animate() {
        // Safety check
        if (!this.ctx || !this.canvas) return;

        this.time += 0.02;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        // Draw central glowing circle
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, 60 + Math.sin(this.time * 2) * 10, 0, Math.PI * 2);
        this.ctx.fillStyle = `rgba(0, 212, 255, ${0.3 + Math.sin(this.time * 3) * 0.2})`;
        this.ctx.fill();
        
        // Draw outer ring
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, 100 + Math.sin(this.time * 1.5) * 15, 0, Math.PI * 2);
        this.ctx.strokeStyle = `rgba(0, 212, 255, ${0.5 + Math.sin(this.time * 2.5) * 0.3})`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Update and draw particles
        this.particles.forEach((particle, index) => {
            particle.angle += 0.02;
            particle.distance += Math.sin(this.time + index) * 0.5;
            
            particle.x = centerX + Math.cos(particle.angle) * particle.distance;
            particle.y = centerY + Math.sin(particle.angle) * particle.distance;
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(0, 212, 255, ${particle.opacity})`;
            this.ctx.fill();
            
            // Draw connections to nearby particles
            this.particles.forEach((otherParticle, otherIndex) => {
                if (index !== otherIndex) {
                    const dx = particle.x - otherParticle.x;
                    const dy = particle.y - otherParticle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < 80) {
                        const opacity = (80 - distance) / 80 * 0.3;
                        this.ctx.beginPath();
                        this.ctx.moveTo(particle.x, particle.y);
                        this.ctx.lineTo(otherParticle.x, otherParticle.y);
                        this.ctx.strokeStyle = `rgba(0, 212, 255, ${opacity})`;
                        this.ctx.lineWidth = 1;
                        this.ctx.stroke();
                    }
                }
            });
        });
        
        // Draw rotating geometric shapes
        this.ctx.save();
        this.ctx.translate(centerX, centerY);
        this.ctx.rotate(this.time * 0.5);
        
        // Triangle
        this.ctx.beginPath();
        this.ctx.moveTo(0, -40);
        this.ctx.lineTo(-35, 20);
        this.ctx.lineTo(35, 20);
        this.ctx.closePath();
        this.ctx.strokeStyle = `rgba(0, 212, 255, 0.6)`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        this.ctx.restore();
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize fallback animation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Try to initialize the fallback animation
    setTimeout(() => {
        new AboutAnimationFallback();
    }, 1000);
});