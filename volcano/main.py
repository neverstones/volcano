import pygame
from player import WobblyBall
from platforms import PlatformManager
from eruption_effects import draw_eruption_effects
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from background_manager import BackgroundManager

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# ----- Background manager -----
background_manager = BackgroundManager()

# ----- Player iniziale -----
player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)

# ----- Piattaforme manager -----
platforms = PlatformManager(num_platforms=10)
platforms.generate_platforms(player=player)

# ----- Eruzione simulata -----
crater_info = (SCREEN_WIDTH // 2 - 50, SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT)

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
                player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
                platforms.generate_platforms(player=player)
                game_over = False

    if not game_over:
        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update(dt)

        # Collisione con piattaforme
        platforms.check_collision(player)

        # Limiti orizzontali (area d'azione)
        if player.x - player.radius < 50:   # margine sinistro
            player.x = 50 + player.radius
            player.vx = 0
        elif player.x + player.radius > SCREEN_WIDTH - 50:  # margine destro
            player.x = SCREEN_WIDTH - 50 - player.radius
            player.vx = 0

        # Scroll verticale (quando il player sale)
        if player.vy < 0 and player.y < SCREEN_HEIGHT * 0.4:
            dy = int((SCREEN_HEIGHT * 0.4 - player.y) * 0.5)
            player.y += dy
            platforms.update(dy)
            background_manager.update(dy)   # 🔥 aggiorna lo sfondo insieme alle piattaforme


        # Controllo game over (caduta fuori schermo)
        if player.y - player.radius > SCREEN_HEIGHT:
            game_over = True

    # ----- Draw -----
    screen.fill((20, 20, 30))
    background_manager.draw(screen)
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
