import pygame, random
from player import WobblyBall
from platforms import PlatformManager
from eruption_effects import draw_eruption_effects
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GRAVITY, LEVELS
from levels import LevelManager


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# ----- Level manager -----
level_manager = LevelManager(LEVELS)

# ----- Piattaforme manager -----
platforms = PlatformManager(num_platforms=10)


# ----- Player -----
player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

# ----- Platforms -----
platforms = PlatformManager(num_platforms=10)
platforms.generate_platforms(start_x=player.x, start_y=player.y)

# metto il player sopra la prima piattaforma
start_platform = platforms.platforms[0]
player.x = start_platform.rect.centerx
player.y = start_platform.rect.top - player.radius




# ----- Eruzione simulata -----
crater_info = (SCREEN_WIDTH//2 - 50, SCREEN_WIDTH//2 + 50, SCREEN_HEIGHT)

# ----- Main loop -----
running = True
game_over = False

while running:
    dt = clock.tick(FPS) / 1000.0
    t = pygame.time.get_ticks() / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                # Reset game
                start_platform = platforms.platforms[0]
                player = WobblyBall(start_platform.rect.centerx, start_platform.rect.top - 32)
                platforms.generate_platforms()
                game_over = False

    if not game_over:
        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update(dt)

    # --- Collisione con piattaforme + rimbalzo automatico ---
        if platforms.check_collision(player):
            player.jump()   # salto automatico in stile doodle jump

    # --- Scroll verticale ---
        if player.vy < 0 and player.y < SCREEN_HEIGHT * 0.4:
            dy = int((SCREEN_HEIGHT * 0.4 - player.y) * 0.5)
            player.y += dy
            platforms.update(dy)

    # --- Controllo game over ---
        if player.y - player.radius > SCREEN_HEIGHT:
            game_over = True

    # ----- Draw -----
    screen.fill((20, 20, 30))
    screen.blit(level_manager.get_background(), (0, 0))
    draw_eruption_effects(crater_info, km_height=50, screen=screen)
    platforms.draw(screen)
    player.draw_trail(screen)
    player.draw_particles(screen)
    if not game_over:
        player.draw_wobbly(screen, t)

    # Game Over message
    if game_over:
        font = pygame.font.Font(None, 74)
        text = font.render("Game Over", True, (255, 0, 0))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        font_small = pygame.font.Font(None, 48)
        text_r = font_small.render("Press R to Restart", True, (255, 0, 0))
        screen.blit(text_r, (SCREEN_WIDTH // 2 - text_r.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    pygame.display.flip()

pygame.quit()
