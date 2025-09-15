import random
import pygame
from constants import SCREEN_HEIGHT

# --- Gestione bolle di magma e collectibles globali ---
collectibles = []
block_on_demand_collectibles = False

def spawn_magma_bubbles_on_platforms(platform_manager, density=0.8):
    """Posiziona una bolla di magma su ogni piattaforma di ogni livello, senza offset y. density=1.0 per massima densità."""
    global collectibles
    collectibles = []
    for plat in platform_manager.platforms:
        if random.random() < density:
            if not any(c.type == 'magma_bubble' and c.platform == plat for c in collectibles):
                x = plat.rect.centerx
                radius = 10  # Deve corrispondere a Collectible.radius
                offset = 16  # Spazio extra tra piattaforma e bolla
                y_bubble = plat.rect.top - offset - radius
                bubble = Collectible(x, y_bubble, value=200)
                bubble.type = 'magma_bubble'
                bubble.platform = plat  # Associa la piattaforma
                collectibles.append(bubble)

def add_magma_bubble_for_platform(plat):
    """Aggiunge una bolla di magma su ogni nuova piattaforma, senza offset y."""
    global collectibles
    if random.random() < 0.8:
        if not any(c.type == 'magma_bubble' and c.platform == plat for c in collectibles):
            x = plat.rect.centerx
            radius = 10  # Deve corrispondere a Collectible.radius
            offset = 16  # Spazio extra tra piattaforma e bolla
            y = plat.rect.top - offset - radius
            bubble = Collectible(x, y, value=200)
            bubble.type = 'magma_bubble'
            bubble.platform = plat  # Associa la piattaforma
            collectibles.append(bubble)

def update_collectibles(dt):
    global collectibles
    for c in collectibles:
        c.update(dt)

def draw_collectibles(screen, world_offset, platform_manager):
    global collectibles
    from collectibles import prune_orphaned_or_offscreen
    prune_orphaned_or_offscreen(collectibles, platform_manager, world_offset, SCREEN_HEIGHT)
    for c in collectibles:
        c.draw(screen, world_offset)

def check_collectibles_collision(player):
    global collectibles
    collected = 0
    for c in collectibles:
        if not c.collected and c.type == 'magma_bubble' and c.check_collision(player):
            c.collected = True
            c.trigger_float_text(f'+{c.value}')
            collected += c.value
    return collected

def get_world_offset():
    return 0
@staticmethod
def prune_orphaned_or_offscreen(collectibles, platform_manager, world_offset, screen_height):
    """Rimuove collectibles se la piattaforma associata non è più attiva o sono fuori schermo."""
    active_platforms = set(platform_manager.platforms)
    def is_collectible_visible(c):
        if c.platform is not None:
            if c.platform not in active_platforms:
                return False
            plat_y = c.platform.rect.top + world_offset
            return -50 < plat_y < screen_height + 50
        else:
            y = c.y + world_offset
            return -50 < y < screen_height + 50
    collectibles[:] = [c for c in collectibles if is_collectible_visible(c)]
import pygame
import random
import math
from constants import SCREEN_HEIGHT



class Collectible:
    def __init__(self, x, y, value=100):
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.radius = 10
        self.animation_time = 0
        self.type = random.choice(['crystal', 'gem', 'mineral', 'magma_bubble'])
        self.platform = None  # riferimento alla piattaforma su cui si trova
        self.float_text = None  # testo che sale e si dissolve
        self.float_timer = 0
        self.float_y = 0
        self.lava_particles = []  # particelle decorative

        self.colors = {
            'crystal': (0, 255, 255),
            'gem': (255, 0, 255),
            'mineral': (255, 215, 0),
            'magma_bubble': (255, 120, 0)
        }

    def update(self, dt):
        self.animation_time += dt * 4
        # Se la bolla è raccolta, aggiorna il testo che sale
        if self.float_text:
            self.float_timer += dt
            self.float_y -= 30 * dt  # sale verso l'alto
            if self.float_timer > 1.0:
                self.float_text = None

        # Aggiorna particelle lava decorative
        if self.type == 'magma_bubble' and not self.collected:
            # Aggiungi nuove particelle decorative ancorate alla piattaforma
            if random.random() < 0.15:
                angle = random.uniform(0, 2*math.pi)
                speed = random.uniform(8, 18)
                vx = math.cos(angle) * speed * 0.1
                vy = math.sin(angle) * speed * 0.1 - 0.5
                self.lava_particles.append({
                    'rel_x': 0,
                    'rel_y': 0,
                    'vx': vx,
                    'vy': vy,
                    'life': random.uniform(0.3, 0.7),
                    'age': 0,
                    'radius': random.randint(2, 4)
                })
            # Aggiorna e rimuovi particelle vecchie (relative alla bolla)
            for p in self.lava_particles:
                p['rel_x'] += p['vx']
                p['rel_y'] += p['vy']
                p['vy'] += 0.12  # gravità
                p['age'] += dt
            self.lava_particles = [p for p in self.lava_particles if p['age'] < p['life']]


    def draw(self, surface, world_offset):
        # Testo che sale e si dissolve
        # Calcola la posizione reale ancorata alla piattaforma (se presente)
        plat_x = self.x
        plat_y = self.y
        if self.platform is not None:
            plat_x = self.platform.rect.centerx
            plat_y = self.platform.rect.top

            # Offset verticale per le magma_bubble (sempre sopra la piattaforma)
            vertical_gap = 10  # spazio visivo tra piattaforma e bolla

            if self.type == 'magma_bubble' and self.platform is not None:
                y_draw = plat_y - vertical_gap - self.radius + world_offset
            else:
                y_draw = plat_y + world_offset

            # Testo che sale e si dissolve
            if self.float_text:
                font = pygame.font.SysFont(None, 32)
                alpha = max(0, 255 - int(self.float_timer * 255))
                text_surf = font.render(self.float_text, True, (255,255,0))
                text_surf.set_alpha(alpha)
                surface.blit(text_surf, (plat_x-18, y_draw + self.float_y))

            if self.collected:
                return

            # Statico: la bolla resta ferma sulla piattaforma
            screen_y = y_draw
            if -50 < screen_y < SCREEN_HEIGHT + 50:
                if self.type == 'magma_bubble':
                    # Particelle lava decorative ancorate alla piattaforma
                    for p in self.lava_particles:
                        alpha = int(255 * (1 - p['age']/p['life']))
                        color = (255, 120, 0, alpha)
                        s = pygame.Surface((p['radius']*2, p['radius']*2), pygame.SRCALPHA)
                        pygame.draw.circle(s, color, (p['radius'], p['radius']), p['radius'])
                        # Le particelle sono sempre relative alla piattaforma
                        surface.blit(s, (plat_x + p['rel_x'] - p['radius'], plat_y + p['rel_y'] - p['radius'] - vertical_gap - self.radius + world_offset))
                    # Bolla
                    pygame.draw.circle(surface, (255, 120, 0), (int(plat_x), int(y_draw)), self.radius)
                    glow_surf = pygame.Surface((self.radius*2+8, self.radius*2+8), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (255, 200, 80, 80), (self.radius+4, self.radius+4), self.radius+4)
                    surface.blit(glow_surf, (int(plat_x)-self.radius-4, int(y_draw)-self.radius-4), special_flags=pygame.BLEND_RGBA_ADD)
                    pygame.draw.circle(surface, (255, 255, 180), (int(plat_x)-4, int(y_draw)-4), 5)
                    pygame.draw.circle(surface, (180, 60, 0), (int(plat_x), int(y_draw)), self.radius, 2)
                else:
                    # ...existing code for other types...
                    color = self.colors.get(self.type, (255,255,255))
                    rotation = self.animation_time
                    scale = 0.9 + 0.1 * math.sin(self.animation_time * 2)
                    radius = int(self.radius * scale)
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
        if self.collected or self.float_text:
            return False
        # Usa la posizione ancorata alla piattaforma
        plat_x = self.x
        plat_y = self.y
        if self.platform is not None:
            plat_x = self.platform.rect.centerx
            plat_y = self.platform.rect.top - 28
        distance = math.hypot(player.x - plat_x, player.y - plat_y)
        # Raccogli solo se il player è sopra la piattaforma (non se la piattaforma copre la bolla)
        if player.y + player.radius < plat_y:
            return False
        return distance < (self.radius + player.radius)

    def trigger_float_text(self, text='+100'):
        self.float_text = text
        self.float_timer = 0
        self.float_y = 0