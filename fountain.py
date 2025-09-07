import pygame
import random
import math

# --- Costanti ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 120

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

# --- Particelle lava (fontana verticale) ---
class LavaParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-10,10)  # getto più largo
        self.y = y
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(-12, -6)
        self.radius = random.uniform(6,10)
        self.trail = []
        self.max_trail = 25
        self.age = 0

    def update(self):
        gravity = 0.3
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.age += 1

        # Trail
        self.trail.insert(0, (self.x,self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

    def draw(self, surf):
        L = len(self.trail)
        for i,(tx,ty) in enumerate(self.trail):
            t = i/max(1,L-1)
            if t < 0.5:
                col = lerp_color((255,165,0),(255,0,0), t*2)
            else:
                col = lerp_color((255,0,0),(120,120,120), (t-0.5)*2)
            alpha = int(255*(1-t))
            size = int(self.radius*(0.5 + 0.5*(1-t)))
            s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size,size), size)
            surf.blit(s, (tx-size, ty-size))

# --- Particelle fumo (plume aeriforme più larga) ---
class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-30,30)  # ancora più largo
        self.y = y - 30  # parte prima della fontana
        self.vx = random.uniform(-0.5,0.5)
        self.vy = random.uniform(-4.0,-2.0)  # sale velocemente
        self.radius = random.uniform(10,18)
        self.trail = []
        self.max_trail = 60

    def update(self):
        # Sale verso l’alto con movimento aeriforme
        self.x += math.sin(pygame.time.get_ticks()*0.002 + random.random()*2) * 0.3
        self.y += self.vy

        # Trail
        self.trail.insert(0, (self.x,self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

    def draw(self, surf):
        L = len(self.trail)
        for i,(tx,ty) in enumerate(self.trail):
            t = i/max(1,L-1)
            col = (50,50,50)  # grigio scuro
            alpha = int(180*(1-t))
            size = int(self.radius*(0.3 + 0.7*(1-t)))
            s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size,size), size)
            surf.blit(s, (tx-size, ty-size))

# --- Setup Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fontana Lava + Plume Fumo")
clock = pygame.time.Clock()

fountain_x = SCREEN_WIDTH//2
fountain_y = SCREEN_HEIGHT-50
lava_particles = []
smoke_particles = []

running = True
while running:
    dt = clock.tick(FPS)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Genera particelle ---
    for _ in range(5):
        lava_particles.append(LavaParticle(fountain_x, fountain_y))
    for _ in range(6):
        smoke_particles.append(SmokeParticle(fountain_x, fountain_y))

    # --- Aggiorna particelle ---
    for p in lava_particles:
        p.update()
    for p in smoke_particles:
        p.update()

    # --- Rimuove particelle fuori schermo ---
    lava_particles = [p for p in lava_particles if p.y < SCREEN_HEIGHT+50]
    smoke_particles = [p for p in smoke_particles if p.y > -50]

    # --- Disegno ---
    screen.fill((10,10,20))

    # Prima il fumo (plume)
    for p in smoke_particles:
        p.draw(screen)
    # Poi la lava in primo piano
    for p in lava_particles:
        p.draw(screen)

    pygame.display.flip()

pygame.quit()
