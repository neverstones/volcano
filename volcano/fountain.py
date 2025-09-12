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
        self.x = x + random.uniform(-8,8)  # Più stretto (era -20,20)
        self.y = y
        self.vx = random.uniform(-1.0, 1.0)  # Velocità orizzontale ridotta (era -2.0, 2.0)
        self.vy = random.uniform(-16, -9)  # più alta
        self.radius = random.uniform(6,10)
        self.trail = []
        self.max_trail = 30
        self.fade_factor = 1.0

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

# --- Particelle fumo (plume) ---
class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-60, 60)    # Dispersione limitata
        self.y = y - 30                         # Parte poco sopra la fontana
        self.vx = random.uniform(-5.0, 5.0)     # Velocità orizzontale contenuta
        self.vy = random.uniform(-12.0, -8.0)   # Velocità verticale moderata
        self.radius = random.uniform(12, 20)    # Nuvole piccole
        self.age = 0
        self.max_age = random.randint(180, 220) # Durata moderata

    def update(self):
        gravity = 0.05  # Gravità molto ridotta per il fumo
        self.vy += gravity
        
        self.x += self.vx + math.sin(self.age*0.03)*0.5
        self.y += self.vy
        self.age += 1

        self.radius *= 1.003

    def draw(self, surf):
        alpha = max(0, int(200 * (1 - self.age/self.max_age)))
        if alpha <= 0:
            return
        size = int(self.radius)
        s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (40,40,40,alpha), (size,size), size)
        surf.blit(s, (self.x-size, self.y-size))

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Fontana Ultra-Spettacolare")
    clock = pygame.time.Clock()

    fountain_x = SCREEN_WIDTH//2
    fountain_y = SCREEN_HEIGHT-50
    lava_particles = []
    smoke_particles = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fontana: getto centrale e due archi laterali
        for _ in range(3):
            lava_particles.append(LavaParticle(fountain_x, fountain_y, mode="center"))
        for _ in range(3):
            lava_particles.append(LavaParticle(fountain_x, fountain_y, mode="left"))
        for _ in range(3):
            lava_particles.append(LavaParticle(fountain_x, fountain_y, mode="right"))
        for _ in range(5):
            smoke_particles.append(SmokeParticle(fountain_x, fountain_y))

        # Aggiorna
        for p in lava_particles:
            p.update()
        for p in smoke_particles:
            p.update()

        # Pulisci
        lava_particles = [p for p in lava_particles if p.y < SCREEN_HEIGHT+100]
        smoke_particles = [p for p in smoke_particles if p.age < p.max_age]

        # Disegna
        screen.fill((10,10,20))

        # Prima fumo
        for p in smoke_particles:
            p.draw(screen)
        # Poi lava
        for p in lava_particles:
            p.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
