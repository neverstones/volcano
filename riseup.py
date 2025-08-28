import pygame, random, math

pygame.init()
WIDTH, HEIGHT = 500, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wobbly Ball con Scia Gradiente")

clock = pygame.time.Clock()

# Proprietà palla
x, y = WIDTH // 2, HEIGHT // 2
vx = vy = 0
radius = 40
stretch_x = stretch_y = 1.0

# Colore iniziale
orange = (255, 165, 0)
red = (255, 0, 0)
black = (10, 10, 20)

# Scia
trail = []
MAX_TRAIL = 40

# Particelle
particles = []

class Particle:
    def __init__(self, x, y, color):
        self.x = x + random.uniform(-5,5)
        self.y = y + random.uniform(-5,5)
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-2, -0.5)
        self.life = random.randint(20, 40)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, int(255 * (self.life / 40)))
        s = pygame.Surface((6,6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (3,3), 3)
        surface.blit(s, (self.x, self.y))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    speed = 4
    vx = vy = 0
    if keys[pygame.K_LEFT]:  vx = -speed
    if keys[pygame.K_RIGHT]: vx = speed
    if keys[pygame.K_UP]:    vy = -speed
    if keys[pygame.K_DOWN]:  vy = speed

    x += vx
    y += vy
    stretch_x += (1.0 + vx*0.1 - stretch_x) * 0.2
    stretch_y += (1.0 + vy*0.1 - stretch_y) * 0.2
    stretch_x += (1.0 - stretch_x) * 0.05
    stretch_y += (1.0 - stretch_y) * 0.05

    trail.append((x, y))
    if len(trail) > MAX_TRAIL:
        trail.pop(0)

    if vx or vy:
        for _ in range(2):
            particles.append(Particle(x, y, orange))

    for p in particles[:]:
        p.update()
        if p.life <= 0:
            particles.remove(p)

    screen.fill(black)

    # Disegna scia (invertita: più grossa/luminosa vicino alla palla)
    for i, (tx, ty) in enumerate(reversed(trail)):
        t = i / len(trail)
        if t < 0.5:
            col = lerp_color(orange, red, t * 2)
        else:
            col = lerp_color(red, black, (t - 0.5) * 2)
        alpha = int(255 * (1 - t))
        size = int(radius * (1.0 - 0.7 * t))  # più grande vicino alla palla
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, alpha), (size, size), size)
        screen.blit(s, (tx - size, ty - size))

    for p in particles:
        p.draw(screen)

    ellipse_rect = pygame.Rect(0, 0, radius*2*stretch_x, radius*2*stretch_y)
    ellipse_rect.center = (x, y)
    pygame.draw.ellipse(screen, orange, ellipse_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()