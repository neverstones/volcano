import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from player import WobblyBall
from platforms import PlatformManager
from background_manager import BackgroundManager
from levels import LevelManager, LEVEL_DEFS

# --- Inizializza pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# --- Istanza oggetti principali ---
player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
platform_manager = PlatformManager(num_platforms=10)
level_manager = LevelManager(LEVEL_DEFS)
background_manager = BackgroundManager()

# Prima generazione piattaforme
platform_manager.generate_platforms(player=player)

# --- Funzione reset ---
def reset_game():
    global player, platform_manager, level_manager, background_manager
    player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
    platform_manager = PlatformManager(num_platforms=10)
    platform_manager.generate_platforms(player=player)
    level_manager.reset()
    background_manager.reset()

# --- Loop principale ---
running = True
game_over = False

while running:
    dt = clock.tick(FPS) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                reset_game()
                game_over = False

    if not game_over:
        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update(dt)

        # Collisioni con piattaforme
        platform_manager.check_collision(player)

        # Limiti orizzontali
        if player.x - player.radius < 50:
            player.x = 50 + player.radius
            player.vx = 0
        elif player.x + player.radius > SCREEN_WIDTH - 50:
            player.x = SCREEN_WIDTH - 50 - player.radius
            player.vx = 0

        # Scroll verticale
        if player.y < SCREEN_HEIGHT * 0.4:
            dy = int((SCREEN_HEIGHT * 0.4 - player.y) * 0.5)
            player.y += dy
            platform_manager.update(dy)
            background_manager.update(dy)

        # Aggiorna livello in base all'altezza
        level_manager.update(player.y)
        background_manager.current_index = level_manager.current_index

        # Controllo game over
        if player.y - player.radius > SCREEN_HEIGHT:
            game_over = True

    # --- Draw ---
    screen.fill((0, 0, 0))
    background_manager.draw(screen)
    platform_manager.draw(screen)
    # Disegno player
    player.draw_trail(screen)
    player.draw_particles(screen)
    player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)


    # HUD livello
    font = pygame.font.SysFont(None, 30)
    text = font.render(f"Livello: {level_manager.get_current_level()['name']}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    # Messaggio Game Over
    if game_over:
        font_big = pygame.font.Font(None, 74)
        text_go = font_big.render("Game Over", True, (255, 0, 0))
        screen.blit(text_go, (SCREEN_WIDTH // 2 - text_go.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        font_small = pygame.font.Font(None, 48)
        text_r = font_small.render("Premi R per ricominciare", True, (255, 0, 0))
        screen.blit(text_r, (SCREEN_WIDTH // 2 - text_r.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    pygame.display.flip()

pygame.quit()
sys.exit()
