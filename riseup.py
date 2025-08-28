import pygame, random, math, sys

pygame.init()

# ----------------- Window -----------------
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Volcano Jump - PNG Background")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)

# ----------------- Load Background Tiles -----------------
bg_tiles = [
    pygame.image.load("./RoundedBlocks/lava.png").convert(),
    pygame.image.load("./RoundedBlocks/stone.png").convert(),
    pygame.image.load("./RoundedBlocks/ground.png").convert_alpha()
]

# scale tiles
for i in range(len(bg_tiles)):
    bg_tiles[i] = pygame.transform.scale(bg_tiles[i], (WIDTH, HEIGHT))

# ----------------- Platforms -----------------
platforms = [
    pygame.Rect(100, 700, 64, 16),
    pygame.Rect(250, 600, 64, 16),
    pygame.Rect(400, 500, 64, 16),
    pygame.Rect(150, 400, 64, 16),
    pygame.Rect(300, 300, 64, 16),
]
platform_types = [0,1,0,2,0]

# Starting platform under player
start_platform = pygame.Rect(WIDTH//2 - 40, HEIGHT - 50, 80, 16)
platforms.insert(0, start_platform)
platform_types.insert(0,0)

# ----------------- WobblyBall -----------------
class WobblyBall:
    def __init__(self, x, y, radius=32, color=(255,165,0)):
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

    def apply_input(self, keys):
        speed = 5
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = speed
        else:
            self.vx = 0

    def update_physics(self, dt, gravity=0.8):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

        # horizontal walls
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = 0
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = 0

        # trail
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.MAX_TRAIL:
            self.trail.pop()

        # particles
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

        # wobble
        speed_factor = math.hypot(self.vx, self.vy)
        target_radius = self.base_radius * (1.0 + min(0.5, speed_factor*0.03))
        self.radius += (target_radius - self.radius) * 0.12

    def draw_trail(self, surf, orange=(255,165,0), red=(255,0,0), black=(10,10,20)):
        if not self.trail:
            return
        L = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = i / max(1, L-1)
            if t < 0.5:
                col = lerp_color(orange, red, t * 2)
            else:
                col = lerp_color(red, black, (t - 0.5) * 2)
            alpha = int(255 * (1 - t))
            size = int(self.radius * (0.5 + 0.5 * (1 - t)))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size, size), size)
            surf.blit(s, (tx - size, ty - size))

    def draw_particles(self, surf):
        for p in self.particles:
            alpha = max(0, int(255 * (p[3] / 34)))
            r = max(1, int(p[2]))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255,180,60,alpha), (r,r), r)
            surf.blit(s, (p[0]-r, p[1]-r))

    def draw_wobbly(self, surf, t):
        cx, cy = int(self.x), int(self.y)
        points = []
        segments = 32
        speed_factor = math.hypot(self.vx, self.vy)
        for i in range(segments):
            ang = i * (2*math.pi / segments)
            wobble = math.sin(t*6 + i*0.7) * 4.0
            r = self.radius * (1 + wobble*0.01) * (0.95 + min(0.2, speed_factor*0.02))
            x = cx + r * math.cos(ang) * (1.0 + 0.02*self.vx)
            y = cy + r * math.sin(ang) * (1.0 + -0.01*self.vy)
            points.append((x,y))
        pygame.draw.polygon(surf, self.color, points)
        pygame.draw.aalines(surf, (255,220,140), True, points, 1)

# ----------------- Utilities -----------------
def lerp_color(c1, c2, t):
    return (int(c1[0]*(1-t)+c2[0]*t),
            int(c1[1]*(1-t)+c2[1]*t),
            int(c1[2]*(1-t)+c2[2]*t))

def check_platform_collision(ball, platforms, world_offset):
    # collisione se scende o fermo appoggiato
    for i, plat in enumerate(platforms):
        plat_rect = plat.copy()
        plat_rect.y += world_offset
        if ball.x + ball.radius > plat_rect.left and ball.x - ball.radius < plat_rect.right:
            if ball.vy >= 0 and ball.y + ball.radius >= plat_rect.top and ball.y + ball.radius <= plat_rect.top + max(ball.vy,5):
                return True, i
    return False, None



def reset_game():
    global player, world_offset, score, GAME_OVER, tiles_revealed
    player.x = WIDTH//2
    player.y = HEIGHT - 100
    player.vx = player.vy = 0
    player.radius = player.base_radius
    player.trail.clear()
    player.particles.clear()
    world_offset = 0
    score = 0
    GAME_OVER = False
    tiles_revealed = 1  # mostra solo primo tile

def draw_background():
    # Mostra solo i tile in base al numero di salti
    for i in range(tiles_revealed):
        screen.blit(bg_tiles[i], (0,0))

# ----------------- Game Loop -----------------
player = WobblyBall(WIDTH//2, HEIGHT - 100)
world_offset = 0
t_global = 0
score = 0
GAME_OVER = False
tiles_revealed = 1  # solo primo tile inizialmente
jumps_made = 0

def main():
    global t_global, world_offset, score, GAME_OVER, tiles_revealed, jumps_made
    running = True
    while running:
        dt = clock.tick(60)/1000.0
        t_global += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    grounded, idx = check_platform_collision(player, platforms, world_offset)
                    if grounded and not GAME_OVER:
                        plat = platforms[idx]
                        player.y = plat.top - player.radius
                        if platform_types[idx] == 1:
                            player.vy = -22  # jump boost
                            jumps_made += 1
                        else:
                            player.vy = -15  # normal jump
                            jumps_made += 1
                            if platform_types[idx] == 2:
                                jumps_made += 1
                                player.radius = min(80, player.radius + 6)  # increase size on bouncy
                                score += 15

                if ev.key == pygame.K_r and GAME_OVER:
                    reset_game()

        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update_physics(dt)

        # scrolling
        SCROLL_THRESH = HEIGHT*0.35
        highest_platform_y = min([p.y + world_offset for p in platforms])
        if player.y < SCROLL_THRESH and player.y < highest_platform_y + 100:
            dy = SCROLL_THRESH - player.y
            world_offset += dy
            player.y = SCROLL_THRESH
            score += int(dy*0.2)

        # collision
        grounded, idx = check_platform_collision(player, platforms, world_offset)
        if grounded:
            plat = platforms[idx]
            player.y = plat.top - player.radius
            player.vy = 0
            player.radius = min(80, player.base_radius)  # reset radius when grounded

        # game over
        if player.y - player.radius > HEIGHT:
            GAME_OVER = True

        # ----------------- Draw -----------------
        screen.fill((0,0,0))
        draw_background()

        # draw platforms
        for i, plat in enumerate(platforms):
            rect = plat.copy()
            rect.y += world_offset
            if platform_types[i]==0:
                color=(150,80,40)
            elif platform_types[i]==1:
                color=(100,255,255)
            else:
                color=(255,100,200)
            pygame.draw.rect(screen, color, rect)

        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, t_global)

        txt = FONT.render(f"Score: {score}", True, (255,255,255))
        screen.blit(txt, (10,10))
        if GAME_OVER:
            txt = FONT.render("GAME OVER - Press R to restart", True, (255,0,0))
            screen.blit(txt, (WIDTH//2-140, HEIGHT//2))

        pygame.display.flip()

main()
pygame.quit()
sys.exit()
