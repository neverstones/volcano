import pygame, random, math
from game_constants import HEIGHT


class Collectible:
    def __init__(self, x, y, value=100):
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.radius = 10
        self.animation_time = 0
        self.type = random.choice(['crystal', 'gem', 'mineral'])

        self.colors = {
            'crystal': (0, 255, 255),
            'gem': (255, 0, 255),
            'mineral': (255, 215, 0)
        }

    def update(self, dt):
        self.animation_time += dt * 4

    def draw(self, surface, world_offset):
        if self.collected:
            return

        screen_y = self.y + world_offset
        if -50 < screen_y < HEIGHT + 50:
            # Rotazione e scala
            rotation = self.animation_time
            scale = 0.9 + 0.1 * math.sin(self.animation_time * 2)

            color = self.colors[self.type]
            radius = int(self.radius * scale)

            # Stella brillante
            points = []
            for i in range(8):
                angle = rotation + i * math.pi / 4
                if i % 2 == 0:
                    r = radius
                else:
                    r = radius * 0.5

                x = self.x + r * math.cos(angle)
                y = screen_y + r * math.sin(angle)
                points.append((x, y))

            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)

            # Particelle scintillanti - VERSIONE STABILE
            time_seed = int(pygame.time.get_ticks() / 200) % 1000  # Cambia ogni 200ms
            crystal_seed = int(self.x + self.y) % 100  # Seed basato su posizione
            
            for i in range(3):
                particle_seed = (time_seed + crystal_seed + i * 17) % 1000
                px = self.x + ((particle_seed % 31) - 15)  # -15 a +15
                py = screen_y + (((particle_seed + 31) % 31) - 15)  # -15 a +15
                size = 1 + (particle_seed % 3)  # 1-3
                alpha = int(255 * ((particle_seed % 100) / 100.0))  # 0-255
                sparkle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surface, (*color, alpha), (size, size), size)
                surface.blit(sparkle_surface, (px-size, py-size))

    def check_collision(self, player):
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)