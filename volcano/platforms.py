import pygame, random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, PLATFORM_WIDTH, PLATFORM_HEIGHT

class Platform:
    def __init__(self, x, y, width=PLATFORM_WIDTH, height=PLATFORM_HEIGHT):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surf):
        pygame.draw.rect(surf, (100, 50, 0), self.rect, border_radius=5)

class PlatformManager:
    def __init__(self, num_platforms=12):
        self.num_platforms = num_platforms
        self.platforms = []

    def generate_platforms(self, player=None):
        """Genera piattaforme con almeno una per fascia verticale."""
        self.platforms = []

        # Piattaforma iniziale sotto il player
        if player:
            start_x = player.x - PLATFORM_WIDTH // 2
            start_y = player.y + player.radius
            self.platforms.append(Platform(start_x, start_y))
            base_y = start_y
        else:
            base_y = SCREEN_HEIGHT - 50
            self.platforms.append(Platform(SCREEN_WIDTH//2 - PLATFORM_WIDTH//2, base_y))

        # Altezza massima raggiungibile
        min_dy = 50
        max_dy = 120
        current_y = base_y
        max_height = SCREEN_HEIGHT * 3

        while current_y > -max_height:
            # Crea una piattaforma per ciascuna fascia: sinistra, centro, destra
            for zone in range(3):
                zone_x_min = zone * (SCREEN_WIDTH//3) + 20
                zone_x_max = (zone + 1) * (SCREEN_WIDTH//3) - PLATFORM_WIDTH - 20
                if zone_x_max <= zone_x_min:
                    continue
                x = random.randint(zone_x_min, zone_x_max)
                y = current_y - random.randint(min_dy, max_dy)
                self.platforms.append(Platform(x, y))
            current_y = y

    def update(self, dy):
        """Scroll delle piattaforme verso il basso."""
        for plat in self.platforms:
            plat.rect.y += dy

        # Rigenera piattaforme sopra lo schermo
        for plat in self.platforms:
            if plat.rect.top > SCREEN_HEIGHT:
                zone = random.randint(0, 2)
                zone_x_min = zone * (SCREEN_WIDTH//3) + 20
                zone_x_max = (zone + 1) * (SCREEN_WIDTH//3) - PLATFORM_WIDTH - 20
                plat.rect.x = random.randint(zone_x_min, zone_x_max)
                plat.rect.y = -PLATFORM_HEIGHT

    def check_collision(self, player):
        """Collisione arcade solo da sopra (Doodle Jump)."""
        player_rect = pygame.Rect(
            player.x - player.radius,
            player.y + player.radius,
            player.radius*2,
            2  # piccolo rettangolo sotto il player
        )
        for plat in self.platforms:
            if player.vy > 0 and player_rect.colliderect(plat.rect):
                player.y = plat.rect.top - player.radius
                player.vy = -player.jump_strength
                player.on_ground = True
                return True
        return False

    def draw(self, surf):
        for plat in self.platforms:
            plat.draw(surf)
