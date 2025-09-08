import pygame
import random
import math

# --- Costanti ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 120

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

# --- Particelle lava (fontana) ---
class LavaParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-20,20)  # più largo
        self.y = y
        self.vx = random.uniform(-2.0, 2.0)
        self.vy = random.uniform(-16, -9)  # più alta
        self.radius = random.uniform(6,10)
        self.trail = []
        self.max_trail = 30

    def update(self):
        gravity = 0.35
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

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
                col = lerp_color((255,0,0),(80,80,80), (t-0.5)*2)
            alpha = int(255*(1-t))
            size = int(self.radius*(0.5 + 0.5*(1-t)))
            s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size,size), size)
            surf.blit(s, (tx-size, ty-size))

# --- Particelle fumo (plume aeriforme largo) ---
class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-50,50)  # molto più largo
        self.y = y - 40  # parte prima della fontana
        self.vx = random.uniform(-0.6,0.6)
        self.vy = random.uniform(-3.5,-1.8)
        self.radius = random.uniform(12,20)
        self.age = 0
        self.max_age = random.randint(140,180)

    def update(self):
        # sale verso l’alto con dispersione
        self.x += self.vx + math.sin(self.age*0.05)*0.2
        self.y += self.vy
        self.age += 1

        # allargamento colonna con l’altezza
        self.radius *= 1.002

    def draw(self, surf):
        alpha = max(0, int(200 * (1 - self.age/self.max_age)))
        if alpha <= 0:
            return
        size = int(self.radius)
        s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (40,40,40,alpha), (size,size), size)
        surf.blit(s, (self.x-size, self.y-size))

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
    for _ in range(6):
        lava_particles.append(LavaParticle(fountain_x, fountain_y))
    for _ in range(8):
        smoke_particles.append(SmokeParticle(fountain_x, fountain_y))

    # --- Aggiorna ---
    for p in lava_particles:
        p.update()
    for p in smoke_particles:
        p.update()

    # --- Pulisci vecchie particelle ---
    lava_particles = [p for p in lava_particles if p.y < SCREEN_HEIGHT+50]
    smoke_particles = [p for p in smoke_particles if p.age < p.max_age]

    # --- Disegno ---
    screen.fill((10,10,20))

    # prima fumo
    for p in smoke_particles:
        p.draw(screen)
    # poi lava in primo piano
    for p in lava_particles:
        p.draw(screen)

    pygame.display.flip()

pygame.quit()
