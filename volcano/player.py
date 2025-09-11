import pygame, math, random
from constants import SCREEN_WIDTH, PLAYER_RADIUS

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

class WobblyBall:
    def __init__(self, x, y, radius=PLAYER_RADIUS, color=(255,165,0)):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = radius
        self.base_radius = radius
        self.color = color
        self.trail = []
        self.MAX_TRAIL = 36
        self.particles = []

        # Power-up system
        self.active_powerups = {}
        self.shield_active = False
        self.shield_time = 0
        self.health = 3
        self.max_health = 3
        self.invulnerable_time = 0

        self.jump_strength = 15  # Ridotto da 18 a 15 per un salto più controllato
        self.on_ground = False

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def apply_input(self, keys):
        accel = 1.5  # Aumentato da 1.2 per più controllo orizzontale
        max_speed = 10  # Aumentato da 8 per raggiungere piattaforme più distanti
        friction = 0.85
        if 'thermal_boost' in self.active_powerups:
            accel *= 1.5
            max_speed *= 1.3
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = max(-max_speed, self.vx - accel)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = min(max_speed, self.vx + accel)
        else:
            self.vx *= friction

    def jump(self):
        base_jump = -self.jump_strength
        if 'magma_jump' in self.active_powerups:
            base_jump *= 1.5
        self.vy = base_jump

    def update_physics(self, dt, gravity=0.8):
        max_fall_speed = 15
        if 'volcanic_time' in self.active_powerups:
            gravity *= 0.5
            max_fall_speed *= 0.7
        self.vy = min(self.vy + gravity, max_fall_speed)
        self.x += self.vx
        self.y += self.vy

        # Bordo orizzontale
        bounce_factor = 0.7
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * bounce_factor
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx) * bounce_factor

        # Trail
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.MAX_TRAIL:
            self.trail.pop()

        # Particelle
        if abs(self.vx) > 0.5 or abs(self.vy) > 0.5:
            for _ in range(1):
                self.particles.append([
                    self.x + random.uniform(-4,4),
                    self.y + random.uniform(-4,4),
                    random.uniform(1.8,3.6),
                    random.randint(18,34)
                ])
        for p in self.particles:
            p[1] += 1.5
            p[2] *= 0.96
            p[3] -= 1
        self.particles = [p for p in self.particles if p[3] > 0 and p[2] > 0.5]

    def update_powerups(self, dt):
        for powerup_type in list(self.active_powerups.keys()):
            self.active_powerups[powerup_type] -= dt
            if self.active_powerups[powerup_type] <= 0:
                del self.active_powerups[powerup_type]
        self.shield_active = 'gas_shield' in self.active_powerups
        if self.shield_active:
            self.shield_time += dt

    def update(self, dt):
        self.update_physics(dt)
        self.update_powerups(dt)
        if self.invulnerable_time > 0:
            self.invulnerable_time -= dt

    def draw_trail(self, surf):
        if not self.trail:
            return
        L = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = i / max(1, L-1)
            if t < 0.5:
                col = lerp_color((255,165,0),(255,0,0),t*2)
            else:
                col = lerp_color((255,0,0),(10,10,20),(t-0.5)*2)
            alpha = int(255 * (1 - t))
            size = int(self.radius * (0.5 + 0.5 * (1 - t)))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size, size), size)
            surf.blit(s, (tx - size, ty - size))

    def draw_particles(self, surf):
        for p in self.particles:
            alpha = max(0,int(255*(p[3]/34)))
            r = max(1,int(p[2]))
            s = pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(255,180,60,alpha),(r,r),r)
            surf.blit(s,(p[0]-r,p[1]-r))

    def draw_wobbly(self,surf,t):
        cx,cy = int(self.x),int(self.y)
        points=[]
        segments=32
        speed_factor=math.hypot(self.vx,self.vy)
        for i in range(segments):
            ang=i*(2*math.pi/segments)
            wobble=math.sin(t*6+i*0.7)*4.0
            r=self.radius*(1+wobble*0.01)*(0.95+min(0.2,speed_factor*0.02))
            x=cx+r*math.cos(ang)*(1+0.02*self.vx)
            y=cy+r*math.sin(ang)*(1-0.01*self.vy)
            points.append((x,y))
        pygame.draw.polygon(surf,self.color,points)
        pygame.draw.aalines(surf,(255,220,140),True,points,1)
