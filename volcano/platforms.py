import pygame
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

class Platform:
    def __init__(self, x, y, width=100, height=20, color=(100, 255, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)

    def collidepoint(self, px, py):
        """Controlla se un punto (player) sta sopra la piattaforma."""
        return self.rect.collidepoint(px, py)


class PlatformManager:
    def __init__(self, num_platforms=8):
        self.platforms = []
        self.num_platforms = num_platforms
        

    def generate_platforms(self, start_x=None, start_y=None):
        self.platforms.clear()

        # --- piattaforma iniziale fissa sotto il player ---
        if start_x is not None and start_y is not None:
            start_platform = Platform(start_x - 50, start_y + 40, 100, 20)
            self.platforms.append(start_platform)

        # --- altre piattaforme random ---
        for i in range(self.num_platforms):
            x = random.randint(50, SCREEN_WIDTH - 150)
            y = random.randint(50, SCREEN_HEIGHT - 50)
            self.platforms.append(Platform(x, y, 100, 20))

    def draw(self, surf):
        for p in self.platforms:
            p.draw(surf)

    def check_collision(self, player):
        """Ritorna True se il player sta su una piattaforma."""
        for plat in self.platforms:
            if player.vy > 0 and plat.rect.collidepoint(player.x, player.y + player.radius):
                player.y = plat.rect.top - player.radius
                player.vy = 0
                player.on_ground = True
                return True
        return False
    
    def generate_initial_platforms(self, player_x, player_y, width=100, height=20):
        """Genera la piattaforma iniziale sotto il player + altre random."""
        # piattaforma iniziale sotto il player
        base_platform = Platform(player_x - width // 2, player_y + 50, width, height)
        self.platforms.add(base_platform)

        # genera alcune piattaforme random sopra
        for i in range(6):
            x = random.randint(50, SCREEN_WIDTH - 150)
            y = SCREEN_HEIGHT - (i * 100)
            plat = Platform(x, y, 100, 20)
            self.platforms.add(plat)

    def update(self, dy):
        """Scorre le piattaforme verso il basso (per effetto jump)."""
        for p in self.platforms:
            p.rect.y += dy
        # Rimuovi piattaforme fuori schermo e genera nuove in alto
        for i in range(len(self.platforms)):
            if self.platforms[i].rect.top > SCREEN_HEIGHT:
                width = random.randint(80, 150)
                x = random.randint(0, SCREEN_WIDTH - width)
                y = -20
                self.platforms[i] = Platform(x, y, width)
