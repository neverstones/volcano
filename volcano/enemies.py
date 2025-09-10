import pygame
import random
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(6, 12)  # Dimensioni più varie
        self.velocity_y = random.uniform(40, 80)  # Velocità di caduta
        self.velocity_x = random.uniform(-15, 15)  # Movimento orizzontale
        self.animation_time = 0
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-3, 3)
        
        # Minerali della serie di Bowen
        mineral_types = [
            {'name': 'Olivina', 'color': (107, 142, 35), 'speed_mult': 1.2, 'damage': 20},     # Verde oliva
            {'name': 'Pirosseno', 'color': (34, 139, 34), 'speed_mult': 1.0, 'damage': 25},   # Verde foresta
            {'name': 'Plagioclasio', 'color': (220, 220, 220), 'speed_mult': 0.8, 'damage': 18}, # Grigio chiaro
            {'name': 'Quarzo', 'color': (255, 255, 255), 'speed_mult': 0.7, 'damage': 30},    # Bianco cristallino
            {'name': 'Ortoclasio', 'color': (255, 192, 203), 'speed_mult': 0.9, 'damage': 22}, # Rosa chiaro
            {'name': 'Biotite', 'color': (25, 25, 25), 'speed_mult': 1.1, 'damage': 15}       # Nero brillante
        ]
        
        self.mineral_data = random.choice(mineral_types)
        self.name = self.mineral_data['name']
        self.color = self.mineral_data['color']
        self.damage_seconds = self.mineral_data['damage']  # Secondi da sottrarre
        
        # Applica modificatore velocità
        self.velocity_y *= self.mineral_data['speed_mult']

    def update(self, dt):
        """Aggiorna il movimento del nemico."""
        # Movimento di caduta
        self.y += self.velocity_y * dt
        self.x += self.velocity_x * dt
        
        # Rotazione e oscillazione
        self.animation_time += dt * 3
        self.rotation += self.rotation_speed * dt
        self.x += math.sin(self.animation_time) * 0.3

    def draw(self, surface):
        """Disegna il nemico."""
        if -100 < self.y < SCREEN_HEIGHT + 100:
            # Crea una forma irregolare per il minerale
            points = []
            num_points = 8
            for i in range(num_points):
                angle = (2 * math.pi * i / num_points) + self.rotation
                # Raggio variabile per forma irregolare
                radius_variation = self.radius * (0.7 + 0.3 * math.sin(i * 2.5))
                point_x = self.x + radius_variation * math.cos(angle)
                point_y = self.y + radius_variation * math.sin(angle)
                points.append((int(point_x), int(point_y)))
            
            # Disegna il minerale
            pygame.draw.polygon(surface, self.color, points)
            
            # Bordo più scuro
            border_color = tuple(max(0, c - 30) for c in self.color)
            pygame.draw.polygon(surface, border_color, points, 2)
            
            # Effetto di lucentezza
            shine_x = int(self.x - self.radius // 3)
            shine_y = int(self.y - self.radius // 3)
            shine_radius = max(1, self.radius // 4)
            pygame.draw.circle(surface, (255, 255, 255, 150), (shine_x, shine_y), shine_radius)
            
            # Testo con nome del minerale sopra
            font = pygame.font.SysFont(None, 20)
            text = font.render(self.name, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.x, self.y - self.radius - 15))
            
            # Sfondo scuro per il testo
            bg_rect = text_rect.copy()
            bg_rect.inflate(4, 2)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
            
            surface.blit(text, text_rect)

    def check_collision(self, player):
        """Controlla collisione con il player."""
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)


class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(2, 4)  # Ridotto da 3-6 a 2-4 secondi
        
    def update(self, dt, dy):
        """Aggiorna tutti i nemici."""
        # Aggiorna timer di spawn
        self.spawn_timer += dt
        
        # Spawna nuovi nemici occasionalmente
        if self.spawn_timer >= self.spawn_interval:
            # Probabilità di spawn multiplo (30% di chance per 2-3 nemici)
            num_enemies = 1
            if random.random() < 0.3:
                num_enemies = random.randint(2, 3)
            
            for _ in range(num_enemies):
                # Spawna nemico da sopra lo schermo
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = -50 - random.randint(0, 30)  # Leggermente sparsi in altezza
                enemy = Enemy(x, y)
                self.enemies.append(enemy)
            
            # Reset timer con intervallo casuale
            self.spawn_timer = 0
            self.spawn_interval = random.uniform(2, 5)  # Ridotto da 4-8 a 2-5 secondi
        
        # Aggiorna nemici esistenti
        for enemy in self.enemies:
            # Fisica del nemico
            enemy.update(dt)
            # Scroll della mappa
            enemy.y += dy
        
        # Rimuovi nemici che sono usciti dallo schermo (in basso)
        self.enemies = [e for e in self.enemies if e.y < SCREEN_HEIGHT + 100]
    
    def draw(self, screen):
        """Disegna tutti i nemici."""
        for enemy in self.enemies:
            enemy.draw(screen)
    
    def check_collisions(self, player):
        """Controlla collisioni con il player."""
        for enemy in self.enemies:
            if enemy.check_collision(player):
                return enemy  # Restituisce il nemico colpito
        return None  # Nessuna collisione
    
    def reset(self):
        """Resetta il sistema dei nemici."""
        self.enemies = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(2, 4)
