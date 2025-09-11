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

# --- Variabile globale per tracciare lo scroll ---
total_scroll_distance = 0

# --- Istanza oggetti principali ---
player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)  # Posiziona il player più in alto
platform_manager = PlatformManager(num_platforms=10)
level_manager = LevelManager(LEVEL_DEFS)
background_manager = BackgroundManager()

# Prima generazione piattaforme
platform_manager.generate_initial_platforms(player)

# Posiziona il player sopra la prima piattaforma
if platform_manager.platforms:
    first_platform = platform_manager.platforms[0]
    player.y = first_platform.rect.top - player.radius - 5  # 5 pixel sopra la piattaforma

# --- Funzione reset ---
def reset_game():
    global player, platform_manager, level_manager, background_manager, total_scroll_distance
    player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)  # Posiziona il player più in alto
    platform_manager = PlatformManager(num_platforms=10)
    platform_manager.generate_initial_platforms(player=player)
    # Dopo aver generato le piattaforme, posiziona il player sopra la prima piattaforma
    if platform_manager.platforms:
        first_platform = platform_manager.platforms[0]
        player.y = first_platform.rect.top - player.radius - 5  # 5 pixel sopra la piattaforma
    level_manager.reset()
    background_manager.reset()
    total_scroll_distance = 0  # Reset anche la distanza scrollata

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
            elif event.key == pygame.K_SPACE and not game_over:
                # Permetti al player di saltare manualmente
                player.jump()

    if not game_over:
        # Aggiorna il player solo se non siamo in modalità cratere
        if not background_manager.is_crater_mode():
            keys = pygame.key.get_pressed()
            player.apply_input(keys)
            player.update(dt)

            # Collisioni con piattaforme
            platform_manager.check_collision(player)

            # Collisioni con le pareti del vulcano (livello 2 = Vulcano)
            if level_manager.current_index == 2:  # Solo nel livello vulcano
                background_manager.check_volcano_collision(player)
                # Controlla se il player ha raggiunto il cratere per attivare la fontana
                background_manager.check_crater_reached(player.y)

            # Limiti orizzontali (solo per livelli non-vulcano)
            if level_manager.current_index != 2:
                if player.x - player.radius < 50:
                    player.x = 50 + player.radius
                    player.vx = 0
                elif player.x + player.radius > SCREEN_WIDTH - 50:
                    player.x = SCREEN_WIDTH - 50 - player.radius
                    player.vx = 0

            # Scroll verticale
            if player.y < SCREEN_HEIGHT * 0.4:
                dy = int(SCREEN_HEIGHT * 0.4 - player.y)
                player.y += dy
                platform_manager.update(dy)
                background_manager.update(dy)
                
                # Traccia la distanza totale scrollata
                total_scroll_distance += dy

            # Aggiorna livello in base ai tile di background attraversati
            # Ogni tile è alto SCREEN_HEIGHT (800 pixel)
            # Ogni 3 tile si cambia livello
            old_level = level_manager.current_index
            
            # Calcola quanti tile sono stati attraversati
            tiles_passed = total_scroll_distance // SCREEN_HEIGHT
            level_index = int(tiles_passed // 3)  # Ogni 3 tile = 1 livello
            
            if level_index < len(LEVEL_DEFS):
                level_manager.current_index = level_index
                background_manager.current_index = level_index
            else:
                level_manager.current_index = len(LEVEL_DEFS) - 1
                background_manager.current_index = len(LEVEL_DEFS) - 1
                
            # Stampa messaggio se il livello è cambiato
            if old_level != level_manager.current_index:
                current_level = level_manager.get_current_level()
                print(f"🌋 LIVELLO CAMBIATO! Ora sei nel: {current_level['name']} (Livello {level_manager.current_index})")
                print(f"   Hai attraversato {tiles_passed} tile di background")
                
            # Debug: stampa informazioni livello ogni tanto
            if pygame.time.get_ticks() % 3000 < 16:  # Stampa ogni 3 secondi
                altitude = max(0, SCREEN_HEIGHT - 150 - player.y)
                print(f"Scroll: {total_scroll_distance:.0f}px, Tiles: {tiles_passed}, Level: {level_manager.current_index} ({level_manager.get_current_level()['name']})")

            # Controllo game over
            if player.y - player.radius > SCREEN_HEIGHT:
                game_over = True
        else:
            # In modalità cratere, controlla comunque se siamo nel vulcano per aggiornamenti di base
            if level_manager.current_index == 2:
                background_manager.check_crater_reached(player.y)

    # --- Draw ---
    screen.fill((0, 0, 0))
    background_manager.draw(screen)
    
    # Disegna piattaforme solo se non siamo in modalità cratere
    if not background_manager.is_crater_mode():
        platform_manager.draw(screen)
    
    # Disegna player (goccia) solo se non siamo in modalità cratere
    if not background_manager.is_crater_mode():
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
