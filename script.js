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
                temperature: 5,         // Temperatura finale molto bassa come richiesto
                density: 1.5
            }
        }
    },
    magma: {
        radius: 15, // Aumentato da 10 a 15 per dimensione maggiore
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
        horizontalForce: 25.0,    // Aumentato da 15.0 a 25.0 per controlli super-responsivi
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
    resistantRocks: {
        spawnRate: 0.15,          // Frequenza di spawn delle rocce resistenti
        density: 0.8,             // Densità man mano che si sale
        blockageStrength: 0.3,    // Ridotto da 0.95 a 0.3 per non fermare il gioco
        minSize: 25,              // Dimensione minima
        maxSize: 60,              // Dimensione massima
        color: '#1C1C1C'          // Nero scuro
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
        
        // Boost di velocità temporaneo
        magma.faultSpeedBoost = {
            active: true,
            duration: 2000, // 2 secondi
            startTime: Date.now(),
            multiplier: 2.5 // Boost di velocità 2.5x
        };
        
        // Trasformazione temporanea della forma alla faglia
        magma.faultShapeTransform = {
            active: true,
            duration: 1500, // 1.5 secondi
            startTime: Date.now(),
            angle: this.angle,
            intensity: 1.0
        };
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
        this.smokeParticles = []; // Particelle di fumo nero
        
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
        
        // Disegna il cielo sopra il cratere quando visibile
        if (this.crater.y < 100) { // Se il cratere è vicino alla superficie
            // Gradiente del cielo
            const skyGradient = ctx.createLinearGradient(0, 0, 0, this.crater.y);
            skyGradient.addColorStop(0, '#87CEEB'); // Azzurro cielo
            skyGradient.addColorStop(0.7, '#B0C4DE'); // Azzurro più chiaro
            skyGradient.addColorStop(1, '#F0F8FF'); // Quasi bianco verso l'orizzonte
            
            ctx.fillStyle = skyGradient;
            ctx.fillRect(0, 0, GAME_CONFIG.canvas.width, this.crater.y);
            
            // Aggiungi nuvole semplici
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            for (let i = 0; i < 3; i++) {
                const cloudX = (i * GAME_CONFIG.canvas.width / 3) + Math.sin(Date.now() * 0.0005 + i) * 20;
                const cloudY = 20 + i * 15;
                
                // Nuvola semplice con più cerchi
                for (let j = 0; j < 5; j++) {
                    const offsetX = (j - 2) * 15;
                    const radius = 15 + Math.sin(Date.now() * 0.001 + j) * 3;
                    ctx.beginPath();
                    ctx.arc(cloudX + offsetX, cloudY, radius, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }
        
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
            // Cratere normale con fumo nero
            craterGradient.addColorStop(0, '#4B0000');
            craterGradient.addColorStop(0.5, '#2F0000');
            craterGradient.addColorStop(1, '#1F0000');
            
            // Genera fumo nero che esce dal cratere
            this.generateSmoke(ctx);
        }
        
        ctx.fillStyle = craterGradient;
        ctx.beginPath();
        ctx.arc(this.crater.x, this.crater.y, this.crater.radius, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    generateSmoke(ctx) {
        // Genera nuove particelle di fumo
        if (Math.random() < 0.3) {
            this.smokeParticles.push({
                x: this.crater.x + (Math.random() - 0.5) * this.crater.radius,
                y: this.crater.y,
                vx: (Math.random() - 0.5) * 2,
                vy: -Math.random() * 3 - 1,
                size: Math.random() * 8 + 4,
                life: 1.0,
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.02
            });
        }
        
        // Aggiorna e disegna particelle esistenti
        this.smokeParticles = this.smokeParticles.filter(particle => {
            // Aggiorna posizione
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy -= 0.05; // Gravità leggera verso l'alto
            particle.vx *= 0.98; // Attrito
            particle.size += 0.1; // Crescita del fumo
            particle.life -= 0.008; // Dissolvenza
            particle.rotation += particle.rotationSpeed;
            
            // Disegna particella
            if (particle.life > 0) {
                ctx.save();
                ctx.translate(particle.x, particle.y);
                ctx.rotate(particle.rotation);
                
                const alpha = particle.life * 0.6;
                ctx.fillStyle = `rgba(30, 30, 30, ${alpha})`;
                ctx.beginPath();
                ctx.arc(0, 0, particle.size, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.restore();
                return true;
            }
            return false;
        });
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
        
        // Lava flows - flussi di lava che scendono lungo i lati del vulcano
        if (this.eruptionPhase === 'main' || this.eruptionPhase === 'explosive') {
            for (let i = 0; i < intensity * 3; i++) {
                this.lavaFlows.push({
                    x: this.crater.x + (Math.random() - 0.5) * this.crater.radius * 2,
                    y: this.crater.y + 10,
                    vx: (Math.random() - 0.5) * 2,
                    vy: Math.random() * 2 + 1,
                    width: Math.random() * 30 + 15,
                    height: Math.random() * 20 + 10,
                    life: 1,
                    temperature: 1100 + Math.random() * 200,
                    type: 'lavaflow'
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
        
        // Update lava flows
        this.lavaFlows = this.lavaFlows.filter(flow => {
            flow.x += flow.vx * dt;
            flow.y += flow.vy * dt;
            flow.vy += 3 * dt; // gravità per scorrimento verso il basso
            flow.vx *= 0.99; // attrito
            flow.life -= 0.3 * dt; // durata più lunga per flussi persistenti
            flow.temperature -= 20 * dt; // raffreddamento lento
            flow.width += 0.5 * dt; // si allarga mentre scorre
            return flow.life > 0 && flow.y < GAME_CONFIG.world.totalHeight;
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
        
        // Draw lava flows - flussi di lava che scendono dal cratere
        this.lavaFlows.forEach(flow => {
            ctx.save();
            ctx.globalAlpha = flow.life;
            
            // Gradiente per flusso di lava
            const flowGradient = ctx.createLinearGradient(flow.x - flow.width/2, flow.y, flow.x + flow.width/2, flow.y);
            flowGradient.addColorStop(0, 'rgba(139, 0, 0, 0.5)');
            flowGradient.addColorStop(0.5, '#FF4500');
            flowGradient.addColorStop(1, 'rgba(139, 0, 0, 0.5)');
            
            ctx.fillStyle = flowGradient;
            ctx.shadowColor = '#FF4500';
            ctx.shadowBlur = 10;
            
            // Disegna il flusso con forma organica
            ctx.beginPath();
            ctx.ellipse(flow.x, flow.y, flow.width/2, flow.height/2, 0, 0, Math.PI * 2);
            ctx.fill();
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

// Resistant Rock Obstacle Class - "ROCCIA RESISTENTE" (molto più resistente)
class ResistantRock {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = Math.random() * (GAME_CONFIG.resistantRocks.maxSize - GAME_CONFIG.resistantRocks.minSize) + GAME_CONFIG.resistantRocks.minSize;
        this.height = Math.random() * 30 + 20;
        this.color = GAME_CONFIG.resistantRocks.color;
        this.name = "ROCCIA RESISTENTE"; // Nome italiano dell'oggetto
        this.blockage = GAME_CONFIG.resistantRocks.blockageStrength;
        this.cracks = []; // Crepe dalla pressione del magma
        this.integrity = 1.0; // Integrità della roccia
    }
    
    draw(ctx) {
        // Safety check for valid coordinates and dimensions
        if (!isFinite(this.x) || !isFinite(this.y) || !isFinite(this.width) || !isFinite(this.height)) {
            return;
        }
        
        ctx.save();
        
        // Roccia nera principale con texture
        const gradient = ctx.createLinearGradient(this.x, this.y, this.x + this.width, this.y + this.height);
        gradient.addColorStop(0, '#2C2C2C');   // Grigio scuro
        gradient.addColorStop(0.3, '#1C1C1C'); // Nero
        gradient.addColorStop(0.7, '#0C0C0C'); // Nero profondo
        gradient.addColorStop(1, '#000000');   // Nero assoluto
        
        ctx.fillStyle = gradient;
        ctx.fillRect(this.x, this.y, this.width, this.height);
        
        // Bordo più scuro per enfatizzare resistenza
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.strokeRect(this.x, this.y, this.width, this.height);
        
        // Texture di resistenza - cristalli scuri
        ctx.fillStyle = '#444444';
        for (let i = 0; i < 8; i++) {
            const crystalX = this.x + Math.random() * this.width;
            const crystalY = this.y + Math.random() * this.height;
            const crystalSize = Math.random() * 3 + 1;
            ctx.beginPath();
            ctx.arc(crystalX, crystalY, crystalSize, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Mostra crepe se la roccia è danneggiata
        if (this.integrity < 1.0) {
            ctx.strokeStyle = `rgba(139, 69, 19, ${1 - this.integrity})`;
            ctx.lineWidth = 1;
            this.cracks.forEach(crack => {
                ctx.beginPath();
                ctx.moveTo(crack.x1, crack.y1);
                ctx.lineTo(crack.x2, crack.y2);
                ctx.stroke();
            });
        }
        
        ctx.restore();
    }
    
    checkCollision(magma) {
        return magma.x + magma.radius > this.x &&
               magma.x - magma.radius < this.x + this.width &&
               magma.y + magma.radius > this.y &&
               magma.y - magma.radius < this.y + this.height;
    }
    
    // Metodo per applicare pressione del magma
    applyMagmaPressure(pressure) {
        this.integrity -= pressure * 0.001; // Lenta erosione
        
        // Aggiungi crepe casuali quando danneggiata
        if (this.integrity < 0.8 && Math.random() < 0.1) {
            this.cracks.push({
                x1: this.x + Math.random() * this.width,
                y1: this.y + Math.random() * this.height,
                x2: this.x + Math.random() * this.width,
                y2: this.y + Math.random() * this.height
            });
        }
        
        return this.integrity > 0; // Ritorna false se distrutta
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
        
        // Proprietà per deformazioni dinamiche
        this.collisionDeformation = 1.0; // Fattore di deformazione da collisioni
        this.deformationDecay = 0.05; // Velocità di ritorno alla forma normale
        this.lastCollisionTime = 0;
        this.impactDirection = { x: 0, y: 0 }; // Direzione dell'ultimo impatto
        
        // Fluid dynamics properties
        this.density = 2.5;
        this.mass = Math.PI * this.radius * this.radius * this.density;
        
        // Proprietà per gestione rocce resistenti
        this.nearResistantRock = false;
        this.blockedByResistantRock = false;
    }
    
    update(controls, dt) {
        // Gestione boost di velocità da faglia geologica
        if (this.faultSpeedBoost && this.faultSpeedBoost.active) {
            const elapsed = Date.now() - this.faultSpeedBoost.startTime;
            if (elapsed >= this.faultSpeedBoost.duration) {
                this.faultSpeedBoost.active = false;
            }
        }
        
        // Gestione trasformazione di forma da faglia geologica
        if (this.faultShapeTransform && this.faultShapeTransform.active) {
            const elapsed = Date.now() - this.faultShapeTransform.startTime;
            if (elapsed >= this.faultShapeTransform.duration) {
                this.faultShapeTransform.active = false;
            } else {
                // Decadimento graduale dell'intensità
                this.faultShapeTransform.intensity = 1.0 - (elapsed / this.faultShapeTransform.duration);
            }
        }
        
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
        // Boost extra quando si è vicini a rocce resistenti
        let horizontalBoost = 1.0;
        if (this.nearResistantRock) {
            horizontalBoost = 2.5; // Boost 2.5x per aggirare ostacoli
        }
        if (this.blockedByResistantRock) {
            horizontalBoost = 4.0; // Boost 4x quando completamente bloccato
        }
        
        if (controls.left) {
            this.vx -= GAME_CONFIG.controls.horizontalForce * dt * horizontalBoost;
        }
        if (controls.right) {
            this.vx += GAME_CONFIG.controls.horizontalForce * dt * horizontalBoost;
        }
        
        // Apply space boost (with cooldown)
        if (controls.space && Date.now() - this.lastSpaceBoost > GAME_CONFIG.controls.spaceBoostCooldown) {
            this.vy -= GAME_CONFIG.controls.spaceBoostForce;
            this.lastSpaceBoost = Date.now();
            
            // Create boost particles
            this.createBoostParticles();
        }
        
        // Salta tutte le forze automatiche se bloccato da roccia resistente
        if (!this.blockedByResistantRock) {
            // Natural buoyancy (magma wants to rise)
            const buoyancy = this.composition.getBuoyancy();
            this.vy -= buoyancy * dt * 10.0; // Aumentato da 3.0 a 10.0 per azione esplosiva
            
            // Pressure gradient force (lower pressure above)
            const pressureGradient = (layerProps.pressure - 0.3) * 1.0; // Aumentato da 0.3 a 1.0
            this.vy -= pressureGradient * dt;
            
            // Apply viscosity (resistance to flow) with enhanced dampening
            const viscosity = this.composition.getViscosity() * layerProps.viscosity;
            
            // Improved viscosity dampening with more realistic physics
            this.vx -= this.vx * viscosity * dt * 0.05;
            this.vy -= this.vy * viscosity * dt * 0.03;
            
            // Additional legacy dampening for ultra-smooth movement
            this.vx *= Math.max(0.98, 1 - viscosity * 0.01 * dt);
            this.vy *= Math.max(0.99, 1 - viscosity * 0.005 * dt);
            
            // Add organic noise for more natural movement
            let noise = Math.sin(Date.now() * 0.001) * 0.5;
            this.vx += noise * 0.1 * dt;
            
            // Apply density effects
            const densityEffect = layerProps.density / this.density;
            this.vy += (densityEffect - 1) * 0.5 * dt; // Aumentato da 0.15 a 0.5
        }
        
        // Speed limits based on composition
        let maxSpeed = GAME_CONFIG.magma.maxSpeed / Math.max(0.5, this.composition.getViscosity());
        
        // Applica boost di velocità da faglia geologica
        if (this.faultSpeedBoost && this.faultSpeedBoost.active) {
            maxSpeed *= this.faultSpeedBoost.multiplier;
        }
        
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        
        if (speed > maxSpeed) {
            this.vx = (this.vx / speed) * maxSpeed;
            this.vy = (this.vy / speed) * maxSpeed;
        }
        
        // Update position
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        
        // Keep in horizontal bounds (world wrapping could be added)
        const prevX = this.x;
        this.x = Math.max(this.radius, Math.min(GAME_CONFIG.canvas.width - this.radius, this.x));
        
        // Deformazione da collisione con i bordi
        if (prevX !== this.x) {
            const impactForce = Math.abs(this.vx) / GAME_CONFIG.magma.maxSpeed;
            const dirX = this.x < GAME_CONFIG.canvas.width / 2 ? 1 : -1;
            this.applyCollisionDeformation(impactForce, dirX, 0);
        }
        
        // Update trail
        this.updateTrail();
        
        // Update collision deformation
        this.updateCollisionDeformation(dt);
    }
    
    // Metodo per gestire deformazioni da collisione
    updateCollisionDeformation(dt) {
        // Decadimento graduale della deformazione verso il normale
        if (this.collisionDeformation > 1.0) {
            this.collisionDeformation -= this.deformationDecay * dt;
            this.collisionDeformation = Math.max(1.0, this.collisionDeformation);
        } else if (this.collisionDeformation < 1.0) {
            this.collisionDeformation += this.deformationDecay * dt;
            this.collisionDeformation = Math.min(1.0, this.collisionDeformation);
        }
        
        // Decadimento della direzione di impatto
        this.impactDirection.x *= 0.95;
        this.impactDirection.y *= 0.95;
    }
    
    // Metodo per applicare deformazione da collisione (ridotta per smoothness)
    applyCollisionDeformation(impactForce, directionX, directionY) {
        // Intensità della deformazione ridotta per evitare spigoli
        const deformationIntensity = Math.min(1.5, 1.0 + impactForce * 0.3); // Ridotto da 2.0 e 0.5
        this.collisionDeformation = deformationIntensity;
        
        // Memorizza direzione dell'impatto per deformazione direzionale
        this.impactDirection.x = directionX * 0.5; // Ridotto l'effetto
        this.impactDirection.y = directionY * 0.5;
        
        this.lastCollisionTime = Date.now();
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
        // Aggiungi nuovo segmento della coda con proprietà estese
        this.trail.push({
            x: this.x,
            y: this.y,
            radius: this.radius,
            life: 1.0,
            temperature: this.composition.temperature,
            viscosity: this.composition.getViscosity(),
            vx: this.vx, // Velocità per calcolare deformazione
            vy: this.vy,
            deformation: 1.0, // Fattore di deformazione iniziale
            age: 0 // Età del segmento per effetti temporali
        });
        
        // Mantieni una coda molto più lunga (aumentato da 50 a 150)
        if (this.trail.length > 150) {
            this.trail.shift();
        }
        
        // Aggiorna ogni segmento della coda
        for (let i = 0; i < this.trail.length; i++) {
            let p = this.trail[i];
            
            // Incrementa età
            p.age += 0.016; // ~60fps
            
            // Decadimento vita più lento per coda più lunga
            p.life -= 0.008; // Ridotto da 0.02 a 0.008
            p.temperature -= 1; // Raffreddamento più lento
            
            // Calcola deformazione basata su movimento e posizione nella coda
            const speedMagnitude = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
            const maxSpeed = GAME_CONFIG.magma.maxSpeed;
            const speedRatio = Math.min(speedMagnitude / maxSpeed, 1);
            
            // Posizione relativa nella coda (0 = più vecchio, 1 = più nuovo)
            const positionRatio = i / this.trail.length;
            
            // Deformazione basata su velocità, viscosità e posizione
            const viscosityFactor = 1 / Math.max(0.1, p.viscosity);
            const movementDeformation = 1 + (speedRatio * 0.4 * viscosityFactor);
            const trailDeformation = 0.6 + (positionRatio * 0.4); // La coda si assottiglia
            
            // Oscillazioni organiche nella coda
            const wavePhase = p.age * 2 + i * 0.3;
            const organicWobble = 1 + Math.sin(wavePhase) * 0.15 * (1 - positionRatio);
            
            p.deformation = movementDeformation * trailDeformation * organicWobble;
            
            // Aggiorna velocità del segmento (inerzia della coda)
            if (i > 0) {
                const prev = this.trail[i - 1];
                const dampening = 0.95; // Smorzamento per effetto trascinamento
                p.vx = p.vx * dampening + prev.vx * (1 - dampening);
                p.vy = p.vy * dampening + prev.vy * (1 - dampening);
            }
        }
        
        // Rimuovi segmenti morti
        this.trail = this.trail.filter(p => p.life > 0);
    }
    
    drawOval(ctx, x, y, radiusX, radiusY) {
        ctx.beginPath();
        ctx.ellipse(x, y, radiusX, radiusY, 0, 0, Math.PI * 2);
        ctx.fill();
    }

    draw(ctx) {
        const layerProps = this.getLayerProperties();
        
        // Draw enhanced trail with deformation and movement response
        for (let i = 0; i < this.trail.length; i++) {
            const p = this.trail[i];
            ctx.save();
            
            // Enhanced color based on life, temperature and position
            const alpha = p.life * 0.8;
            const redIntensity = Math.min(255, 100 + p.temperature * 0.15);
            const greenIntensity = Math.floor(100 * p.life);
            
            // Gradiente di colore lungo la coda
            const positionRatio = i / this.trail.length;
            const heatAdjustment = 1 - (positionRatio * 0.3); // La coda si raffredda
            
            ctx.fillStyle = `rgba(${Math.floor(redIntensity * heatAdjustment)}, ${Math.floor(greenIntensity * heatAdjustment)}, 0, ${alpha})`;
            
            // Calcola dimensione con deformazione avanzata
            const baseSize = p.radius * p.life * p.deformation;
            
            // Deformazione direzionale basata sulla velocità
            const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
            if (speed > 0.5) {
                // Allungamento nella direzione del movimento
                const angle = Math.atan2(p.vy, p.vx);
                const stretchFactor = 1 + (speed / GAME_CONFIG.magma.maxSpeed) * 0.6;
                const compressFactor = 1 / Math.sqrt(stretchFactor);
                
                ctx.translate(p.x, p.y);
                ctx.rotate(angle);
                
                // Forma ellittica deformata
                ctx.beginPath();
                ctx.ellipse(0, 0, baseSize * stretchFactor, baseSize * compressFactor, 0, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.restore();
            } else {
                // Forma circolare per movimenti lenti
                ctx.beginPath();
                ctx.arc(p.x, p.y, baseSize, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }
        
        // Calculate speed and movement direction for fluid dynamics
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        const maxSpeed = GAME_CONFIG.magma.maxSpeed;
        const speedRatio = Math.min(speed / maxSpeed, 1);
        
        // Calculate fluid deformation based on velocity, viscosity, and geological depth
        const viscosity = this.composition.getViscosity();
        const fluidResistance = Math.max(0.1, Math.min(1, viscosity));
        
        // Get geological layer-based deformation factors (declare once here)
        const depthFactor = this.getDepthDeformationFactor();
        const temperatureFactor = Math.min(1.5, this.composition.temperature / 800); // Higher temp = more fluid
        
        // Enhanced deformation factors that change with depth, temperature and collisions
        const baseStretch = 1.5 + (depthFactor * 2.0); // More deformation in deeper layers
        const baseCompress = 0.3 + (depthFactor * 0.4); // More compression when fluid
        
        // Fattori di deformazione da collisione
        const collisionStretch = this.collisionDeformation;
        const impactAngle = Math.atan2(this.impactDirection.y, this.impactDirection.x);
        
        const stretchFactor = (1 + (speedRatio * baseStretch * (1 - fluidResistance) * temperatureFactor)) * collisionStretch;
        const compressFactor = 1 - (speedRatio * baseCompress * (1 - fluidResistance) * temperatureFactor);
        
        // Movement angle for directional deformation
        const moveAngle = Math.atan2(this.vy, this.vx);
        
        // Time-based variables for lava lamp animation with depth-dependent frequency (molto più lento)
        const baseFrequency = 0.0008 + (depthFactor * 0.001); // Ridotto drasticamente da 0.003-0.004
        const time = Date.now() * baseFrequency;
        const slowTime = Date.now() * (baseFrequency * 0.2); // Ancora più lento
        
        // Wobble intensity based on geological layer (molto più ampio e lento)
        const wobbleIntensity = 0.3 + (depthFactor * 0.4); // Ridotto ulteriormente per movimenti ampi
        
        // Apply organic squish effect using your enhanced code (super lento e ampio)
        let squish = 1 + Math.sin(Date.now() * 0.001) * 0.2; // Molto più lento e ampio
        
        ctx.save();
        
        // Enhanced glow intensity based on temperature with pulsing effect
        const glowIntensity = Math.min(60, this.composition.temperature / 15);
        const glowPulse = 1 + Math.sin(time * 2) * 0.3; // Pulsing glow
        ctx.shadowColor = this.getTemperatureColor();
        ctx.shadowBlur = glowIntensity * glowPulse;
        
        // Move to magma center for transformation
        ctx.translate(this.x, this.y);
        
        // Apply rotation based on movement direction for flowing effect
        if (speed > 1) {
            ctx.rotate(moveAngle + Math.sin(time) * 0.1); // Slight rotation wobble
        }
        
        // Create complex gradient for enhanced lava lamp effect
        const gradientRadius = this.radius * stretchFactor;
        const gradient = ctx.createRadialGradient(
            -gradientRadius * 0.3 + Math.sin(time * 1.5) * gradientRadius * 0.1, // Moving light spot
            -gradientRadius * 0.2 + Math.cos(time * 1.2) * gradientRadius * 0.1, 
            0,
            0, 0, gradientRadius * 1.2 // Larger gradient for softer edges
        );
        
        // Multi-layered gradient for realistic lava look with smoother transitions
        const tempColor = this.getTemperatureColor();
        const baseTemp = this.composition.temperature;
        
        if (baseTemp > 1000) {
            // Very hot - bright core with dynamic inner light
            gradient.addColorStop(0, '#FFFFFF');      // White hot center
            gradient.addColorStop(0.15, '#FFFF99');   // Bright yellow
            gradient.addColorStop(0.3, '#FFD700');    // Gold
            gradient.addColorStop(0.5, '#FF8C00');    // Orange
            gradient.addColorStop(0.7, '#FF4500');    // Red
            gradient.addColorStop(0.85, '#DC143C');   // Crimson
            gradient.addColorStop(1, '#8B0000');      // Dark red edge
        } else if (baseTemp > 800) {
            // Hot - golden core with smooth transitions
            gradient.addColorStop(0, '#FFD700');      // Gold center
            gradient.addColorStop(0.2, '#FFA500');    // Orange
            gradient.addColorStop(0.4, '#FF8C00');    // Dark orange
            gradient.addColorStop(0.6, '#FF4500');    // Red-orange
            gradient.addColorStop(0.8, '#DC143C');    // Crimson
            gradient.addColorStop(1, '#8B0000');      // Dark red edge
        } else {
            // Cooler - red core with subtle variations
            gradient.addColorStop(0, '#FF6347');      // Tomato center
            gradient.addColorStop(0.3, '#FF4500');    // Orange-red
            gradient.addColorStop(0.6, '#DC143C');    // Crimson
            gradient.addColorStop(0.8, '#8B0000');    // Dark red
            gradient.addColorStop(1, '#4B0000');      // Very dark edge
        }
        
        // Draw enhanced fluid blob with lava lamp organic shape
        ctx.fillStyle = gradient;
        ctx.beginPath();
        
        // Create highly organic, lava lamp shape using more control points for ultra-smooth curves
        const points = 32; // Aumentato da 24 a 32 per curves più fluide
        const angleStep = (Math.PI * 2) / points;
        
        // Multiple wave frequencies for complex organic shape - molto più lente
        const wave1Freq = 2 + (depthFactor * 1); // Ridotto drasticamente per onde lente
        const wave2Freq = 3 + (depthFactor * 1.5); // Molto più lento
        const wave3Freq = 4 + (depthFactor * 2); // Più lento
        
        for (let i = 0; i <= points; i++) {
            const angle = i * angleStep;
            
            // Calculate radius with complex organic variation
            let radiusVariation = this.radius;
            
            // Apply stretching in movement direction
            if (Math.abs(Math.cos(angle)) > Math.abs(Math.sin(angle))) {
                // Horizontal stretching based on movement
                radiusVariation *= stretchFactor;
            } else {
                // Vertical compression
                radiusVariation *= compressFactor;
            }
            
            // Multiple layers of organic wobble for lava lamp effect - super lente e ampie
            const primaryWobble = Math.sin(angle * wave1Freq + time) * 0.25 * wobbleIntensity; // Aumentato per ampiezza
            const secondaryWobble = Math.sin(angle * wave2Freq + slowTime * 2) * 0.15 * wobbleIntensity; // Più ampio
            const tertiaryWobble = Math.sin(angle * wave3Freq - time * 1.5) * 0.08 * wobbleIntensity; // Più ampio
            
            const totalWobble = (primaryWobble + secondaryWobble + tertiaryWobble) * this.radius * (1 - fluidResistance);
            radiusVariation += totalWobble;
            
            // Smoothing filter per evitare cambi bruschi
            const targetRadius = radiusVariation;
            if (i > 0) {
                const prevAngleTarget = ((i - 1) / points) * Math.PI * 2;
                const prevRadius = this.radius + (Math.sin(prevAngleTarget * wave1Freq + time) * 0.08 * wobbleIntensity * this.radius * (1 - fluidResistance));
                radiusVariation = radiusVariation * 0.8 + prevRadius * 0.2; // Smoothing blend
            }
            
            // Add surface tension effect with temperature and depth influence
            const tensionPhase = angle * 4 + time * 0.5;
            const tensionEffect = 1 + Math.sin(tensionPhase) * 0.08 * (1 - speedRatio) * temperatureFactor * (1 + depthFactor);
            radiusVariation *= tensionEffect;
            
            // Add buoyancy bulges (magma rises in blobs) - more pronounced in mantle
            if (this.vy < 0) { // Rising
                const buoyancyEffect = Math.sin(angle * 2 + time * 2) * 0.1 * Math.abs(this.vy) / 10 * (1 + depthFactor);
                radiusVariation += buoyancyEffect * this.radius;
            }
            
            // Aggiungi deformazione da collisione (ridotta per smoothness)
            if (this.collisionDeformation > 1.0) {
                // Deformazione direzionale basata sull'impatto - ridotta
                const impactInfluence = Math.cos(angle - impactAngle) * 0.15; // Ridotto da 0.3
                const collisionEffect = (this.collisionDeformation - 1.0) * impactInfluence;
                radiusVariation *= (1 + collisionEffect);
            }
            
            // Trasformazione di forma da faglia geologica
            if (this.faultShapeTransform && this.faultShapeTransform.active) {
                // Crea forma allungata nella direzione della faglia
                const faultAngle = this.faultShapeTransform.angle;
                const intensity = this.faultShapeTransform.intensity;
                
                // Allunga nella direzione della faglia, comprimi perpendicolarmente
                const angleDiff = Math.abs(((angle - faultAngle) % (Math.PI * 2)) - Math.PI);
                const isParallelToFault = angleDiff < Math.PI / 4 || angleDiff > (3 * Math.PI / 4);
                
                if (isParallelToFault) {
                    // Allunga lungo la faglia
                    radiusVariation *= (1 + intensity * 0.6);
                } else {
                    // Comprimi perpendicolarmente alla faglia
                    radiusVariation *= (1 - intensity * 0.3);
                }
            }
            
            // Calculate position with organic flowing curves and squish effect
            const x = Math.cos(angle) * radiusVariation * squish;
            const y = Math.sin(angle) * radiusVariation / squish;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else if (i === points) {
                // Close the path smoothly back to the start with improved curve
                const firstAngle = 0;
                const firstRadiusVar = this.radius;
                const firstX = Math.cos(firstAngle) * firstRadiusVar * squish;
                const firstY = Math.sin(firstAngle) * firstRadiusVar / squish;
                
                ctx.lineTo(firstX, firstY);
            } else {
                // Use simple lineTo for perfect smoothness
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        
        // Add multiple inner highlights for enhanced lava lamp realism
        if (baseTemp > 800) {
            // Primary highlight with flowing movement
            const highlightGradient = ctx.createRadialGradient(
                -this.radius * 0.4 + Math.sin(time * 1.8) * this.radius * 0.2,
                -this.radius * 0.3 + Math.cos(time * 1.3) * this.radius * 0.15,
                0,
                0, 0, this.radius * 0.8
            );
            highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
            highlightGradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.4)');
            highlightGradient.addColorStop(0.6, 'rgba(255, 255, 255, 0.1)');
            highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
            
            ctx.fillStyle = highlightGradient;
            ctx.beginPath();
            ctx.ellipse(0, 0, this.radius * 0.6 * stretchFactor, this.radius * 0.6 * compressFactor, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Secondary highlight for depth
            const secondaryHighlight = ctx.createRadialGradient(
                this.radius * 0.2 + Math.cos(time * 2.2) * this.radius * 0.1,
                this.radius * 0.3 + Math.sin(time * 1.7) * this.radius * 0.1,
                0,
                0, 0, this.radius * 0.5
            );
            secondaryHighlight.addColorStop(0, 'rgba(255, 255, 255, 0.4)');
            secondaryHighlight.addColorStop(0.5, 'rgba(255, 255, 255, 0.1)');
            secondaryHighlight.addColorStop(1, 'rgba(255, 255, 255, 0)');
            
            ctx.fillStyle = secondaryHighlight;
            ctx.beginPath();
            ctx.ellipse(0, 0, this.radius * 0.3, this.radius * 0.3, 0, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Enhanced gas bubbles with lava lamp style animation
        if (this.composition.gas > 0.05) {
            const bubbleCount = Math.floor(this.composition.gas * 20);
            for (let i = 0; i < bubbleCount; i++) {
                // Animated bubble positions
                const bubbleTime = time + i * 0.5;
                const bubbleAngle = (i / bubbleCount) * Math.PI * 2 + bubbleTime * 0.3;
                const bubbleDistance = (0.3 + Math.sin(bubbleTime * 1.5) * 0.2) * this.radius;
                
                // Bubble movement like in lava lamp
                const bubbleX = Math.cos(bubbleAngle) * bubbleDistance + Math.sin(bubbleTime * 2) * this.radius * 0.1;
                const bubbleY = Math.sin(bubbleAngle) * bubbleDistance + Math.cos(bubbleTime * 1.8) * this.radius * 0.1;
                const bubbleSize = (2 + Math.sin(bubbleTime * 3) * 1) * (1 + this.composition.gas);
                
                // Bubble gradient for 3D effect
                const bubbleGradient = ctx.createRadialGradient(
                    bubbleX - bubbleSize * 0.3, bubbleY - bubbleSize * 0.3, 0,
                    bubbleX, bubbleY, bubbleSize
                );
                bubbleGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
                bubbleGradient.addColorStop(0.6, 'rgba(255, 255, 255, 0.4)');
                bubbleGradient.addColorStop(1, 'rgba(255, 255, 255, 0.1)');
                
                ctx.fillStyle = bubbleGradient;
                ctx.beginPath();
                ctx.arc(bubbleX, bubbleY, bubbleSize, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        // Add enhanced viscosity indicator with subtle lava lamp flow
        if (viscosity < 0.5 && depthFactor > 0.3) { // Only show flow in deeper, more fluid layers
            const flowOpacity = 0.15 * (1 - viscosity) * depthFactor; // Reduced opacity
            ctx.strokeStyle = `rgba(255, 200, 100, ${flowOpacity})`;
            ctx.lineWidth = 0.5 + (depthFactor * 0.3); // Thinner lines
            
            // Only show subtle inner flow patterns
            const flowLines = 2 + Math.floor(depthFactor * 2);
            for (let i = 0; i < flowLines; i++) {
                const lineTime = time * (0.5 + i * 0.2 + depthFactor * 0.3); // Slower animation
                const rippleRadius = this.radius * (0.7 + i * 0.1); // Smaller, inner circles
                
                ctx.beginPath();
                ctx.arc(0, 0, rippleRadius, 0, Math.PI * 2);
                ctx.stroke();
            }
        }
        
        // Add flowing energy streaks for very hot magma - more intense in deeper layers
        if (baseTemp > 1000) {
            const streakOpacity = 0.6 * Math.sin(time * 3) * (1 + depthFactor * 0.5);
            ctx.strokeStyle = `rgba(255, 255, 0, ${Math.abs(streakOpacity)})`;
            ctx.lineWidth = 2 + (depthFactor * 1);
            
            const streakCount = 3 + Math.floor(depthFactor * 2);
            for (let i = 0; i < streakCount; i++) {
                const streakAngle = (i / streakCount) * Math.PI * 2 + time * (1 + depthFactor);
                const streakLength = this.radius * (1.5 + depthFactor);
                
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(
                    Math.cos(streakAngle) * streakLength,
                    Math.sin(streakAngle) * streakLength
                );
                ctx.stroke();
            }
        }
        
        // Add depth-specific particle effects
        if (depthFactor > 0.7) { // Deep mantle effects
            ctx.fillStyle = `rgba(255, 100, 0, ${0.3 * Math.sin(time * 4)})`;
            for (let i = 0; i < 5; i++) {
                const particleAngle = (i / 5) * Math.PI * 2 + time * 2;
                const particleDistance = this.radius * (1.2 + Math.sin(time + i) * 0.3);
                const particleX = Math.cos(particleAngle) * particleDistance;
                const particleY = Math.sin(particleAngle) * particleDistance;
                const particleSize = 2 + Math.sin(time * 3 + i) * 1;
                
                ctx.beginPath();
                ctx.arc(particleX, particleY, particleSize, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        ctx.restore();
        
        // Indicatore di vicinanza a rocce resistenti
        if (this.nearResistantRock || this.blockedByResistantRock) {
            ctx.save();
            
            // Colore diverso se completamente bloccato
            if (this.blockedByResistantRock) {
                ctx.strokeStyle = '#FF0000'; // Rosso per blocco totale
                ctx.lineWidth = 5;
            } else {
                ctx.strokeStyle = '#FFFF00'; // Giallo per vicinanza
                ctx.lineWidth = 3;
            }
            
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius + 15, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Frecce di direzione per movimento laterale (più grandi se bloccato)
            const arrowSize = this.blockedByResistantRock ? 12 : 8;
            const arrowY = this.y - this.radius - 25;
            
            // Freccia sinistra
            ctx.fillStyle = this.blockedByResistantRock ? '#FF0000' : '#FFFF00';
            ctx.beginPath();
            ctx.moveTo(this.x - 30, arrowY);
            ctx.lineTo(this.x - 30 - arrowSize, arrowY - arrowSize/2);
            ctx.lineTo(this.x - 30 - arrowSize, arrowY + arrowSize/2);
            ctx.closePath();
            ctx.fill();
            
            // Freccia destra
            ctx.beginPath();
            ctx.moveTo(this.x + 30, arrowY);
            ctx.lineTo(this.x + 30 + arrowSize, arrowY - arrowSize/2);
            ctx.lineTo(this.x + 30 + arrowSize, arrowY + arrowSize/2);
            ctx.closePath();
            ctx.fill();
            
            ctx.restore();
        }
        
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
    
    // Calculate deformation factor based on geological depth
    getDepthDeformationFactor() {
        // Returns 0 to 1 where 1 = maximum deformation (deep mantle), 0 = minimum (surface)
        if (this.y > GAME_CONFIG.world.mantleStart) {
            // Deep mantle: maximum fluidity and deformation
            const mantleDepth = (this.y - GAME_CONFIG.world.mantleStart) / (GAME_CONFIG.world.totalHeight - GAME_CONFIG.world.mantleStart);
            return 0.7 + (mantleDepth * 0.3); // 0.7 to 1.0
        } else if (this.y > GAME_CONFIG.world.crustStart) {
            // Mantle to crust transition: medium fluidity
            const transitionDepth = (this.y - GAME_CONFIG.world.crustStart) / (GAME_CONFIG.world.mantleStart - GAME_CONFIG.world.crustStart);
            return 0.4 + (transitionDepth * 0.3); // 0.4 to 0.7
        } else if (this.y > GAME_CONFIG.world.surfaceStart) {
            // Crust: lower fluidity
            const crustDepth = (this.y - GAME_CONFIG.world.surfaceStart) / (GAME_CONFIG.world.crustStart - GAME_CONFIG.world.surfaceStart);
            return 0.2 + (crustDepth * 0.2); // 0.2 to 0.4
        } else {
            // Surface: minimum fluidity, maximum viscosity
            const surfaceDepth = this.y / GAME_CONFIG.world.surfaceStart;
            return surfaceDepth * 0.2; // 0.0 to 0.2
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
        
        // Crescita del magma quando raccoglie acqua
        let growthFactor = amount * 0.02; // Crescita proporzionale all'acqua raccolta
        this.baseRadius += growthFactor;
        
        // Limita la crescita massima
        if (this.baseRadius > 35) {
            this.baseRadius = 35;
        }
        
        // Aggiorna anche il raggio dei trail per mantenere proporzioni
        this.updateTrailRadii();
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
    
    updateTrailRadii() {
        // Aggiorna i raggi dei trail per mantenere proporzioni con la crescita
        this.trail.forEach((segment, index) => {
            if (segment) {
                let fadeRatio = segment.life;
                segment.radius = this.baseRadius * fadeRatio * 0.8;
            }
        });
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
        this.resistantRocks = []; // Rocce nere resistenti
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
        this.resistantRocks = []; // Reset rocce resistenti
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
        
        // Generate resistant rocks (rocce nere) - più frequenti man mano che si sale
        for (let y = 0; y < worldHeight; y += 150) {
            // Densità crescente verso la superficie
            const surfaceProgress = (worldHeight - y) / worldHeight; // 0 = fondo, 1 = superficie
            const resistantRockChance = surfaceProgress * GAME_CONFIG.resistantRocks.density;
            
            if (Math.random() < resistantRockChance) {
                const numResistantRocks = Math.floor(Math.random() * 3) + 1; // 1-3 rocce resistenti
                for (let i = 0; i < numResistantRocks; i++) {
                    const x = Math.random() * (GAME_CONFIG.canvas.width - 100) + 50;
                    const rockY = y + Math.random() * 140;
                    this.resistantRocks.push(new ResistantRock(x, rockY));
                }
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
                // Calcola forza di impatto per deformazione
                const impactSpeed = Math.sqrt(this.magma.vx * this.magma.vx + this.magma.vy * this.magma.vy);
                const impactForce = impactSpeed / GAME_CONFIG.magma.maxSpeed;
                
                // Calcola direzione dell'impatto
                const dx = this.magma.x - (rock.x + rock.width/2);
                const dy = this.magma.y - (rock.y + rock.height/2);
                const distance = Math.sqrt(dx * dx + dy * dy);
                const dirX = distance > 0 ? dx / distance : 0;
                const dirY = distance > 0 ? dy / distance : 0;
                
                // Applica deformazione da collisione
                this.magma.applyCollisionDeformation(impactForce, dirX, dirY);
                
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
        
        // Check proximity to resistant rocks for enhanced controls
        this.magma.nearResistantRock = false;
        this.magma.blockedByResistantRock = false; // Reset blocco ogni frame
        this.resistantRocks.forEach(rock => {
            const dx = this.magma.x - (rock.x + rock.width/2);
            const dy = this.magma.y - (rock.y + rock.height/2);
            const distance = Math.sqrt(dx * dx + dy * dy);
            const proximityDistance = 80; // Distanza di rilevamento vicinanza
            
            if (distance < proximityDistance) {
                this.magma.nearResistantRock = true;
            }
        });
        
        // Check resistant rock collisions (molto più resistenti)
        this.resistantRocks = this.resistantRocks.filter(rock => {
            if (rock.checkCollision(this.magma)) {
                // Calcola forza di impatto
                const impactSpeed = Math.sqrt(this.magma.vx * this.magma.vx + this.magma.vy * this.magma.vy);
                const impactForce = impactSpeed / GAME_CONFIG.magma.maxSpeed;
                
                // Calcola direzione dell'impatto
                const dx = this.magma.x - (rock.x + rock.width/2);
                const dy = this.magma.y - (rock.y + rock.height/2);
                const distance = Math.sqrt(dx * dx + dy * dy);
                const dirX = distance > 0 ? dx / distance : 0;
                const dirY = distance > 0 ? dy / distance : 0;
                
                // Applica deformazione da collisione molto forte
                this.magma.applyCollisionDeformation(impactForce * 2, dirX, dirY);
                
                // STOP COMPLETO: ferma tutto il movimento quando colpisce roccia resistente
                this.magma.vx = 0;
                this.magma.vy = 0;
                
                // Segnala che il magma è bloccato da roccia resistente
                this.magma.blockedByResistantRock = true;
                
                // Raffreddamento drastico del magma
                this.magma.composition.temperature -= 50 * this.deltaTime;
                
                // Applica pressione alla roccia (può danneggiarla lentamente)
                const pressure = this.magma.composition.pressure * impactForce;
                const rockSurvives = rock.applyMagmaPressure(pressure);
                
                // Feedback message per roccia resistente
                this.showFeedback("Roccia Resistente!", rock.x, rock.y - 20, '#000000');
                
                return rockSurvives; // Rimuovi se distrutta
            }
            return true; // Mantieni se non colpita
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
        
        // Draw resistant rocks (rocce nere)
        this.resistantRocks.forEach(rock => rock.draw(this.ctx));
        
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
