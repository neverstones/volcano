import pygame, random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, PLATFORM_WIDTH, PLATFORM_HEIGHT

class Platform:
    def __init__(self, x, y, width=PLATFORM_WIDTH, height=PLATFORM_HEIGHT):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surf):
        pygame.draw.rect(surf, (100, 50, 0), self.rect, border_radius=5)


class PlatformManager:
    def __init__(self, num_platforms=10):
        self.num_platforms = num_platforms
        self.platforms = []

    def generate_platforms(self, player=None):
        """Genera piattaforme, assicurando che ci sia sempre quella iniziale sotto il player."""
        self.platforms = []

        # Se c'è il player → piattaforma di partenza sotto di lui
        if player:
            start_x = player.x - PLATFORM_WIDTH // 2
            start_y = player.y + player.radius
            start_platform = Platform(start_x, start_y, PLATFORM_WIDTH, PLATFORM_HEIGHT)
            self.platforms.append(start_platform)
        else:
            # Default: piattaforma in basso al centro
            self.platforms.append(
                Platform(SCREEN_WIDTH // 2 - PLATFORM_WIDTH // 2, SCREEN_HEIGHT - 50)
            )

        # Genera le altre piattaforme random
        for i in range(1, self.num_platforms):
            x = random.randint(50, SCREEN_WIDTH - PLATFORM_WIDTH - 50)
            y = SCREEN_HEIGHT - i * 80
            self.platforms.append(Platform(x, y))

    def update(self, dy):
        """Scroll delle piattaforme quando il player sale."""
        for plat in self.platforms:
            plat.rect.y += dy

        # Rigenera quelle uscite dallo schermo
        for plat in self.platforms:
            if plat.rect.top > SCREEN_HEIGHT:
                plat.rect.x = random.randint(50, SCREEN_WIDTH - PLATFORM_WIDTH - 50)
                plat.rect.y = -PLATFORM_HEIGHT

    def check_collision(self, player):
        """Collisione arcade solo da sopra (Doodle Jump)."""
        player_rect = pygame.Rect(
            player.x - player.radius,
            player.y + player.radius,
            player.radius * 2,
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
