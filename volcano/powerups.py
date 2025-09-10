import pygame
import random
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.collected = False
        self.animation_time = 0
        self.type = 'fumarole_gas'  # Gas delle fumarole
        
        # Movimento indipendente per simulare il gas che sale
        self.base_y = y
        self.base_x = x
        self.rise_speed = random.uniform(20, 40)  # Gas che sale lentamente
        self.wave_amplitude = random.uniform(5, 10)  # Ampiezza ondulazione
        self.wave_frequency = random.uniform(1.5, 2.5)  # Frequenza ondulazione
        
        # Particelle del gas
        self.particles = []
        for _ in range(8):
            self.particles.append({
                'x': random.uniform(-8, 8),
                'y': random.uniform(-8, 8),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.5, 1.5)
            })

    def update(self, dt):
        """Aggiorna il powerup."""
        self.animation_time += dt * 2
        
        # Movimento del gas che sale (indipendente)
        self.base_y -= self.rise_speed * dt
        
        # Ondulazione laterale
        self.y = self.base_y + math.sin(self.animation_time * self.wave_frequency) * self.wave_amplitude
        self.x = self.base_x + math.cos(self.animation_time * self.wave_frequency * 0.7) * (self.wave_amplitude * 0.5)
        
        # Aggiorna particelle
        for particle in self.particles:
            particle['y'] -= particle['speed'] * dt * 20
            particle['x'] += math.sin(self.animation_time + particle['x']) * 0.3
            
            # Ricicla particelle che escono
            if particle['y'] < -15:
                particle['y'] = 15
                particle['x'] = random.uniform(-8, 8)

    def draw(self, surface):
        """Disegna il powerup."""
        if -50 < self.y < SCREEN_HEIGHT + 50:
            # Disegna le particelle di gas prima
            for particle in self.particles:
                px = self.x + particle['x']
                py = self.y + particle['y']
                size = int(particle['size'])
                
                # Colore del gas vulcanico (giallo-verdastro)
                alpha = int(100 + 50 * math.sin(self.animation_time * 3 + particle['x']))
                color = (255, 255, 100, alpha)  # Giallo gas
                
                # Disegna particella con trasparenza
                gas_surface = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
                pygame.draw.circle(gas_surface, color, (size*2, size*2), size)
                surface.blit(gas_surface, (px - size*2, py - size*2))
            
            # Centro del powerup (sorgente del gas)
            center_color = (255, 200, 0)  # Oro per il centro
            glow_radius = int(self.radius + 3 * math.sin(self.animation_time * 4))
            
            # Effetto bagliore
            glow_surface = pygame.Surface((glow_radius*4, glow_radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*center_color, 50), (glow_radius*2, glow_radius*2), glow_radius)
            surface.blit(glow_surface, (self.x - glow_radius*2, self.y - glow_radius*2))
            
            # Centro solido
            pygame.draw.circle(surface, center_color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

    def check_collision(self, player):
        """Controlla collisione con il player."""
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)


class PowerUpManager:
    def __init__(self):
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(8, 15)  # Ogni 8-15 secondi
        
    def update(self, dt, dy):
        """Aggiorna tutti i powerup."""
        # Aggiorna timer di spawn
        self.spawn_timer += dt
        
        # Spawna nuovi powerup occasionalmente
        if self.spawn_timer >= self.spawn_interval:
            # Spawna powerup in posizione casuale dal basso
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = SCREEN_HEIGHT + 50  # Dal basso dello schermo
            powerup = PowerUp(x, y)
            self.powerups.append(powerup)
            
            # Reset timer con intervallo casuale
            self.spawn_timer = 0
            self.spawn_interval = random.uniform(10, 20)  # Ogni 10-20 secondi
        
        # Aggiorna powerup esistenti
        for powerup in self.powerups:
            # Movimento indipendente del powerup
            powerup.update(dt)
            # Scroll della mappa
            powerup.y += dy
        
        # Rimuovi powerup che sono usciti dallo schermo (in alto)
        self.powerups = [p for p in self.powerups if p.y > -100]
    
    def draw(self, screen):
        """Disegna tutti i powerup."""
        for powerup in self.powerups:
            powerup.draw(screen)
    
    def check_collisions(self, player):
        """Controlla collisioni con il player e restituisce powerup raccolti."""
        collected = []
        for powerup in self.powerups:
            if powerup.check_collision(player):
                powerup.collected = True
                collected.append(powerup)
                
                # Applica effetto del powerup
                if powerup.type == 'fumarole_gas':
                    # Boost di velocità verso l'alto
                    player.vy = min(player.vy - 300, -300)  # Boost potente
                    print("💨 Gas delle fumarole! Boost verso l'alto!")
        
        # Rimuovi powerup raccolti
        self.powerups = [p for p in self.powerups if not p.collected]
        return collected
    
    def reset(self):
        """Resetta il sistema dei powerup."""
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(8, 15)
