import pygame
import random
import math
from constants import SCREEN_HEIGHT


class Collectible:
    def __init__(self, x, y, value=None):
        self.x = x
        self.y = y
        self.collected = False
        self.radius = 10
        self.animation_time = 0
        
        # Più varietà di collectibles con valori diversi
        collectible_types = [
            {'type': 'crystal', 'color': (0, 255, 255), 'value': 100, 'weight': 40},      # Cristallo - comune
            {'type': 'gem', 'color': (255, 0, 255), 'value': 150, 'weight': 30},         # Gemma - meno comune
            {'type': 'mineral', 'color': (255, 215, 0), 'value': 200, 'weight': 20},     # Minerale - raro
            {'type': 'diamond', 'color': (200, 200, 255), 'value': 300, 'weight': 8},    # Diamante - molto raro
            {'type': 'ruby', 'color': (220, 20, 60), 'value': 250, 'weight': 2}          # Rubino - rarissimo
        ]
        
        # Selezione pesata per rarità
        weights = [ct['weight'] for ct in collectible_types]
        selected = random.choices(collectible_types, weights=weights)[0]
        
        self.type = selected['type']
        self.base_color = selected['color']
        self.value = value if value is not None else selected['value']
        
        # Radius varia in base al valore
        if self.value >= 300:
            self.radius = 14  # Diamanti più grandi
        elif self.value >= 200:
            self.radius = 12  # Minerali medi
        else:
            self.radius = 10  # Cristalli e gemme normali

    def update(self, dt):
        self.animation_time += dt * 4

    def draw(self, surface, world_offset=0):
        if self.collected:
            return

        if -50 < self.y < SCREEN_HEIGHT + 50:
            # Rotazione e scala
            rotation = self.animation_time
            scale = 0.9 + 0.1 * math.sin(self.animation_time * 2)

            color = self.base_color
            radius = int(self.radius * scale)

            # Forma diversa in base al tipo
            if self.type == 'diamond':
                # Diamante - forma a losanga
                points = []
                for i in range(4):
                    angle = rotation + i * math.pi / 2
                    x = self.x + radius * math.cos(angle)
                    y = self.y + radius * math.sin(angle) * 0.7
                    points.append((x, y))
                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 3)
            
            elif self.type == 'ruby':
                # Rubino - forma ottagonale
                points = []
                for i in range(8):
                    angle = rotation + i * math.pi / 4
                    r = radius if i % 2 == 0 else radius * 0.8
                    x = self.x + r * math.cos(angle)
                    y = self.y + r * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 2)
            
            else:
                # Stella brillante per crystal, gem, mineral
                points = []
                for i in range(8):
                    angle = rotation + i * math.pi / 4
                    if i % 2 == 0:
                        r = radius
                    else:
                        r = radius * 0.5

                    x = self.x + r * math.cos(angle)
                    y = self.y + r * math.sin(angle)
                    points.append((x, y))

                pygame.draw.polygon(surface, color, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 2)

            # Particelle scintillanti - più intense per oggetti rari
            particle_count = 3
            if self.type == 'diamond':
                particle_count = 6
            elif self.type == 'ruby':
                particle_count = 5
            elif self.type == 'mineral':
                particle_count = 4
            
            time_seed = int(pygame.time.get_ticks() / 200) % 1000
            crystal_seed = int(self.x + self.y) % 100
            
            for i in range(particle_count):
                particle_seed = (time_seed + crystal_seed + i * 17) % 1000
                px = self.x + ((particle_seed % 31) - 15)
                py = self.y + (((particle_seed + 31) % 31) - 15)
                size = 1 + (particle_seed % 3)
                alpha = int(255 * ((particle_seed % 100) / 100.0))
                sparkle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surface, (*color, alpha), (size, size), size)
                surface.blit(sparkle_surface, (px-size, py-size))

    def check_collision(self, player):
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)


class CollectibleManager:
    def __init__(self):
        self.collectibles = []
        self.score = 0
        self.generated_platforms = set()
        
    def add_collectible_near_platform(self, platform, total_scroll_distance):
        """Aggiunge un collezionabile vicino a una piattaforma."""
        absolute_y = platform.rect.top - total_scroll_distance
        platform_id = f"{platform.rect.centerx}_{int(absolute_y)}"
        
        if platform_id in self.generated_platforms:
            return
            
        x = platform.rect.centerx + random.randint(-40, 40)
        y = platform.rect.top - random.randint(20, 40)
        collectible = Collectible(x, y)
        self.collectibles.append(collectible)
        
        self.generated_platforms.add(platform_id)
        
    def update(self, dt, dy):
        """Aggiorna tutti i collezionabili."""
        for collectible in self.collectibles:
            collectible.update(dt)
            collectible.y += dy  # Segue lo scroll della camera
        
        # Rimuovi collezionabili che sono usciti dallo schermo
        self.collectibles = [c for c in self.collectibles if c.y < SCREEN_HEIGHT + 100]
    
    def draw(self, screen):
        """Disegna tutti i collezionabili."""
        for collectible in self.collectibles:
            if -50 < collectible.y < SCREEN_HEIGHT + 50:
                collectible.draw(screen, 0)
    
    def check_collisions(self, player):
        """Controlla collisioni con il player."""
        collected = []
        for collectible in self.collectibles:
            if collectible.check_collision(player):
                collectible.collected = True
                self.score += collectible.value
                # Restituisce tupla (collectible, valore) per i popup
                collected.append((collectible, collectible.value))
        
        self.collectibles = [c for c in self.collectibles if not c.collected]
        return collected
    
    def generate_random_collectibles(self, platforms, total_scroll_distance):
        """Genera collezionabili casuali vicino ad alcune piattaforme."""
        for platform in platforms:
            absolute_y = platform.rect.top - total_scroll_distance
            platform_id = f"{platform.rect.centerx}_{int(absolute_y)}"
            
            if platform_id in self.generated_platforms:
                continue
                
            # Aumentata probabilità dal 30% al 50% per ancora più collectibles
            if random.random() < 0.50:
                # Possibilità di generare più collectibles per piattaforma
                num_collectibles = 1
                if random.random() < 0.3:  # 30% chance per collectibles multipli
                    num_collectibles = random.randint(2, 3)
                
                for _ in range(num_collectibles):
                    proposed_x = platform.rect.centerx + random.randint(-60, 60)
                    proposed_y = platform.rect.top - random.randint(15, 50)
                    
                    too_close = False
                    for collectible in self.collectibles:
                        if abs(collectible.x - proposed_x) < 40 and abs(collectible.y - proposed_y) < 40:
                            too_close = True
                            break
                    
                    if not too_close:
                        collectible = Collectible(proposed_x, proposed_y)
                        self.collectibles.append(collectible)
                
                self.generated_platforms.add(platform_id)
    
    def get_score(self):
        """Restituisce il punteggio attuale."""
        return self.score
    
    def reset(self):
        """Resetta il sistema dei collezionabili."""
        self.collectibles = []
        self.score = 0
        self.generated_platforms = set()