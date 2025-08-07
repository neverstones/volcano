// Game Configuration
const GAME_CONFIG = {
    canvas: {
        width: 800,
        height: 600
    },
    world: {
        // Total world height in pixels (much larger than canvas)
        totalHeight: 5000,      // 5000px total world
        mantleStart: 4500,      // Deep mantle starts at bottom
        mantleEnd: 2000,        // Mantle ends at 2000px
        crustStart: 2000,       // Crust starts
        crustEnd: 500,          // Crust ends
        surfaceStart: 500,      // Surface area
        surfaceEnd: 0,          // Top of world
        
        // Geological properties
        layers: {
            mantle: {
                color: '#8B0000',
                viscosity: 0.05,        // Very fluid in mantle
                pressure: 1.5,          // High pressure aids movement
                temperature: 1200,      // Very hot
                density: 0.8
            },
            crust: {
                color: '#654321',
                viscosity: 0.25,        // More viscous in crust
                pressure: 0.7,          // Lower pressure
                temperature: 800,       // Cooler
                density: 1.2
            },
            surface: {
                color: '#228B22',
                viscosity: 0.4,         // Highest viscosity near surface
                pressure: 0.3,          // Lowest pressure
                temperature: 400,       // Much cooler
                density: 1.5
            }
        }
    },
    magma: {
        radius: 10,
        maxSpeed: 200,  // Aumentato drasticamente da 20 a 200 per azione veloce!
        // Realistic magma properties
        composition: {
            silica: 0.5,            // SiO2 content (affects viscosity)
            water: 0.02,            // H2O content (aids melting)
            gas: 0.01              // Gas content (provides buoyancy)
        },
        meltingPoint: 600,
        minPressure: 0.4,
        color: '#ff4500',
        glowColor: '#ff8c42'
    },
    camera: {
        smoothing: 0.25,         // Aumentato per seguire l'azione veloce
        offsetY: 150             // Keep magma this far from center
    },
    controls: {
        horizontalForce: 8.0,    // Aumentato da 3.0 a 8.0 per controlli super-responsivi
        spaceBoostForce: 20.0,   // Aumentato da 8.0 a 20.0 per boost esplosivo
        spaceBoostCooldown: 200  // Ridotto da 500ms a 200ms per boost quasi continuo
    },
    particles: {
        maxCount: 120,
        fadeSpeed: 0.012
    },
    bubbles: {
        spawnRate: 0.04,
        waterContent: 0.2,       // Aumentato da 0.1 a 0.2 per effetto più significativo
        gasContent: 0.3          // Aumentato da 0.15 a 0.3 per più spinta
    },
    faults: {
        spawnRate: 0.6,
        pressureBoost: 1.5,      // Aumentato da 0.8 a 1.5 per boost più potente
        temperatureBoost: 400    // Aumentato da 200 a 400 per riscaldamento maggiore
    },
    volcano: {
        width: 200,
        height: 150,
        craterRadius: 40,
        eruptionDuration: 5000   // 5 seconds of eruption
    }
};

// Camera System for following magma
class Camera {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.targetX = 0;
        this.targetY = 0;
    }
    
    update(targetX, targetY) {
        // Set target position (center magma on screen with slight offset)
        this.targetX = targetX - GAME_CONFIG.canvas.width / 2;
        this.targetY = targetY - GAME_CONFIG.canvas.height / 2 + GAME_CONFIG.camera.offsetY;
        
        // Smooth camera movement
        this.x += (this.targetX - this.x) * GAME_CONFIG.camera.smoothing;
        this.y += (this.targetY - this.y) * GAME_CONFIG.camera.smoothing;
        
        // Constrain camera to world bounds
        this.x = Math.max(0, Math.min(this.x, 0)); // No horizontal scrolling for now
        this.y = Math.max(0, Math.min(this.y, GAME_CONFIG.world.totalHeight - GAME_CONFIG.canvas.height));
    }
    
    apply(ctx) {
        ctx.save();
        ctx.translate(-this.x, -this.y);
    }
    
    restore(ctx) {
        ctx.restore();
    }
    
    worldToScreen(x, y) {
        return {
            x: x - this.x,
            y: y - this.y
        };
    }
    
    screenToWorld(x, y) {
        return {
            x: x + this.x,
            y: y + this.y
        };
    }
}

// Enhanced Magma Composition and Physics
class MagmaComposition {
    constructor() {
        this.silica = GAME_CONFIG.magma.composition.silica;
        this.water = GAME_CONFIG.magma.composition.water;
        this.gas = GAME_CONFIG.magma.composition.gas;
        this.temperature = 1000; // Starting temperature
        this.pressure = 1.0;     // Starting pressure
    }
    
    // Calculate viscosity based on composition and conditions
    getViscosity() {
        let baseViscosity = 1.0;
        
        // Silica increases viscosity exponentially
        baseViscosity *= Math.pow(2, this.silica * 5);
        
        // Water dramatically reduces viscosity
        baseViscosity *= (1 / (1 + this.water * 20));
        
        // Temperature affects viscosity (Arrhenius equation simplified)
        baseViscosity *= Math.exp(8000 / Math.max(this.temperature, 400));
        
        return Math.max(0.01, Math.min(2.0, baseViscosity));
    }
    
    // Calculate buoyancy based on gas content and pressure
    getBuoyancy() {
        // Gas bubbles provide upward force, especially at lower pressures
        return this.gas * (2 - this.pressure) * 8.0; // Aumentato da 2.0 a 8.0 per movimento super dinamico
    }
    
    // Check if magma can continue melting and moving
    canMelt() {
        return this.temperature > GAME_CONFIG.magma.meltingPoint && 
               this.pressure > GAME_CONFIG.magma.minPressure;
    }
    
    // Update composition based on environment
    updateFromEnvironment(layerProps, dt) {
        // Temperature equilibration with surroundings
        const targetTemp = layerProps.temperature;
        this.temperature += (targetTemp - this.temperature) * 0.02 * dt;
        
        // Pressure from layer
        this.pressure += (layerProps.pressure - this.pressure) * 0.05 * dt;
        
        // Gas loss at low pressure (degassing)
        if (this.pressure < 0.5) {
            this.gas = Math.max(0, this.gas - 0.001 * dt);
        }
        
        // Water loss at high temperature
        if (this.temperature > 900) {
            this.water = Math.max(0, this.water - 0.0005 * dt);
        }
    }
    
    addWater(amount) {
        this.water = Math.min(0.15, this.water + amount);
    }
    
    addGas(amount) {
        this.gas = Math.min(0.25, this.gas + amount);
    }
    
    addHeat(amount) {
        this.temperature = Math.min(1300, this.temperature + amount);
    }
    
    increasePressure(amount) {
        this.pressure = Math.min(2.0, this.pressure + amount);
    }
}

// Game State Management
class GameState {
    constructor() {
        this.current = 'MENU';
        this.previous = null;
    }
    
    setState(newState) {
        this.previous = this.current;
        this.current = newState;
        this.updateScreens();
    }
    
    updateScreens() {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        const activeScreen = this.getScreenElement();
        if (activeScreen) {
            activeScreen.classList.add('active');
        }
    }
    
    getScreenElement() {
        const screenMap = {
            'MENU': 'menuScreen',
            'INSTRUCTIONS': 'instructionsScreen',
            'GAME': 'gameScreen',
            'PAUSE': 'pauseScreen',
            'GAME_OVER': 'gameOverScreen',
            'LEADERBOARD': 'leaderboardScreen'
        };
        
        return document.getElementById(screenMap[this.current]);
    }
}

// Particle System
class Particle {
    constructor(x, y, vx, vy, color, life = 1) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.color = color;
        this.life = life;
        this.maxLife = life;
        this.size = Math.random() * 4 + 2;
    }
    
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += 0.1; // gravity
        this.vx *= 0.99; // air resistance
        this.life -= GAME_CONFIG.particles.fadeSpeed;
        
        return this.life > 0;
    }
    
    draw(ctx) {
        // Safety check for valid coordinates and properties
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.size) || !isFinite(this.life) || !isFinite(this.maxLife)) {
            return;
        }
        
        const alpha = this.life / this.maxLife;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

// Water Pocket Class - "SORGENTE TERMALE" (reduces viscosity, aids melting)
class WaterPocket {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.radius = Math.random() * 12 + 8;
        this.collected = false;
        this.pulse = 0;
        this.waterContent = GAME_CONFIG.bubbles.waterContent;
        this.name = "SORGENTE TERMALE"; // Nome italiano dell'oggetto
    }
    
    update(dt) {
        this.pulse += 0.1 * dt;
        return true; // Water pockets are stationary
    }
    
    draw(ctx) {
        if (this.collected) return;
        
        // Safety check for valid coordinates
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.radius)) {
            return;
        }
        
        ctx.save();
        ctx.globalAlpha = 0.7 + Math.sin(this.pulse) * 0.2;
        
        // Water gradient
        const gradient = ctx.createRadialGradient(
            this.x - this.radius * 0.3, this.y - this.radius * 0.3, 0,
            this.x, this.y, this.radius
        );
        gradient.addColorStop(0, 'rgba(100, 200, 255, 0.9)');
        gradient.addColorStop(0.7, 'rgba(50, 150, 255, 0.7)');
        gradient.addColorStop(1, 'rgba(0, 100, 200, 0.5)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Water droplet effect
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.beginPath();
        ctx.arc(this.x - this.radius * 0.2, this.y - this.radius * 0.2, this.radius * 0.2, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    checkCollision(magma) {
        if (this.collected) return false;
        
        const dx = this.x - magma.x;
        const dy = this.y - magma.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        return distance < this.radius + magma.radius;
    }
}

// Gas Pocket Class - "BOLLA DI GAS" (provides buoyancy)
class GasPocket {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.radius = Math.random() * 10 + 6;
        this.collected = false;
        this.pulse = 0;
        this.gasContent = GAME_CONFIG.bubbles.gasContent;
        this.floatSpeed = Math.random() * 0.5 + 0.2;
        this.name = "BOLLA DI GAS"; // Nome italiano dell'oggetto
    }
    
    update(dt) {
        this.y -= this.floatSpeed * dt; // Gas bubbles rise slowly
        this.pulse += 0.15 * dt;
        
        // Remove if too high
        return this.y > -100;
    }
    
    draw(ctx) {
        if (this.collected) return;
        
        // Safety check for valid coordinates
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.radius)) {
            return;
        }
        
        ctx.save();
        ctx.globalAlpha = 0.6 + Math.sin(this.pulse) * 0.3;
        
        // Gas gradient
        const gradient = ctx.createRadialGradient(
            this.x - this.radius * 0.3, this.y - this.radius * 0.3, 0,
            this.x, this.y, this.radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        gradient.addColorStop(0.7, 'rgba(200, 200, 200, 0.6)');
        gradient.addColorStop(1, 'rgba(150, 150, 150, 0.4)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Multiple small bubbles inside
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        for (let i = 0; i < 3; i++) {
            const bubbleX = this.x + (Math.random() - 0.5) * this.radius;
            const bubbleY = this.y + (Math.random() - 0.5) * this.radius;
            const bubbleSize = Math.random() * 2 + 1;
            ctx.beginPath();
            ctx.arc(bubbleX, bubbleY, bubbleSize, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    }
    
    checkCollision(magma) {
        if (this.collected) return false;
        
        const dx = this.x - magma.x;
        const dy = this.y - magma.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        return distance < this.radius + magma.radius;
    }
}

// Enhanced Geological Fault Class - "FAGLIA VULCANICA"
class GeologicalFault {
    constructor(x, y, angle = 0) {
        this.x = x;
        this.y = y;
        this.width = 20 + Math.random() * 15;
        this.height = Math.random() * 150 + 100;
        this.angle = angle;
        this.active = false;
        this.glow = 0;
        this.particles = [];
        this.heatBoost = GAME_CONFIG.faults.temperatureBoost;
        this.pressureBoost = GAME_CONFIG.faults.pressureBoost;
        this.lastActivation = 0;
        this.name = "FAGLIA VULCANICA"; // Nome italiano dell'oggetto
    }
    
    update(dt) {
        // Update glow effect
        if (this.active) {
            this.glow = Math.min(1, this.glow + 0.08 * dt);
        } else {
            this.glow = Math.max(0, this.glow - 0.03 * dt);
        }
        
        // Deactivate after some time
        if (this.active && Date.now() - this.lastActivation > 3000) {
            this.active = false;
        }
        
        // Generate heat particles when active
        if (this.active && Math.random() < 0.4) {
            this.particles.push({
                x: this.x + (Math.random() - 0.5) * this.width,
                y: this.y + Math.random() * this.height,
                vx: (Math.random() - 0.5) * 3,
                vy: -Math.random() * 4 - 1,
                life: 1,
                size: Math.random() * 4 + 2,
                color: Math.random() > 0.5 ? '#FF6347' : '#FF4500'
            });
        }
        
        // Update fault particles
        this.particles = this.particles.filter(particle => {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.vy += 0.1 * dt; // slight gravity
            particle.life -= 0.015 * dt;
            return particle.life > 0;
        });
    }
    
    draw(ctx) {
        // Safety check for valid coordinates and properties
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.width) || !isFinite(this.height) || !isFinite(this.glow)) {
            return;
        }
        
        ctx.save();
        
        // Draw fault line
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);
        
        // Main fault with heat glow
        const gradient = ctx.createLinearGradient(-this.width/2, 0, this.width/2, 0);
        gradient.addColorStop(0, 'rgba(139, 69, 19, 0.6)'); // Brown rock
        gradient.addColorStop(0.3, `rgba(255, 99, 71, ${Math.max(0, Math.min(1, 0.4 + this.glow * 0.6))})`); // Heat
        gradient.addColorStop(0.7, `rgba(255, 69, 0, ${Math.max(0, Math.min(1, 0.6 + this.glow * 0.4))})`); // More heat
        gradient.addColorStop(1, 'rgba(139, 69, 19, 0.6)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(-this.width/2, 0, this.width, this.height);
        
        // Active state glow
        if (this.glow > 0) {
            ctx.shadowColor = '#FF4500';
            ctx.shadowBlur = 25 * this.glow;
            ctx.strokeStyle = `rgba(255, 69, 0, ${this.glow})`;
            ctx.lineWidth = 3;
            ctx.strokeRect(-this.width/2, 0, this.width, this.height);
            
            // Internal heat lines
            ctx.strokeStyle = `rgba(255, 215, 0, ${Math.max(0, Math.min(1, this.glow * 0.8))})`;
            ctx.lineWidth = 1;
            for (let i = 0; i < 3; i++) {
                const lineY = (this.height / 4) * (i + 1);
                ctx.beginPath();
                ctx.moveTo(-this.width/2 + 2, lineY);
                ctx.lineTo(this.width/2 - 2, lineY);
                ctx.stroke();
            }
        }
        
        ctx.restore();
        
        // Draw particles
        this.particles.forEach(particle => {
            ctx.save();
            ctx.globalAlpha = particle.life;
            ctx.fillStyle = particle.color;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        });
    }
    
    checkCollision(magma) {
        // Enhanced collision detection
        const dx = Math.abs(magma.x - this.x);
        const dy = magma.y - this.y;
        
        return dx < this.width/2 + magma.radius && 
               dy > -magma.radius && 
               dy < this.height + magma.radius;
    }
    
    activate() {
        this.active = true;
        this.lastActivation = Date.now();
    }
    
    applyEffects(magma) {
        // Geological effects on magma
        magma.addHeat(this.heatBoost);
        magma.increasePressure(this.pressureBoost);
        
        // Physical boost upward - boost esplosivo per gameplay dinamico
        magma.vy -= 15.0; // Aumentato da 5.0 a 15.0 per boost spettacolare!
    }
}

// Majestic Volcano Eruption System
class VolcanoStructure {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = GAME_CONFIG.volcano.width;
        this.height = GAME_CONFIG.volcano.height;
        this.crater = {
            x: x,
            y: y - this.height + 20,
            radius: GAME_CONFIG.volcano.craterRadius
        };
        this.erupting = false;
        this.eruptionIntensity = 0;
        this.eruptionTime = 0;
        this.eruptionDuration = GAME_CONFIG.volcano.eruptionDuration;
        
        // Eruption particle systems
        this.lavaFountain = [];
        this.pyroclasticFlow = [];
        this.ashCloud = [];
        this.lightningBolts = [];
        this.lavaFlows = [];
        
        this.eruptionPhase = 'initial'; // initial, main, explosive, declining
    }
    
    draw(ctx, camera) {
        // Draw volcano cone with realistic textures
        this.drawVolcanoCone(ctx);
        
        // Draw crater
        this.drawCrater(ctx);
        
        // Draw eruption if active
        if (this.erupting) {
            this.drawEruption(ctx, camera);
        }
    }
    
    drawVolcanoCone(ctx) {
        ctx.save();
        
        // Main volcano body with gradient
        const gradient = ctx.createLinearGradient(this.x - this.width/2, this.y, this.x + this.width/2, this.y);
        gradient.addColorStop(0, '#654321');
        gradient.addColorStop(0.3, '#8B4513');
        gradient.addColorStop(0.7, '#8B4513');
        gradient.addColorStop(1, '#654321');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(this.x - this.width/2, this.y);
        ctx.lineTo(this.x - this.crater.radius, this.crater.y);
        ctx.lineTo(this.x + this.crater.radius, this.crater.y);
        ctx.lineTo(this.x + this.width/2, this.y);
        ctx.closePath();
        ctx.fill();
        
        // Add rock texture
        ctx.fillStyle = '#5D4037';
        for (let i = 0; i < 15; i++) {
            const rockX = this.x + (Math.random() - 0.5) * this.width * 0.8;
            const rockY = this.y - Math.random() * this.height * 0.8;
            const rockSize = Math.random() * 8 + 3;
            ctx.beginPath();
            ctx.arc(rockX, rockY, rockSize, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    }
    
    drawCrater(ctx) {
        ctx.save();
        
        // Crater rim
        ctx.strokeStyle = '#4B0000';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(this.crater.x, this.crater.y, this.crater.radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // Crater interior
        const craterGradient = ctx.createRadialGradient(
            this.crater.x, this.crater.y, 0,
            this.crater.x, this.crater.y, this.crater.radius
        );
        
        if (this.erupting) {
            // Glowing crater during eruption
            craterGradient.addColorStop(0, '#FFD700');
            craterGradient.addColorStop(0.3, '#FF4500');
            craterGradient.addColorStop(0.7, '#8B0000');
            craterGradient.addColorStop(1, '#2F0000');
            
            // Crater glow effect
            ctx.shadowColor = '#FF4500';
            ctx.shadowBlur = 30;
        } else {
            craterGradient.addColorStop(0, '#4B0000');
            craterGradient.addColorStop(0.5, '#2F0000');
            craterGradient.addColorStop(1, '#1F0000');
        }
        
        ctx.fillStyle = craterGradient;
        ctx.beginPath();
        ctx.arc(this.crater.x, this.crater.y, this.crater.radius, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    startEruption() {
        this.erupting = true;
        this.eruptionTime = 0;
        this.eruptionIntensity = 0;
        this.eruptionPhase = 'initial';
        
        // Clear previous eruption particles
        this.lavaFountain = [];
        this.pyroclasticFlow = [];
        this.ashCloud = [];
        this.lightningBolts = [];
        this.lavaFlows = [];
    }
    
    updateEruption(dt) {
        if (!this.erupting) return;
        
        this.eruptionTime += dt;
        
        // Update eruption phases
        this.updateEruptionPhase();
        
        // Generate particles based on phase
        this.generateEruptionParticles();
        
        // Update existing particles
        this.updateEruptionParticles(dt);
        
        // Check if eruption should end
        if (this.eruptionTime > this.eruptionDuration) {
            this.erupting = false;
        }
    }
    
    updateEruptionPhase() {
        const progress = this.eruptionTime / this.eruptionDuration;
        
        if (progress < 0.1) {
            this.eruptionPhase = 'initial';
            this.eruptionIntensity = progress * 10;
        } else if (progress < 0.3) {
            this.eruptionPhase = 'main';
            this.eruptionIntensity = 1.0;
        } else if (progress < 0.6) {
            this.eruptionPhase = 'explosive';
            this.eruptionIntensity = 1.5;
        } else {
            this.eruptionPhase = 'declining';
            this.eruptionIntensity = Math.max(0, 1.5 * (1 - (progress - 0.6) / 0.4));
        }
    }
    
    generateEruptionParticles() {
        const intensity = this.eruptionIntensity;
        
        // Lava fountain
        for (let i = 0; i < intensity * 15; i++) {
            this.lavaFountain.push({
                x: this.crater.x + (Math.random() - 0.5) * this.crater.radius,
                y: this.crater.y,
                vx: (Math.random() - 0.5) * intensity * 8,
                vy: -Math.random() * intensity * 25 - 10,
                size: Math.random() * 6 + 3,
                life: 1,
                temperature: 1200 + Math.random() * 200,
                type: 'lava'
            });
        }
        
        // Ash cloud
        if (this.eruptionPhase === 'explosive') {
            for (let i = 0; i < intensity * 25; i++) {
                this.ashCloud.push({
                    x: this.crater.x + (Math.random() - 0.5) * 100,
                    y: this.crater.y,
                    vx: (Math.random() - 0.5) * 6,
                    vy: -Math.random() * 15 - 5,
                    size: Math.random() * 12 + 8,
                    life: 1,
                    opacity: Math.random() * 0.6 + 0.4,
                    type: 'ash'
                });
            }
        }
        
        // Pyroclastic flow
        if (this.eruptionPhase === 'main' || this.eruptionPhase === 'explosive') {
            for (let i = 0; i < intensity * 8; i++) {
                this.pyroclasticFlow.push({
                    x: this.crater.x + (Math.random() - 0.5) * 80,
                    y: this.crater.y,
                    vx: (Math.random() - 0.5) * 12,
                    vy: Math.random() * 3 + 2,
                    size: Math.random() * 20 + 15,
                    life: 1,
                    temperature: 700 + Math.random() * 300,
                    type: 'pyroclastic'
                });
            }
        }
        
        // Lightning bolts during explosive phase
        if (this.eruptionPhase === 'explosive' && Math.random() < 0.1) {
            this.lightningBolts.push({
                startX: this.crater.x + (Math.random() - 0.5) * 200,
                startY: this.crater.y - 100,
                endX: this.crater.x + (Math.random() - 0.5) * 300,
                endY: this.crater.y - 300,
                life: 0.3,
                intensity: Math.random() * 0.8 + 0.2
            });
        }
    }
    
    updateEruptionParticles(dt) {
        // Update lava fountain
        this.lavaFountain = this.lavaFountain.filter(particle => {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.vy += 15 * dt; // gravity
            particle.life -= 0.8 * dt;
            particle.temperature -= 50 * dt; // cooling
            return particle.life > 0 && particle.y < GAME_CONFIG.world.totalHeight;
        });
        
        // Update ash cloud
        this.ashCloud = this.ashCloud.filter(particle => {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.vx *= 0.98; // air resistance
            particle.vy *= 0.99;
            particle.life -= 0.3 * dt;
            particle.size += 0.5 * dt; // ash spreads
            return particle.life > 0;
        });
        
        // Update pyroclastic flow
        this.pyroclasticFlow = this.pyroclasticFlow.filter(particle => {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.vy += 5 * dt; // some gravity
            particle.life -= 0.6 * dt;
            particle.temperature -= 30 * dt;
            return particle.life > 0 && particle.y < GAME_CONFIG.world.totalHeight;
        });
        
        // Update lightning bolts
        this.lightningBolts = this.lightningBolts.filter(bolt => {
            bolt.life -= 3 * dt;
            return bolt.life > 0;
        });
    }
    
    drawEruption(ctx, camera) {
        ctx.save();
        
        // Draw pyroclastic flow
        this.pyroclasticFlow.forEach(particle => {
            ctx.save();
            ctx.globalAlpha = particle.life * 0.7;
            
            const tempColor = this.getTemperatureColor(particle.temperature);
            ctx.fillStyle = tempColor;
            ctx.shadowColor = tempColor;
            ctx.shadowBlur = 15;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        });
        
        // Draw lava fountain
        this.lavaFountain.forEach(particle => {
            ctx.save();
            ctx.globalAlpha = particle.life;
            
            const tempColor = this.getTemperatureColor(particle.temperature);
            ctx.fillStyle = tempColor;
            ctx.shadowColor = tempColor;
            ctx.shadowBlur = 20;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        });
        
        // Draw ash cloud
        this.ashCloud.forEach(particle => {
            ctx.save();
            ctx.globalAlpha = particle.life * particle.opacity;
            ctx.fillStyle = '#2F2F2F';
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        });
        
        // Draw lightning bolts
        this.lightningBolts.forEach(bolt => {
            ctx.save();
            ctx.globalAlpha = bolt.life * bolt.intensity;
            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 3;
            ctx.shadowColor = '#FFFFFF';
            ctx.shadowBlur = 15;
            
            ctx.beginPath();
            ctx.moveTo(bolt.startX, bolt.startY);
            
            // Jagged lightning path
            const segments = 5;
            for (let i = 1; i <= segments; i++) {
                const progress = i / segments;
                const x = bolt.startX + (bolt.endX - bolt.startX) * progress + (Math.random() - 0.5) * 30;
                const y = bolt.startY + (bolt.endY - bolt.startY) * progress;
                ctx.lineTo(x, y);
            }
            
            ctx.stroke();
            ctx.restore();
        });
        
        ctx.restore();
    }
    
    getTemperatureColor(temperature) {
        if (temperature > 1100) return '#FFFF00'; // White hot
        if (temperature > 900) return '#FFD700';  // Gold
        if (temperature > 700) return '#FF8C00';  // Dark orange
        if (temperature > 500) return '#FF4500';  // Orange red
        return '#8B0000';                         // Dark red
    }
    
    checkReached(magma) {
        const dx = magma.x - this.crater.x;
        const dy = magma.y - this.crater.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < this.crater.radius + magma.radius;
    }
}

// Rock Obstacle Class - "ROCCIA VULCANICA"
class RockObstacle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = Math.random() * 40 + 30;
        this.height = Math.random() * 30 + 20;
        this.color = '#654321';
        this.name = "ROCCIA VULCANICA"; // Nome italiano dell'oggetto
    }
    
    draw(ctx) {
        // Safety check for valid coordinates and dimensions
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.width) || !isFinite(this.height)) {
            return;
        }
        
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);
        
        // Add some texture
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(this.x + 5, this.y + 5, this.width - 10, this.height - 10);
    }
    
    checkCollision(magma) {
        return magma.x + magma.radius > this.x &&
               magma.x - magma.radius < this.x + this.width &&
               magma.y + magma.radius > this.y &&
               magma.y - magma.radius < this.y + this.height;
    }
}

// Enhanced Magma Player with Realistic Physics
class MagmaPlayer {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.radius = GAME_CONFIG.magma.radius;
        this.composition = new MagmaComposition();
        this.trail = [];
        this.lastSpaceBoost = 0;
        
        // Fluid dynamics properties
        this.density = 2.5;
        this.mass = Math.PI * this.radius * this.radius * this.density;
    }
    
    update(controls, dt) {
        // Get current layer properties
        const layerProps = this.getLayerProperties();
        
        // Update magma composition based on environment
        this.composition.updateFromEnvironment(layerProps, dt);
        
        // Check if magma can still move (hasn't solidified)
        if (!this.composition.canMelt()) {
            // Magma is solidifying - dramatically reduce movement
            this.vx *= 0.9;
            this.vy *= 0.9;
            return;
        }
        
        // Apply horizontal controls (left/right arrows)
        if (controls.left) {
            this.vx -= GAME_CONFIG.controls.horizontalForce * dt;
        }
        if (controls.right) {
            this.vx += GAME_CONFIG.controls.horizontalForce * dt;
        }
        
        // Apply space boost (with cooldown)
        if (controls.space && Date.now() - this.lastSpaceBoost > GAME_CONFIG.controls.spaceBoostCooldown) {
            this.vy -= GAME_CONFIG.controls.spaceBoostForce;
            this.lastSpaceBoost = Date.now();
            
            // Create boost particles
            this.createBoostParticles();
        }
        
        // Natural buoyancy (magma wants to rise)
        const buoyancy = this.composition.getBuoyancy();
        this.vy -= buoyancy * dt * 10.0; // Aumentato da 3.0 a 10.0 per azione esplosiva
        
        // Pressure gradient force (lower pressure above)
        const pressureGradient = (layerProps.pressure - 0.3) * 1.0; // Aumentato da 0.3 a 1.0
        this.vy -= pressureGradient * dt;
        
        // Apply viscosity (resistance to flow) - ulteriormente ridotto
        const viscosity = this.composition.getViscosity() * layerProps.viscosity;
        this.vx *= Math.max(0.98, 1 - viscosity * 0.01 * dt); // Quasi nessuna resistenza
        this.vy *= Math.max(0.99, 1 - viscosity * 0.005 * dt); // Quasi nessuna resistenza
        
        // Apply density effects
        const densityEffect = layerProps.density / this.density;
        this.vy += (densityEffect - 1) * 0.5 * dt; // Aumentato da 0.15 a 0.5
        
        // Speed limits based on composition
        const maxSpeed = GAME_CONFIG.magma.maxSpeed / Math.max(0.5, this.composition.getViscosity());
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        
        if (speed > maxSpeed) {
            this.vx = (this.vx / speed) * maxSpeed;
            this.vy = (this.vy / speed) * maxSpeed;
        }
        
        // Update position
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        
        // Keep in horizontal bounds (world wrapping could be added)
        this.x = Math.max(this.radius, Math.min(GAME_CONFIG.canvas.width - this.radius, this.x));
        
        // Update trail
        this.updateTrail();
    }
    
    createBoostParticles() {
        // Create dramatic boost effect particles
        for (let i = 0; i < 20; i++) {
            const angle = (Math.PI * 2 * i) / 20;
            const speed = Math.random() * 4 + 2;
            // Particles will be added by the game class
        }
    }
    
    updateTrail() {
        this.trail.push({
            x: this.x,
            y: this.y,
            life: 1,
            temperature: this.composition.temperature,
            viscosity: this.composition.getViscosity()
        });
        
        if (this.trail.length > 20) {
            this.trail.shift();
        }
        
        // Fade trail based on cooling
        this.trail.forEach(point => {
            point.life -= 0.05;
            point.temperature -= 2; // Cooling over time
        });
        this.trail = this.trail.filter(point => point.life > 0);
    }
    
    draw(ctx) {
        const layerProps = this.getLayerProperties();
        
        // Draw trail with temperature-based colors
        this.trail.forEach((point, index) => {
            ctx.save();
            ctx.globalAlpha = point.life * 0.6;
            
            // Color based on temperature
            let trailColor = '#8B0000'; // Dark red for cool
            if (point.temperature > 800) trailColor = '#FF4500'; // Orange for hot
            if (point.temperature > 1000) trailColor = '#FFD700'; // Gold for very hot
            
            ctx.fillStyle = trailColor;
            const size = (this.radius * 0.7) * point.life * (1 / Math.max(0.5, point.viscosity));
            ctx.beginPath();
            ctx.arc(point.x, point.y, size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        });
        
        // Calculate speed and movement direction for fluid dynamics
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        const maxSpeed = GAME_CONFIG.magma.maxSpeed;
        const speedRatio = Math.min(speed / maxSpeed, 1);
        
        // Calculate fluid deformation based on velocity and viscosity
        const viscosity = this.composition.getViscosity();
        const fluidResistance = Math.max(0.1, Math.min(1, viscosity));
        
        // Deformation factors for lava lamp effect
        const stretchFactor = 1 + (speedRatio * 1.5 * (1 - fluidResistance)); // More speed = more stretch
        const compressFactor = 1 - (speedRatio * 0.3 * (1 - fluidResistance)); // Compression perpendicular to movement
        
        // Movement angle for directional deformation
        const moveAngle = Math.atan2(this.vy, this.vx);
        
        ctx.save();
        
        // Glow intensity based on temperature
        const glowIntensity = Math.min(50, this.composition.temperature / 20);
        ctx.shadowColor = this.getTemperatureColor();
        ctx.shadowBlur = glowIntensity;
        
        // Move to magma center for transformation
        ctx.translate(this.x, this.y);
        
        // Apply rotation based on movement direction
        if (speed > 1) {
            ctx.rotate(moveAngle);
        }
        
        // Create complex gradient for lava lamp effect
        const gradientRadius = this.radius * stretchFactor;
        const gradient = ctx.createRadialGradient(
            -gradientRadius * 0.3, -gradientRadius * 0.2, 0, // Inner light spot (offset)
            0, 0, gradientRadius
        );
        
        // Multi-layered gradient for realistic lava look
        const tempColor = this.getTemperatureColor();
        const baseTemp = this.composition.temperature;
        
        if (baseTemp > 1000) {
            // Very hot - bright core
            gradient.addColorStop(0, '#FFFFFF');      // White hot center
            gradient.addColorStop(0.2, '#FFFF99');    // Bright yellow
            gradient.addColorStop(0.4, '#FFD700');    // Gold
            gradient.addColorStop(0.7, '#FF8C00');    // Orange
            gradient.addColorStop(0.9, '#FF4500');    // Red
            gradient.addColorStop(1, '#8B0000');      // Dark red edge
        } else if (baseTemp > 800) {
            // Hot - golden core
            gradient.addColorStop(0, '#FFD700');      // Gold center
            gradient.addColorStop(0.3, '#FF8C00');    // Orange
            gradient.addColorStop(0.6, '#FF4500');    // Red-orange
            gradient.addColorStop(0.8, '#DC143C');    // Crimson
            gradient.addColorStop(1, '#8B0000');      // Dark red edge
        } else {
            // Cooler - red core
            gradient.addColorStop(0, '#FF6347');      // Tomato center
            gradient.addColorStop(0.4, '#FF4500');    // Orange-red
            gradient.addColorStop(0.7, '#DC143C');    // Crimson
            gradient.addColorStop(0.9, '#8B0000');    // Dark red
            gradient.addColorStop(1, '#4B0000');      // Very dark edge
        }
        
        // Draw fluid blob with dynamic shape
        ctx.fillStyle = gradient;
        ctx.beginPath();
        
        // Create organic, fluid shape using multiple control points
        const points = 16; // Number of points for smooth curve
        const angleStep = (Math.PI * 2) / points;
        
        for (let i = 0; i <= points; i++) {
            const angle = i * angleStep;
            
            // Calculate radius with organic variation
            let radiusVariation = this.radius;
            
            // Apply stretching in movement direction
            if (Math.abs(Math.cos(angle)) > Math.abs(Math.sin(angle))) {
                // Horizontal stretching
                radiusVariation *= stretchFactor;
            } else {
                // Vertical compression
                radiusVariation *= compressFactor;
            }
            
            // Add organic wobble based on viscosity and time
            const wobbleTime = Date.now() * 0.003;
            const wobbleAmount = (1 - fluidResistance) * 0.1 * this.radius;
            const wobble = Math.sin(angle * 3 + wobbleTime) * wobbleAmount;
            radiusVariation += wobble;
            
            // Add surface tension effect
            const tensionEffect = 1 + Math.sin(angle * 4) * 0.05 * (1 - speedRatio);
            radiusVariation *= tensionEffect;
            
            const x = Math.cos(angle) * radiusVariation;
            const y = Math.sin(angle) * radiusVariation;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                // Use smooth curves for organic flow
                const prevAngle = (i - 1) * angleStep;
                const nextAngle = (i + 1) * angleStep;
                
                const controlDistance = radiusVariation * 0.2;
                const cpx = x - Math.cos(angle + Math.PI / 2) * controlDistance;
                const cpy = y - Math.sin(angle + Math.PI / 2) * controlDistance;
                
                ctx.quadraticCurveTo(cpx, cpy, x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        
        // Add inner highlights for more realism
        if (baseTemp > 800) {
            const highlightGradient = ctx.createRadialGradient(
                -this.radius * 0.4, -this.radius * 0.3, 0,
                0, 0, this.radius * 0.7
            );
            highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.6)');
            highlightGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.2)');
            highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
            
            ctx.fillStyle = highlightGradient;
            ctx.beginPath();
            ctx.ellipse(0, 0, this.radius * 0.6 * stretchFactor, this.radius * 0.6 * compressFactor, 0, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Draw gas bubbles if high gas content
        if (this.composition.gas > 0.05) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
            const bubbleCount = Math.floor(this.composition.gas * 15);
            for (let i = 0; i < bubbleCount; i++) {
                const bubbleAngle = (i / bubbleCount) * Math.PI * 2;
                const bubbleDistance = Math.random() * this.radius * 0.7;
                const bubbleX = Math.cos(bubbleAngle) * bubbleDistance;
                const bubbleY = Math.sin(bubbleAngle) * bubbleDistance;
                const bubbleSize = Math.random() * 3 + 1;
                
                ctx.beginPath();
                ctx.arc(bubbleX, bubbleY, bubbleSize, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        // Add viscosity indicator (surface ripples for low viscosity)
        if (viscosity < 0.5) {
            ctx.strokeStyle = `rgba(255, 200, 100, ${0.3 * (1 - viscosity)})`;
            ctx.lineWidth = 1;
            for (let i = 0; i < 3; i++) {
                const rippleRadius = this.radius * (0.7 + i * 0.15);
                ctx.beginPath();
                ctx.arc(0, 0, rippleRadius * stretchFactor, 0, Math.PI * 2);
                ctx.stroke();
            }
        }
        
        ctx.restore();
        
        // Draw composition indicators (moved outside the main transform)
        this.drawCompositionIndicators(ctx);
    }
    
    getTemperatureColor() {
        const temp = this.composition.temperature;
        if (temp < 600) return '#4B0000';      // Dark red (cooling/solid)
        if (temp < 800) return '#8B0000';      // Dark red
        if (temp < 1000) return '#FF4500';     // Orange red
        if (temp < 1200) return '#FF8C00';     // Dark orange
        return '#FFD700';                       // Gold (very hot)
    }
    
    drawCompositionIndicators(ctx) {
        // Small indicators for magma properties
        const startX = this.x - this.radius - 15;
        const startY = this.y - this.radius;
        
        // Water content indicator (blue)
        if (this.composition.water > 0.03) {
            ctx.fillStyle = `rgba(0, 100, 255, ${Math.max(0, Math.min(1, this.composition.water * 5))})`;
            ctx.fillRect(startX, startY, 3, 8);
        }
        
        // Gas content indicator (white)
        if (this.composition.gas > 0.02) {
            ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, Math.min(1, this.composition.gas * 4))})`;
            ctx.fillRect(startX + 4, startY, 3, 8);
        }
        
        // Pressure indicator (yellow)
        if (this.composition.pressure > 1.2) {
            ctx.fillStyle = `rgba(255, 255, 0, ${Math.max(0, Math.min(1, (this.composition.pressure - 1) * 2))})`;
            ctx.fillRect(startX + 8, startY, 3, 8);
        }
    }
    
    getLayerProperties() {
        if (this.y > GAME_CONFIG.world.mantleStart) {
            return GAME_CONFIG.world.layers.mantle;
        } else if (this.y > GAME_CONFIG.world.crustStart) {
            return GAME_CONFIG.world.layers.crust;
        } else {
            return GAME_CONFIG.world.layers.surface;
        }
    }
    
    getCurrentDepth() {
        return GAME_CONFIG.world.totalHeight - this.y;
    }
    
    getAltitude() {
        return this.y;
    }
    
    getSpeed() {
        return Math.sqrt(this.vx * this.vx + this.vy * this.vy);
    }
    
    // Methods for power-ups and environmental effects
    addWaterContent(amount) {
        this.composition.addWater(amount);
    }
    
    addGasContent(amount) {
        this.composition.addGas(amount);
    }
    
    addHeat(amount) {
        this.composition.addHeat(amount);
    }
    
    increasePressure(amount) {
        this.composition.increasePressure(amount);
    }
}

// Main Game Class with Enhanced Systems
class VolcanoGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.gameState = new GameState();
        this.camera = new Camera();
        
        this.magma = null;
        this.particles = [];
        this.waterPockets = [];
        this.gasPockets = [];
        this.rocks = [];
        this.faults = [];
        this.volcano = null;
        
        this.gameTime = 0;
        this.score = 0;
        this.deltaTime = 0;
        this.lastTime = 0;
        
        // Enhanced controls
        this.controls = {
            left: false,
            right: false,
            space: false
        };
        
        this.leaderboard = this.loadLeaderboard();
        
        // Array per messaggi di feedback
        this.feedbackMessages = [];
        
        this.setupEventListeners();
        this.generateLevel();
    }
    
    // Funzione per aggiungere messaggi di feedback
    showFeedback(message, x, y, color = '#FFD700') {
        this.feedbackMessages.push({
            text: message,
            x: x,
            y: y,
            color: color,
            life: 2.0,
            vy: -2,
            alpha: 1.0
        });
    }
    
    setupEventListeners() {
        // Menu buttons (existing code remains the same)
        document.getElementById('playBtn').addEventListener('click', () => this.startGame());
        document.getElementById('leaderboardBtn').addEventListener('click', () => this.showLeaderboard());
        document.getElementById('instructionsBtn').addEventListener('click', () => this.gameState.setState('INSTRUCTIONS'));
        
        // Instructions
        document.getElementById('backFromInstructions').addEventListener('click', () => this.gameState.setState('MENU'));
        
        // Game controls
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseGame());
        
        // Pause menu
        document.getElementById('resumeBtn').addEventListener('click', () => this.resumeGame());
        document.getElementById('restartBtn').addEventListener('click', () => this.startGame());
        document.getElementById('menuBtn').addEventListener('click', () => this.gameState.setState('MENU'));
        
        // Game over
        document.getElementById('saveScoreBtn').addEventListener('click', () => this.saveScore());
        document.getElementById('playAgainBtn').addEventListener('click', () => this.startGame());
        document.getElementById('viewLeaderboardBtn').addEventListener('click', () => this.showLeaderboard());
        
        // Leaderboard
        document.getElementById('backFromLeaderboard').addEventListener('click', () => this.gameState.setState('MENU'));
        
        // Enhanced keyboard controls
        document.addEventListener('keydown', (e) => {
            if (this.gameState.current !== 'GAME') return;
            
            switch(e.code) {
                case 'ArrowLeft':
                case 'KeyA':
                    this.controls.left = true;
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    this.controls.right = true;
                    e.preventDefault();
                    break;
                case 'Space':
                    this.controls.space = true;
                    e.preventDefault();
                    break;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            switch(e.code) {
                case 'ArrowLeft':
                case 'KeyA':
                    this.controls.left = false;
                    break;
                case 'ArrowRight':
                case 'KeyD':
                    this.controls.right = false;
                    break;
                case 'Space':
                    this.controls.space = false;
                    break;
            }
        });
        
        // Touch controls for mobile (simplified for the new control scheme)
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = this.canvas.getBoundingClientRect();
            const x = touch.clientX - rect.left;
            
            if (x < this.canvas.width / 3) {
                this.controls.left = true;
            } else if (x > (this.canvas.width * 2) / 3) {
                this.controls.right = true;
            } else {
                this.controls.space = true;
            }
        });
        
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.controls.left = false;
            this.controls.right = false;
            this.controls.space = false;
        });
    }
    
    startGame() {
        this.gameState.setState('GAME');
        this.resetGame();
        this.lastTime = performance.now();
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    resetGame() {
        // Start at bottom of world
        this.magma = new MagmaPlayer(GAME_CONFIG.canvas.width / 2, GAME_CONFIG.world.totalHeight - 50);
        this.particles = [];
        this.waterPockets = [];
        this.gasPockets = [];
        this.volcano = new VolcanoStructure(GAME_CONFIG.canvas.width / 2, 100);
        this.gameTime = 0;
        this.score = 0;
        this.camera = new Camera();
        this.generateLevel();
    }
    
    generateLevel() {
        this.rocks = [];
        this.faults = [];
        this.waterPockets = [];
        this.gasPockets = [];
        
        // Generate distributed across the entire world height
        const worldHeight = GAME_CONFIG.world.totalHeight;
        
        // Generate rock obstacles (more in crust)
        for (let y = 0; y < worldHeight; y += 200) {
            const numRocks = y < GAME_CONFIG.world.crustStart ? 4 : 2; // More rocks in crust
            for (let i = 0; i < numRocks; i++) {
                const x = Math.random() * (GAME_CONFIG.canvas.width - 100) + 50;
                const rockY = y + Math.random() * 180;
                this.rocks.push(new RockObstacle(x, rockY));
            }
        }
        
        // Generate geological faults (primarily in crust)
        for (let y = GAME_CONFIG.world.crustStart; y < GAME_CONFIG.world.mantleStart; y += 300) {
            for (let i = 0; i < 2; i++) {
                const x = Math.random() * (GAME_CONFIG.canvas.width - 100) + 50;
                const faultY = y + Math.random() * 250;
                const angle = (Math.random() - 0.5) * 0.3;
                this.faults.push(new GeologicalFault(x, faultY, angle));
            }
        }
        
        // Generate water pockets (help with melting)
        for (let y = 0; y < worldHeight; y += 400) {
            for (let i = 0; i < 3; i++) {
                const x = Math.random() * GAME_CONFIG.canvas.width;
                const waterY = y + Math.random() * 350;
                this.waterPockets.push(new WaterPocket(x, waterY));
            }
        }
        
        // Generate gas pockets (provide buoyancy)
        for (let y = GAME_CONFIG.world.mantleEnd; y < worldHeight; y += 300) {
            for (let i = 0; i < 2; i++) {
                const x = Math.random() * GAME_CONFIG.canvas.width;
                const gasY = y + Math.random() * 250;
                this.gasPockets.push(new GasPocket(x, gasY));
            }
        }
    }
    
    pauseGame() {
        this.gameState.setState('PAUSE');
    }
    
    resumeGame() {
        this.gameState.setState('GAME');
        this.lastTime = performance.now(); // Reset time to avoid frame skip
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    gameLoop(currentTime) {
        if (this.gameState.current !== 'GAME') return;
        
        // Calculate delta time
        this.deltaTime = Math.min((currentTime - this.lastTime) / 1000, 1/30); // Cap at 30 FPS minimum
        this.lastTime = currentTime;
        
        this.update();
        this.draw();
        
        requestAnimationFrame((time) => this.gameLoop(time));
    }
    
    update() {
        this.gameTime += this.deltaTime;
        
        // Update magma with new physics
        this.magma.update(this.controls, this.deltaTime);
        
        // Update camera to follow magma
        this.camera.update(this.magma.x, this.magma.y);
        
        // Check win condition - reached volcano
        if (this.volcano.checkReached(this.magma)) {
            this.volcano.startEruption();
            setTimeout(() => {
                this.endGame(true);
            }, GAME_CONFIG.volcano.eruptionDuration);
            return;
        }
        
        // Check lose conditions
        if (this.magma.y > GAME_CONFIG.world.totalHeight + 200) {
            this.endGame(false);
            return;
        }
        
        // Check if magma has solidified (can't melt anymore)
        if (!this.magma.composition.canMelt()) {
            setTimeout(() => {
                this.endGame(false);
            }, 2000); // Give 2 seconds to show solidification
        }
        
        // Update volcano eruption
        this.volcano.updateEruption(this.deltaTime);
        
        // Update water pockets
        this.waterPockets = this.waterPockets.filter(pocket => {
            pocket.update(this.deltaTime);
            
            // Check collision with magma
            if (pocket.checkCollision(this.magma)) {
                this.magma.addWaterContent(pocket.waterContent);
                pocket.collected = true;
                
                // Mostra feedback per la raccolta
                this.showFeedback(`+${pocket.name}!`, pocket.x, pocket.y - 30, '#00BFFF');
                this.showFeedback("VISCOSITÀ RIDOTTA!", pocket.x, pocket.y - 50, '#FFFFFF');
                
                // Add water absorption particles
                for (let i = 0; i < 12; i++) {
                    this.particles.push(new Particle(
                        pocket.x + (Math.random() - 0.5) * 30,
                        pocket.y + (Math.random() - 0.5) * 30,
                        (Math.random() - 0.5) * 4,
                        (Math.random() - 0.5) * 4,
                        '#00BFFF',
                        1.5
                    ));
                }
                
                return false;
            }
            
            return !pocket.collected;
        });
        
        // Update gas pockets
        this.gasPockets = this.gasPockets.filter(pocket => {
            const alive = pocket.update(this.deltaTime);
            
            // Check collision with magma
            if (pocket.checkCollision(this.magma)) {
                this.magma.addGasContent(pocket.gasContent);
                pocket.collected = true;
                
                // Mostra feedback per la raccolta
                this.showFeedback(`+${pocket.name}!`, pocket.x, pocket.y - 30, '#F0F8FF');
                this.showFeedback("SPINTA VERSO L'ALTO!", pocket.x, pocket.y - 50, '#FFFFFF');
                
                // Add gas absorption particles
                for (let i = 0; i < 15; i++) {
                    this.particles.push(new Particle(
                        pocket.x + (Math.random() - 0.5) * 25,
                        pocket.y + (Math.random() - 0.5) * 25,
                        (Math.random() - 0.5) * 5,
                        -Math.random() * 6 - 2,
                        '#F0F8FF',
                        1.2
                    ));
                }
                
                return false;
            }
            
            return alive && !pocket.collected;
        });
        
        // Update geological faults
        this.faults.forEach(fault => {
            fault.update(this.deltaTime);
            
            // Check fault collision
            if (fault.checkCollision(this.magma)) {
                if (!fault.active) {
                    fault.activate();
                    fault.applyEffects(this.magma);
                    
                    // Mostra feedback per l'attivazione della faglia
                    this.showFeedback(`+${fault.name}!`, fault.x, fault.y - 30, '#FF6347');
                    this.showFeedback("BOOST TERMICO!", fault.x, fault.y - 50, '#FFD700');
                    this.showFeedback("LANCIO ESPLOSIVO!", fault.x, fault.y - 70, '#FF4500');
                    
                    // Add fault activation particles
                    for (let i = 0; i < 20; i++) {
                        this.particles.push(new Particle(
                            fault.x + (Math.random() - 0.5) * fault.width,
                            fault.y + Math.random() * fault.height,
                            (Math.random() - 0.5) * 6,
                            -Math.random() * 5 - 3,
                            '#FF6347',
                            1.5
                        ));
                    }
                }
            }
        });
        
        // Check rock collisions (more realistic fluid dynamics)
        this.rocks.forEach(rock => {
            if (rock.checkCollision(this.magma)) {
                // Rocks provide resistance but don't completely stop flow
                const resistance = 0.3 * this.deltaTime;
                this.magma.vx *= (1 - resistance);
                this.magma.vy *= (1 - resistance);
                
                // Cool the magma slightly
                this.magma.composition.temperature -= 10 * this.deltaTime;
                
                // Add rock interaction particles
                if (Math.random() < 0.1) {
                    for (let i = 0; i < 3; i++) {
                        this.particles.push(new Particle(
                            rock.x + Math.random() * rock.width,
                            rock.y + Math.random() * rock.height,
                            (Math.random() - 0.5) * 3,
                            (Math.random() - 0.5) * 3,
                            '#8B4513',
                            0.8
                        ));
                    }
                }
            }
        });
        
        // Add magma trail particles based on composition
        if (Math.random() < 0.5) {
            const tempColor = this.magma.getTemperatureColor();
            this.particles.push(new Particle(
                this.magma.x + (Math.random() - 0.5) * 20,
                this.magma.y + (Math.random() - 0.5) * 20,
                (Math.random() - 0.5) * 3,
                Math.random() * 3 + 1,
                tempColor,
                1.2
            ));
        }
        
        // Update particles
        this.particles = this.particles.filter(particle => particle.update());
        
        // Update feedback messages
        this.feedbackMessages = this.feedbackMessages.filter(msg => {
            msg.y += msg.vy;
            msg.life -= this.deltaTime;
            msg.alpha = msg.life / 2.0;
            return msg.life > 0;
        });
        
        // Limit particle count for performance
        if (this.particles.length > GAME_CONFIG.particles.maxCount) {
            this.particles = this.particles.slice(-GAME_CONFIG.particles.maxCount);
        }
        
        // Update UI
        this.updateUI();
    }

    draw() {
        // Clear canvas
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, GAME_CONFIG.canvas.width, GAME_CONFIG.canvas.height);
        
        // Apply camera transformation
        this.camera.apply(this.ctx);
        
        // Draw geological layers across the entire world
        this.drawGeologicalLayers();
        
        // Draw volcano
        this.volcano.draw(this.ctx, this.camera);
        
        // Draw layer boundaries
        this.drawLayerBoundaries();
        
        // Draw geological faults
        this.faults.forEach(fault => fault.draw(this.ctx));
        
        // Draw rocks
        this.rocks.forEach(rock => rock.draw(this.ctx));
        
        // Draw water pockets
        this.waterPockets.forEach(pocket => pocket.draw(this.ctx));
        
        // Draw gas pockets
        this.gasPockets.forEach(pocket => pocket.draw(this.ctx));
        
        // Draw particles
        this.particles.forEach(particle => particle.draw(this.ctx));
        
        // Draw magma
        this.magma.draw(this.ctx);
        
        // Draw feedback messages (with camera transform)
        this.feedbackMessages.forEach(msg => {
            this.ctx.save();
            this.ctx.globalAlpha = msg.alpha;
            this.ctx.fillStyle = msg.color;
            this.ctx.font = 'bold 16px Orbitron';
            this.ctx.textAlign = 'center';
            this.ctx.strokeStyle = '#000000';
            this.ctx.lineWidth = 3;
            this.ctx.strokeText(msg.text, msg.x, msg.y);
            this.ctx.fillText(msg.text, msg.x, msg.y);
            this.ctx.restore();
        });
        
        // Restore camera transformation
        this.camera.restore(this.ctx);
        
        // Draw UI elements (not affected by camera)
        this.drawUI();
    }

    drawGeologicalLayers() {
        const worldHeight = GAME_CONFIG.world.totalHeight;
        const canvasWidth = GAME_CONFIG.canvas.width;
        
        // Surface layer (top)
        const surfaceGradient = this.ctx.createLinearGradient(0, 0, 0, GAME_CONFIG.world.surfaceStart);
        surfaceGradient.addColorStop(0, '#87CEEB'); // Sky blue
        surfaceGradient.addColorStop(0.7, '#228B22'); // Forest green
        surfaceGradient.addColorStop(1, '#8B7355'); // Light brown
        this.ctx.fillStyle = surfaceGradient;
        this.ctx.fillRect(0, 0, canvasWidth, GAME_CONFIG.world.surfaceStart);
        
        // Crust layer
        const crustHeight = GAME_CONFIG.world.crustStart - GAME_CONFIG.world.crustEnd;
        const crustGradient = this.ctx.createLinearGradient(0, GAME_CONFIG.world.crustEnd, 0, GAME_CONFIG.world.crustStart);
        crustGradient.addColorStop(0, '#8B7355'); // Light brown
        crustGradient.addColorStop(0.3, '#654321'); // Medium brown
        crustGradient.addColorStop(0.7, '#5D4037'); // Dark brown
        crustGradient.addColorStop(1, '#4A2C17'); // Very dark brown
        this.ctx.fillStyle = crustGradient;
        this.ctx.fillRect(0, GAME_CONFIG.world.crustEnd, canvasWidth, crustHeight);
        
        // Mantle layer
        const mantleHeight = GAME_CONFIG.world.mantleEnd - GAME_CONFIG.world.mantleStart;
        const mantleGradient = this.ctx.createLinearGradient(0, GAME_CONFIG.world.mantleStart, 0, GAME_CONFIG.world.mantleEnd);
        mantleGradient.addColorStop(0, '#4A2C17'); // Dark brown (transition)
        mantleGradient.addColorStop(0.2, '#8B0000'); // Dark red
        mantleGradient.addColorStop(0.6, '#B22222'); // Fire brick
        mantleGradient.addColorStop(1, '#DC143C'); // Crimson
        this.ctx.fillStyle = mantleGradient;
        this.ctx.fillRect(0, GAME_CONFIG.world.mantleStart, canvasWidth, -mantleHeight);
        
        // Deep mantle layer
        const deepMantleHeight = worldHeight - GAME_CONFIG.world.mantleStart;
        const deepMantleGradient = this.ctx.createLinearGradient(0, GAME_CONFIG.world.mantleStart, 0, worldHeight);
        deepMantleGradient.addColorStop(0, '#DC143C'); // Crimson
        deepMantleGradient.addColorStop(0.5, '#FF4500'); // Orange red
        deepMantleGradient.addColorStop(1, '#FF6347'); // Tomato (very hot)
        this.ctx.fillStyle = deepMantleGradient;
        this.ctx.fillRect(0, GAME_CONFIG.world.mantleStart, canvasWidth, deepMantleHeight);
        
        // Add some heat shimmer effects in mantle
        this.ctx.fillStyle = 'rgba(255, 140, 0, 0.1)';
        for (let i = 0; i < 40; i++) {
            const x = Math.random() * canvasWidth;
            const y = GAME_CONFIG.world.mantleStart + Math.random() * (worldHeight - GAME_CONFIG.world.mantleStart);
            const size = Math.random() * 40 + 20;
            this.ctx.beginPath();
            this.ctx.arc(x, y, size, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    drawLayerBoundaries() {
        // Surface boundary
        this.ctx.strokeStyle = '#228B22';
        this.ctx.lineWidth = 4;
        this.ctx.setLineDash([]);
        this.ctx.beginPath();
        this.ctx.moveTo(0, GAME_CONFIG.world.surfaceStart);
        this.ctx.lineTo(GAME_CONFIG.canvas.width, GAME_CONFIG.world.surfaceStart);
        this.ctx.stroke();
        
        // Crust-Mantle boundary (Moho)
        this.ctx.strokeStyle = '#FF4500';
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([15, 8]);
        this.ctx.beginPath();
        this.ctx.moveTo(0, GAME_CONFIG.world.crustStart);
        this.ctx.lineTo(GAME_CONFIG.canvas.width, GAME_CONFIG.world.crustStart);
        this.ctx.stroke();
        
        // Deep mantle boundary
        this.ctx.strokeStyle = '#FFD700';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([10, 5]);
        this.ctx.beginPath();
        this.ctx.moveTo(0, GAME_CONFIG.world.mantleStart);
        this.ctx.lineTo(GAME_CONFIG.canvas.width, GAME_CONFIG.world.mantleStart);
        this.ctx.stroke();
        
        // Reset line dash
        this.ctx.setLineDash([]);
    }

    drawUI() {
        // Layer information panel
        const layerProps = this.magma.getLayerProperties();
        
        // Background panel
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(10, 10, 220, 120);
        
        // Border
        this.ctx.strokeStyle = '#FF6B35';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(10, 10, 220, 120);
        
        // Text information
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 14px Orbitron';
        
        let layerName = 'MANTELLO PROFONDO';
        if (this.magma.y < GAME_CONFIG.world.crustStart) layerName = 'MANTELLO';
        if (this.magma.y < GAME_CONFIG.world.crustEnd) layerName = 'CROSTA';
        if (this.magma.y < GAME_CONFIG.world.surfaceStart) layerName = 'SUPERFICIE';
        
        this.ctx.fillText(`Strato: ${layerName}`, 20, 30);
        
        this.ctx.font = '12px Orbitron';
        this.ctx.fillText(`Altitudine: ${Math.round(GAME_CONFIG.world.totalHeight - this.magma.y)}m`, 20, 50);
        this.ctx.fillText(`Temperatura: ${Math.round(this.magma.composition.temperature)}°C`, 20, 70);
        this.ctx.fillText(`Pressione: ${this.magma.composition.pressure.toFixed(2)} atm`, 20, 90);
        this.ctx.fillText(`Viscosità: ${this.magma.composition.getViscosity().toFixed(2)}`, 20, 110);
        
        // Composition indicators
        this.ctx.fillStyle = '#00BFFF';
        this.ctx.fillRect(240, 20, 20, Math.max(2, this.magma.composition.water * 200));
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '10px Orbitron';
        this.ctx.fillText('H₂O', 242, 15);
        
        this.ctx.fillStyle = '#F0F8FF';
        this.ctx.fillRect(265, 20, 20, Math.max(2, this.magma.composition.gas * 100));
        this.ctx.fillText('Gas', 267, 15);
        
        // Controls help
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(10, GAME_CONFIG.canvas.height - 80, 300, 70);
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '12px Orbitron';
        this.ctx.fillText('Controlli:', 20, GAME_CONFIG.canvas.height - 60);
        this.ctx.fillText('← → : Movimento orizzontale', 20, GAME_CONFIG.canvas.height - 45);
        this.ctx.fillText('SPAZIO : Spinta verso l\'alto', 20, GAME_CONFIG.canvas.height - 30);
        this.ctx.fillText('Mobile: Tocca sinistra/destra/centro', 20, GAME_CONFIG.canvas.height - 15);
    }

    updateUI() {
        const altitude = Math.round(GAME_CONFIG.world.totalHeight - this.magma.y);
        const speed = Math.round(this.magma.getSpeed() * 10) / 10;
        const time = Math.round(this.gameTime);
        
        // Update main UI elements
        document.getElementById('depth').textContent = altitude;
        document.getElementById('speed').textContent = speed;
        document.getElementById('time').textContent = time;
        
        // Update progress bar based on altitude gained
        const progress = Math.min(100, (altitude / GAME_CONFIG.world.totalHeight) * 100);
        document.getElementById('progressFill').style.width = progress + '%';
    }
    
    endGame(victory) {
        const altitude = GAME_CONFIG.world.totalHeight - this.magma.y;
        const time = this.gameTime;
        
        if (victory) {
            this.score = Math.round(20000 + (10000 / Math.max(1, time)) + altitude * 3);
            document.getElementById('gameOverTitle').textContent = '🌋 ERUZIONE MAESTOSA!';
        } else {
            let reason = 'MAGMA DISPERSO';
            if (!this.magma.composition.canMelt()) {
                reason = 'MAGMA SOLIDIFICATO';
            }
            this.score = Math.round(altitude + (3000 / Math.max(1, time)));
            document.getElementById('gameOverTitle').textContent = `💀 ${reason}`;
        }
        
        document.getElementById('finalDepth').textContent = Math.round(altitude) + 'm di salita';
        document.getElementById('finalTime').textContent = Math.round(time);
        document.getElementById('finalScore').textContent = this.score;
        
        this.gameState.setState('GAME_OVER');
    }
    
    pauseGame() {
        this.gameState.setState('PAUSE');
    }
    
    saveScore() {
        const playerName = document.getElementById('playerName').value.trim();
        
        if (!playerName) {
            alert('Inserisci il tuo nome!');
            return;
        }
        
        const scoreEntry = {
            name: playerName,
            score: this.score,
            altitude: Math.round(GAME_CONFIG.world.totalHeight - this.magma.y),
            time: Math.round(this.gameTime),
            date: new Date().toLocaleDateString('it-IT')
        };
        
        this.leaderboard.push(scoreEntry);
        this.leaderboard.sort((a, b) => b.score - a.score);
        this.leaderboard = this.leaderboard.slice(0, 10); // Keep top 10
        
        this.saveLeaderboard();
        this.showLeaderboard();
    }
    
    showLeaderboard() {
        this.gameState.setState('LEADERBOARD');
        this.renderLeaderboard();
    }
    
    renderLeaderboard() {
        const list = document.getElementById('leaderboardList');
        list.innerHTML = '';
        
        if (this.leaderboard.length === 0) {
            list.innerHTML = '<p style="text-align: center; color: #cccccc;">Nessun punteggio ancora registrato</p>';
            return;
        }
        
        this.leaderboard.forEach((entry, index) => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            
            const medal = ['🥇', '🥈', '🥉'][index] || `${index + 1}°`;
            
            item.innerHTML = `
                <div class="leaderboard-rank">${medal}</div>
                <div class="leaderboard-name">${entry.name}</div>
                <div class="leaderboard-score">${entry.score} pts</div>
            `;
            
            list.appendChild(item);
        });
    }
    
    loadLeaderboard() {
        try {
            const saved = localStorage.getItem('vulcano_enhanced_leaderboard');
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.error('Error loading leaderboard:', e);
            return [];
        }
    }
    
    saveLeaderboard() {
        try {
            localStorage.setItem('vulcano_enhanced_leaderboard', JSON.stringify(this.leaderboard));
        } catch (e) {
            console.error('Error saving leaderboard:', e);
        }
    }
}

// Initialize enhanced game when page loads
window.addEventListener('load', () => {
    const game = new VolcanoGame();
});
