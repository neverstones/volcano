import pygame
import random

# Inizializzazione
pygame.init()
LARGHEZZA, ALTEZZA = 600, 800
schermo = pygame.display.set_mode((LARGHEZZA, ALTEZZA))
pygame.display.set_caption("Magma Riser")
clock = pygame.time.Clock()

# Colori
ROSSO = (255, 50, 50)
GIALLO = (255, 255, 0)
BLU = (0, 150, 255)
NERO = (0, 0, 0)
BIANCO = (255, 255, 255)

# Costanti fisiche
gravity = 0.4
spinta = -10
friction = 0.98
fluidita_bonus = 1.5

# Magma
magma = pygame.Rect(LARGHEZZA//2 - 15, ALTEZZA - 50, 30, 30)
magma_vel = 0
viscosita = 1.0
raffreddamento = 100  # percentuale
fluid_timer = 0

# Mappa
scroll = 0
profondita = 0
font = pygame.font.SysFont(None, 32)

# Faglie e acqua
faglie = []
acqua = []

for i in range(20):
    x = random.randint(50, LARGHEZZA-50)
    y = random.randint(-3000, -50)
    if i % 3 == 0:
        acqua.append(pygame.Rect(x, y, 40, 20))
    else:
        faglie.append(pygame.Rect(x, y, 50, 20))

# Game loop
running = True
while running:
    clock.tick(60)
    schermo.fill(NERO)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    tasti = pygame.key.get_pressed()
    if tasti[pygame.K_SPACE] and raffreddamento > 0:
        magma_vel += spinta * (1.0 / viscosita)
        raffreddamento -= 0.2

    # Fisica del magma
    magma_vel += gravity
    magma_vel *= friction
    magma.y += int(magma_vel)

    # Raffreddamento
    if magma_vel > 5:
        raffreddamento -= 0.1
    if raffreddamento <= 0:
        running = False  # game over per raffreddamento

    # Fluidità da acqua
    if fluid_timer > 0:
        viscosita = 0.5
        fluid_timer -= 1
    else:
        viscosita = 1.0

    # Scroll
    if magma.y < ALTEZZA//2:
        offset = ALTEZZA//2 - magma.y
        magma.y = ALTEZZA//2
        scroll += offset
        profondita += offset
        for f in faglie:
            f.y += offset
        for a in acqua:
            a.y += offset

    # Collisioni
    for f in faglie:
        if magma.colliderect(f):
            magma_vel = spinta * 0.8

    for a in acqua:
        if magma.colliderect(a):
            fluid_timer = 180  # 3 secondi a 60 FPS

    # Disegno
    pygame.draw.rect(schermo, ROSSO, magma)
    for f in faglie:
        pygame.draw.rect(schermo, GIALLO, f)
    for a in acqua:
        pygame.draw.rect(schermo, BLU, a)

    barra = pygame.Rect(10, 10, int(raffreddamento * 2), 10)
    pygame.draw.rect(schermo, BIANCO, (10, 10, 200, 10), 1)
    pygame.draw.rect(schermo, ROSSO, barra)

    testo = font.render(f"Profondita risalita: {profondita} m", True, BIANCO)
    schermo.blit(testo, (10, 30))

    # Vittoria
    if profondita > 3000:
        testo = font.render("Eruzione riuscita!", True, GIALLO)
        schermo.blit(testo, (LARGHEZZA//2 - 100, ALTEZZA//2))
        pygame.display.flip()
        pygame.time.delay(3000)
        running = False

    pygame.display.flip()

pygame.quit()