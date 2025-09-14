# --- Gestione stato vittoria e fontana ---
import time

victory_fountain_active = False
fountain_start_time = 0
victory_timer = 0
fountain = None

def reset_victory_state():
    global victory_fountain_active, fountain_start_time, victory_timer, fountain
    victory_fountain_active = False
    fountain_start_time = 0
    victory_timer = 0
    fountain = None

def start_victory_fountain(screen_width, screen_height):
    global victory_fountain_active, fountain_start_time, fountain
    victory_fountain_active = True
    fountain_start_time = time.time()
    from fountain import Fountain
    fountain = Fountain(screen_width // 2, screen_height // 2)
    return fountain

def update_victory_fountain():
    global victory_timer, fountain_start_time, fountain
    victory_timer = time.time() - fountain_start_time
    if fountain is not None:
        fountain.emit()
        fountain.update()
    return victory_timer

def is_victory_active():
    global victory_fountain_active
    return victory_fountain_active

def get_victory_timer():
    global victory_timer
    return victory_timer

def get_fountain():
    global fountain
    return fountain

def set_victory_active(val):
    global victory_fountain_active
    victory_fountain_active = val
import pygame
import random
import math

# --- Costanti ---
SCREEN_WIDTH = 800

import pygame
import random
import math

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

class LavaParticle:
    def __init__(self, x, y):
        # Dispersione orizzontale e velocità aumentate per getti più parabolici
        self.x = x + random.uniform(-40, 40)
        self.y = y
        self.vx = random.uniform(-6.0, 6.0)
        self.vy = random.uniform(-16, -9)
        self.radius = random.uniform(6,10)
        self.trail = []
        self.max_trail = 30

    def update(self):
        gravity = 0.35
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.trail.insert(0, (self.x,self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

    def draw(self, surf, crater_y=None):
        L = len(self.trail)
        for i,(tx,ty) in enumerate(self.trail):
            t = i/max(1,L-1)
            if t < 0.5:
                col = lerp_color((255,165,0),(255,0,0), t*2)
            else:
                col = lerp_color((255,0,0),(80,80,80), (t-0.5)*2)
            # Dissolvi dal livello del cratere (passato come argomento)
            fade = 1
            if crater_y is not None and ty > crater_y:
                fade = max(0, 1 - (ty-crater_y)/120)
            alpha = int(255*(1-t)*fade)
            if alpha <= 0:
                continue
            size = int(self.radius*(0.5 + 0.5*(1-t)))
            s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size,size), size)
            surf.blit(s, (tx-size, ty-size))

class SmokeParticle:
    def __init__(self, x, y):
        # Dispersione orizzontale come versione originale (più stretta)
        self.x = x + random.uniform(-50, 50)
        self.y = y - 40
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-3.5, -1.8)
        self.radius = random.uniform(12, 20)
        self.age = 0
        self.max_age = random.randint(140, 180)

    def update(self):
        self.x += self.vx + math.sin(self.age*0.05)*0.2
        self.y += self.vy
        self.age += 1
        self.radius *= 1.002

    def draw(self, surf):
        alpha = max(0, int(200 * (1 - self.age/self.max_age)))
        if alpha <= 0:
            return
        size = int(self.radius)
        s = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (40,40,40,alpha), (size,size), size)
        surf.blit(s, (self.x-size, self.y-size))

class Fountain:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lava_particles = []
        self.smoke_particles = []

    def emit(self):
        # Numero particelle come versione originale
        for _ in range(6):
            self.lava_particles.append(LavaParticle(self.x, self.y))
        for _ in range(8):
            self.smoke_particles.append(SmokeParticle(self.x, self.y))


    def update(self):
        for p in self.lava_particles:
            p.update()
        for p in self.smoke_particles:
            p.update()
        # Elimina le particelle di lava che sono praticamente "dissolte" sotto il cratere
        self.lava_particles = [p for p in self.lava_particles if p.y < 2000 and (p.y < p.y + 120 or p.trail[0][1] < p.y + 120)]
        self.smoke_particles = [p for p in self.smoke_particles if p.age < p.max_age]

    def draw(self, surf):
        for p in self.smoke_particles:
            p.draw(surf)
        # Passa la y del cratere a ogni particella di lava
        for p in self.lava_particles:
            p.draw(surf, crater_y=self.y)

        # Disegna


    pygame.quit()
