import pygame
import random
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

# penalità secondi per tipo minerale
penalties = {
    "olivina": 5,
    "pirosseno": 8, 
    "anfibolo": 10,
    "biotite": 12,
    "feldspato": 7,
    "quarzo": 15,
}

# Proprietà grafiche per ogni minerale
mineral_properties = {
    "olivina": {
        "color": (107, 142, 35),  # Verde oliva
        "accent": (85, 107, 47),  # Verde scuro
        "shape": "crystal",
        "size": 35
    },
    "pirosseno": {
        "color": (139, 69, 19),  # Marrone scuro
        "accent": (160, 82, 45),  # Marrone chiaro
        "shape": "prism",
        "size": 40
    },
    "anfibolo": {
        "color": (47, 79, 79),  # Grigio scuro ardesia
        "accent": (112, 128, 144),  # Grigio ardesia
        "shape": "needle",
        "size": 45
    },
    "biotite": {
        "color": (25, 25, 25),  # Nero
        "accent": (105, 105, 105),  # Grigio scuro
        "shape": "sheet",
        "size": 38
    },
    "feldspato": {
        "color": (255, 228, 196),  # Beige
        "accent": (222, 184, 135),  # Marrone chiaro
        "shape": "block",
        "size": 42
    },
    "quarzo": {
        "color": (230, 230, 250),  # Lavanda
        "accent": (176, 196, 222),  # Azzurro acciaio
        "shape": "hex",
        "size": 36
    },
}

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="olivina"):
        super().__init__()
        self.kind = kind
        self.properties = mineral_properties[kind]
        
        # Crea superficie con alpha per trasparenza
        size = self.properties["size"]
        self.image = pygame.Surface((size + 10, size + 25), pygame.SRCALPHA)
        
        # Disegna il minerale
        self._draw_mineral()
        
        self.rect = self.image.get_rect(center=(x, y))
        
        # Movimento più naturale
        self.speedx = random.uniform(-0.8, 0.8)
        self.speedy = random.uniform(1.0, 2.5)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        
        # Oscillazione durante la caduta
        self.oscillation = random.uniform(0, math.pi * 2)
        self.oscillation_speed = random.uniform(0.02, 0.05)

    def _draw_mineral(self):
        """Disegna il minerale con forma caratteristica."""
        size = self.properties["size"]
        color = self.properties["color"]
        accent = self.properties["accent"]
        shape = self.properties["shape"]
        
        center_x = (size + 10) // 2
        center_y = size // 2
        
        if shape == "crystal":  # Olivina - forma cristallina
            points = [
                (center_x, center_y - size//2),
                (center_x + size//3, center_y - size//4),
                (center_x + size//2, center_y + size//4),
                (center_x, center_y + size//2),
                (center_x - size//2, center_y + size//4),
                (center_x - size//3, center_y - size//4)
            ]
            pygame.draw.polygon(self.image, color, points)
            pygame.draw.polygon(self.image, accent, points, 2)
            
        elif shape == "prism":  # Pirosseno - forma prismatica
            rect = pygame.Rect(center_x - size//3, center_y - size//2, size//1.5, size)
            pygame.draw.rect(self.image, color, rect)
            pygame.draw.rect(self.image, accent, rect, 3)
            # Linee interne
            pygame.draw.line(self.image, accent, 
                           (center_x - size//6, center_y - size//2),
                           (center_x - size//6, center_y + size//2), 2)
            
        elif shape == "needle":  # Anfibolo - forma aghiforme
            pygame.draw.ellipse(self.image, color, 
                              (center_x - size//6, center_y - size//2, size//3, size))
            pygame.draw.ellipse(self.image, accent,
                              (center_x - size//6, center_y - size//2, size//3, size), 2)
            
        elif shape == "sheet":  # Biotite - forma lamellare
            for i in range(3):
                offset = i * 3
                rect = pygame.Rect(center_x - size//2 + offset, center_y - size//3 + offset, 
                                 size - offset*2, size//1.5 - offset)
                pygame.draw.rect(self.image, color if i == 0 else accent, rect)
                
        elif shape == "block":  # Feldspato - forma massiva
            pygame.draw.rect(self.image, color, 
                           (center_x - size//2, center_y - size//2, size, size))
            pygame.draw.rect(self.image, accent,
                           (center_x - size//2, center_y - size//2, size, size), 2)
            # Clivaggio
            pygame.draw.line(self.image, accent,
                           (center_x - size//2, center_y),
                           (center_x + size//2, center_y), 2)
            
        elif shape == "hex":  # Quarzo - forma esagonale
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                x = center_x + (size//2) * math.cos(angle)
                y = center_y + (size//2) * math.sin(angle)
                points.append((x, y))
            pygame.draw.polygon(self.image, color, points)
            pygame.draw.polygon(self.image, accent, points, 2)
        
        # Aggiungi il nome del minerale sotto
        font = pygame.font.Font(None, 16)
        text = font.render(self.kind.capitalize(), True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, size + 15))
        
        # Ombra del testo
        shadow = font.render(self.kind.capitalize(), True, (0, 0, 0))
        self.image.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        self.image.blit(text, text_rect)

    def update(self):
        # Movimento con oscillazione naturale
        self.oscillation += self.oscillation_speed
        oscillation_offset = math.sin(self.oscillation) * 0.5
        
        self.rect.y += self.speedy
        self.rect.x += self.speedx + oscillation_offset
        
        # Rotazione
        self.rotation += self.rotation_speed
        
        # Rimbalzo sui bordi con perdita di energia
        if self.rect.left < 50:
            self.rect.left = 50
            self.speedx = abs(self.speedx) * 0.8
        elif self.rect.right > SCREEN_WIDTH - 50:
            self.rect.right = SCREEN_WIDTH - 50
            self.speedx = -abs(self.speedx) * 0.8

    def draw(self, screen):
        # Disegna con rotazione se necessario
        if abs(self.rotation_speed) > 0.1:
            # Ruota l'immagine
            rotated = pygame.transform.rotate(self.image, self.rotation)
            rotated_rect = rotated.get_rect(center=self.rect.center)
            screen.blit(rotated, rotated_rect)
        else:
            screen.blit(self.image, self.rect.topleft)


class EnemyManager:
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.spawn_timer = 0
        self.base_spawn_interval = 3.0  # secondi base tra spawn
        self.spawn_variation = 2.0  # variazione casuale
        self.next_spawn_time = self._calculate_next_spawn()
        
        # Probabilità di spawn per tipo (alcuni più rari)
        self.spawn_weights = {
            "olivina": 25,     # Comune
            "feldspato": 20,   # Comune
            "pirosseno": 15,   # Abbastanza comune
            "biotite": 15,     # Abbastanza comune
            "anfibolo": 12,    # Meno comune
            "quarzo": 8,       # Raro (più penalità)
        }

    def _calculate_next_spawn(self):
        """Calcola il tempo per il prossimo spawn con variazione casuale."""
        variation = random.uniform(-self.spawn_variation, self.spawn_variation)
        return self.base_spawn_interval + variation

    def _get_weighted_mineral(self):
        """Seleziona un minerale basato sui pesi di probabilità."""
        minerals = list(self.spawn_weights.keys())
        weights = list(self.spawn_weights.values())
        return random.choices(minerals, weights=weights)[0]

    def update(self, dt, scroll_offset=0, total_scroll_distance=0):
        self.spawn_timer += dt

        # Difficoltà: più si sale, più spawn veloci (min 0.7s tra spawn)
        difficulty = min(1.5, 0.2 + (total_scroll_distance or 0) / 3000)
        effective_spawn_interval = max(0.7, self.base_spawn_interval / difficulty)

        if self.spawn_timer >= effective_spawn_interval:
            # Più si sale, più nemici spawnano insieme (max 3)
            n = 1 + int((total_scroll_distance or 0) / 4000)
            for _ in range(min(n, 3)):
                self.spawn_single_enemy()
            self.spawn_timer = 0
            self.next_spawn_time = self._calculate_next_spawn()

        # Aggiorna tutti i nemici
        for enemy in list(self.enemies):
            enemy.update()
            # Applica offset di scroll per effetto salita del player
            if scroll_offset > 0:
                enemy.rect.y += scroll_offset
            # Rimuovi nemici fuori schermo
            if enemy.rect.top > SCREEN_HEIGHT + 50:
                self.enemies.remove(enemy)

    def spawn_single_enemy(self):
        """Spawna un singolo nemico in posizione casuale."""
        kind = self._get_weighted_mineral()
        x = random.randint(80, SCREEN_WIDTH - 80)
        y = random.randint(-100, -50)  # Varia l'altezza di spawn
        
        self.enemies.add(Enemy(x, y, kind))

    def spawn_cluster(self, num_enemies=3):
        """Spawna un gruppo di nemici vicini (per eventi speciali)."""
        center_x = random.randint(100, SCREEN_WIDTH - 100)
        
        for i in range(num_enemies):
            kind = self._get_weighted_mineral()
            # Posizioni vicine ma non sovrapposte
            x = center_x + random.randint(-60, 60)
            y = random.randint(-150, -50) - i * 40
            x = max(80, min(SCREEN_WIDTH - 80, x))  # Mantieni nei limiti
            
            self.enemies.add(Enemy(x, y, kind))

    def check_collision(self, player):
        """Controlla collisioni con il player."""
        player_rect = player.get_rect()
        hits = []
        
        for enemy in self.enemies:
            # Collisione più precisa considerando la forma del minerale
            if enemy.rect.colliderect(player_rect):
                # Controllo distanza per collisione più realistica
                dx = enemy.rect.centerx - player_rect.centerx
                dy = enemy.rect.centery - player_rect.centery
                distance = math.sqrt(dx*dx + dy*dy)
                
                collision_threshold = (enemy.properties["size"] + player.radius) // 2
                if distance < collision_threshold:
                    hits.append(enemy)
        
        return hits

    def draw(self, screen):
        """Disegna tutti i nemici."""
        for enemy in self.enemies:
            enemy.draw(screen)

    def get_enemy_count(self):
        """Restituisce il numero di nemici attivi."""
        return len(self.enemies)
