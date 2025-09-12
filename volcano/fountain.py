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
        self.x = x + random.uniform(-120, 120)  # Ampiezza estrema aumentata (da -80,80 a -120,120)
        self.y = y
        self.vx = random.uniform(-8.0, 8.0)  # Velocità orizzontale aumentata (da -6.0,6.0 a -8.0,8.0)
        self.vy = random.uniform(-40, -30)  # Gittata verticale aumentata (da -35,-25 a -40,-30)
        self.radius = random.uniform(7, 12)  # Particelle ancora più grandi (da 6,10 a 7,12)
        self.trail = []
        self.max_trail = 45  # Trail più lungo (da 40 a 45)
        self.fade_factor = 1.0  # Fattore di trasparenza per fade-out verso il suolo

    def update(self):
        gravity = 0.35
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

        # Calcola fade-out verso il suolo del cratere
        crater_floor_level = 600 * 0.75  # Livello del terreno nel cratere (75% dell'altezza)
        fade_start_level = 600 * 0.65   # Inizia il fade al 65% dell'altezza
        
        if self.y > fade_start_level:
            # Calcola il fattore di fade (1.0 = completamente visibile, 0.0 = trasparente)
            fade_progress = (self.y - fade_start_level) / (crater_floor_level - fade_start_level)
            self.fade_factor = max(0.0, 1.0 - fade_progress)
        else:
            self.fade_factor = 1.0

        # Trail
        self.trail.insert(0, (self.x,self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

    def draw(self, surf):
        # Se il fade_factor è troppo basso, non disegnare nulla
        if self.fade_factor <= 0.05:
            return
            
        L = len(self.trail)
        for i,(tx,ty) in enumerate(self.trail):
            t = i/max(1,L-1)
            if t < 0.5:
                col = lerp_color((255,165,0),(255,0,0), t*2)
            else:
                col = lerp_color((255,0,0),(80,80,80), (t-0.5)*2)
            # Applica il fade_factor all'alpha per il fade-out verso il suolo
            alpha = int(255*(1-t)*self.fade_factor)
            size = int(self.radius*(0.5 + 0.5*(1-t)))
            s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size,size), size)
            surf.blit(s, (tx-size, ty-size))

# --- Particelle fumo (plume aeriforme largo) ---
class SmokeParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-130, 130)  # Ampiezza estrema aumentata (da -100,100 a -130,130)
        self.y = y - 60  # Inizia ancora più in alto (da -50 a -60)
        self.vx = random.uniform(-2.5, 2.5)  # Velocità orizzontale aumentata (da -1.8,1.8 a -2.5,2.5)
        self.vy = random.uniform(-7.5, -5.0)  # Velocità verticale aumentata (da -6.5,-4.0 a -7.5,-5.0)
        self.radius = random.uniform(18, 30)  # Particelle molto più grandi (da 15,25 a 18,30)
        self.age = 0
        self.max_age = random.randint(200, 280)  # Durata aumentata (da 180,250 a 200,280)

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

# --- Setup Pygame (solo se eseguito direttamente) ---
if __name__ == "__main__":
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
