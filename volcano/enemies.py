import pygame
import random
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

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="olivina"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        
        colors = {
            "olivina": (0, 200, 0),
            "pirosseno": (150, 75, 0),
            "anfibolo": (0, 100, 150),
            "biotite": (50, 50, 50),
            "feldspato": (200, 200, 150),
            "quarzo": (180, 180, 255),
        }
        pygame.draw.circle(self.image, colors.get(kind, (255, 0, 0)), (20, 20), 20)
        self.rect = self.image.get_rect(center=(x, y))
        
        # Movimento orizzontale lento
        self.speedx = random.choice([-1, 1])
        self.speedy = random.uniform(0.5, 1.2)  # caduta lenta

    def update(self):
        # Movimento verticale lento
        self.rect.y += self.speedy
        # Movimento laterale
        self.rect.x += self.speedx
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.speedx *= -1

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)


class EnemyManager:
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.spawn_interval = 2000  # ms tra spawn di coppie
        self.last_spawn = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        # spawn coppia ogni spawn_interval
        if now - self.last_spawn > self.spawn_interval:
            self.spawn_pair()
            self.last_spawn = now

        # update tutti i nemici
        for enemy in list(self.enemies):
            enemy.update()
            if enemy.rect.top > SCREEN_HEIGHT:
                self.enemies.remove(enemy)

    def spawn_pair(self):
        kind1 = random.choice(list(penalties.keys()))
        kind2 = random.choice(list(penalties.keys()))
        x1 = random.randint(50, SCREEN_WIDTH - 50)
        x2 = random.randint(50, SCREEN_WIDTH - 50)
        y1 = -40
        y2 = -120  # separazione verticale della coppia
        self.enemies.add(Enemy(x1, y1, kind1))
        self.enemies.add(Enemy(x2, y2, kind2))

    def check_collision(self, player):
        hits = [e for e in self.enemies if e.rect.colliderect(player.get_rect())]
        return hits

    def draw(self, screen):
        for e in self.enemies:
            e.draw(screen)
