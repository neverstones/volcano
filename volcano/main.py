import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from player import WobblyBall
from platforms import PlatformManager
from background_manager import BackgroundManager
from levels import LevelManager, LEVEL_DEFS
from enemies import EnemyManager
from collectibles import CollectibleManager
from powerups import PowerUpManager
from save_system import ScoreSystem
from ui_system import MainMenu, VictoryScreen
from timer_system import CooldownTimer, ScorePopup

# --- Inizializza pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# --- Variabile globale per tracciare lo scroll ---
total_scroll_distance = 0

# --- Istanza oggetti principali ---
player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
platform_manager = PlatformManager(num_platforms=10)
level_manager = LevelManager(LEVEL_DEFS)
enemy_manager = EnemyManager()
collectible_manager = CollectibleManager()
powerup_manager = PowerUpManager()
background_manager = BackgroundManager()

# Sistema di salvataggio e UI
score_system = ScoreSystem()
main_menu = MainMenu(score_system)
victory_screen = VictoryScreen(score_system)

# Sistema timer e popup di punteggio
cooldown_timer = CooldownTimer()
score_popups = []

# Prima generazione piattaforme
platform_manager.generate_initial_platforms(player)

# Imposta i riferimenti ai manager per il controllo del vulcano
platform_manager.set_managers(background_manager, level_manager)

# Posiziona il player sopra la prima piattaforma
if platform_manager.platforms:
    first_platform = platform_manager.platforms[0]
    player.y = first_platform.rect.top - player.radius - 5

# Genera collectibles iniziali
collectible_manager.generate_random_collectibles(platform_manager.platforms, total_scroll_distance)

def reset_game():
    global player, platform_manager, level_manager, background_manager, total_scroll_distance, enemy_manager, collectible_manager, powerup_manager, cooldown_timer, score_popups
    player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    platform_manager = PlatformManager(num_platforms=10)
    platform_manager.set_managers(background_manager, level_manager)  # Ripristina i riferimenti
    platform_manager.generate_initial_platforms(player=player)
    # Dopo aver generato le piattaforme, posiziona il player sopra la prima piattaforma
    if platform_manager.platforms:
        first_platform = platform_manager.platforms[0]
        player.y = first_platform.rect.top - player.radius - 5
    level_manager.reset()
    background_manager.reset()
    enemy_manager.reset()
    collectible_manager.reset()
    powerup_manager.reset()
    cooldown_timer.reset()  # Reset del timer
    score_popups.clear()    # Pulisce i popup
    # Genera collectibles iniziali
    collectible_manager.generate_random_collectibles(platform_manager.platforms, 0)
    total_scroll_distance = 0

# --- Loop principale ---
game_state = "menu"  # "menu", "playing", "victory"
running = True
game_over = False

while running:
    dt = clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == "menu":
            action = main_menu.handle_input(event)
            if action == "play":
                game_state = "playing"
                reset_game()
                game_over = False
            elif action == "quit":
                running = False
        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                elif event.key == pygame.K_r:
                    reset_game()
                    game_over = False
        elif game_state == "victory":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    game_state = "menu"
    
    # Aggiornamento logica di gioco
    if game_state == "playing" and not game_over:
        # Aggiorna timer
        cooldown_timer.update(dt)
        
        # Controlla se il tempo è scaduto
        if cooldown_timer.is_expired():
            print("⏰ Tempo scaduto! Game Over!")
            game_over = True
        
        # Input del player
        keys = pygame.key.get_pressed()
        player.apply_input(keys)  # Usa il sistema di accelerazione graduale del player

        # Aggiorna player
        player.update(dt)

        # Collisioni con piattaforme
        platform_manager.check_collision(player)
        
        # Collisioni con nemici (causano danno al timer)
        hit_enemy = enemy_manager.check_collisions(player)
        if hit_enemy and player.take_damage():  # Solo se non è invulnerabile
            damage = hit_enemy.damage_seconds
            cooldown_timer.apply_damage(damage)
            print(f"💀 Colpito da {hit_enemy.name}! -{damage} secondi! Tempo rimanente: {cooldown_timer.get_remaining_time():.1f}s")
            
        # Collisioni con collectibles (con popup di punteggio)
        collected = collectible_manager.check_collisions(player)
        if collected:
            for collectible, value in collected:
                # Crea popup di punteggio nella posizione del collectible
                popup = ScorePopup(collectible.x, collectible.y, value)
                score_popups.append(popup)
            print(f"💎 Raccolti {len(collected)} oggetti! Punteggio: {collectible_manager.get_score()}")
            
        # Aggiorna e rimuovi popup scaduti
        score_popups = [popup for popup in score_popups if popup.update(dt)]
            
        # Collisioni con powerups
        powerups_collected = powerup_manager.check_collisions(player)
        if powerups_collected:
            print(f"⚡ Raccolti {len(powerups_collected)} powerups!")

        # Collisioni con le pareti del vulcano (livello 2 = Vulcano)
        if level_manager.current_index == 2:
            background_manager.check_volcano_collision(player)
            background_manager.check_crater_reached(player.y)

        # Limiti orizzontali (solo per livelli non-vulcano)
        if level_manager.current_index != 2:
            if player.x - player.radius < 0:
                player.x = player.radius
                player.vx = 0
            elif player.x + player.radius > SCREEN_WIDTH:
                player.x = SCREEN_WIDTH - player.radius
                player.vx = 0

        # Scroll verticale
        if player.y < SCREEN_HEIGHT * 0.4:
            dy = int(SCREEN_HEIGHT * 0.4 - player.y)
            player.y += dy
            platform_manager.update(dy)
            background_manager.update(dy)
            enemy_manager.update(dt, dy)
            collectible_manager.update(dt, dy)
            powerup_manager.update(dt, dy)
            
            total_scroll_distance += dy

        # Aggiorna livello in base ai tile di background attraversati
        old_level = level_manager.current_index
        tiles_passed = total_scroll_distance // SCREEN_HEIGHT
        level_index = int(tiles_passed // 3)
        
        if level_index < len(LEVEL_DEFS):
            level_manager.current_index = level_index
            background_manager.current_index = level_index
        else:
            level_manager.current_index = len(LEVEL_DEFS) - 1
            background_manager.current_index = len(LEVEL_DEFS) - 1
            
        # Genera nuovi collectibles quando cambia livello
        if old_level != level_manager.current_index:
            current_level = level_manager.get_current_level()
            print(f"🌋 LIVELLO CAMBIATO! Ora sei nel: {current_level['name']} (Livello {level_manager.current_index})")
            collectible_manager.generate_random_collectibles(platform_manager.platforms, total_scroll_distance)

        # Controlla vittoria (modalità cratere attiva) - ma aspetta un po'
        if background_manager.is_crater_mode():
            # Aspetta almeno 3 secondi prima di mostrare la vittoria per far vedere la fontana
            if not hasattr(background_manager, 'crater_victory_timer'):
                background_manager.crater_victory_timer = 0
            
            background_manager.crater_victory_timer += dt
            
            # Dopo 3 secondi nel cratere, attiva la vittoria
            if background_manager.crater_victory_timer >= 3.0:
                final_score = collectible_manager.get_score()
                victory_screen.reset()
                game_state = "victory"
            
        # Game over se il player cade troppo in basso
        if player.y > SCREEN_HEIGHT + 200:
            game_over = True
    
    elif game_state == "victory":
        # Aggiorna schermata di vittoria
        final_score = collectible_manager.get_score()
        level_reached = level_manager.current_index
        collectibles_collected = len([c for c in collectible_manager.collectibles if c.collected])
        
        if victory_screen.update(dt, final_score, level_reached, collectibles_collected):
            game_state = "menu"

    # Rendering
    if game_state == "menu":
        main_menu.draw(screen)
    elif game_state == "playing":
        screen.fill((0, 0, 0))
        background_manager.draw(screen)
        
        # Disegna solo se non siamo in modalità cratere
        if not background_manager.is_crater_mode():
            platform_manager.draw(screen)
            enemy_manager.draw(screen)
            collectible_manager.draw(screen)
            powerup_manager.draw(screen)
            player.draw_trail(screen)
            player.draw_particles(screen)
            
            # Effetto lampeggiante durante invulnerabilità
            if player.is_invulnerable():
                # Lampeggia ogni 0.1 secondi
                if int(pygame.time.get_ticks() / 100) % 2 == 0:
                    player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)
            else:
                player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)

        # HUD
        font = pygame.font.SysFont(None, 30)
        level_text = font.render(f"Livello: {level_manager.get_current_level()['name']}", True, (255, 255, 255))
        screen.blit(level_text, (10, 10))
        
        score_text = font.render(f"Punteggio: {collectible_manager.get_score()}", True, (255, 255, 255))
        screen.blit(score_text, (10, 40))
        
        # Disegna timer di raffreddamento
        cooldown_timer.draw(screen)
        
        # Disegna popup di punteggio
        for popup in score_popups:
            popup.draw(screen)
        
        # Mostra messaggio nel cratere
        if background_manager.is_crater_mode() and hasattr(background_manager, 'crater_victory_timer'):
            font_big = pygame.font.SysFont(None, 48)
            time_left = max(0, 3.0 - background_manager.crater_victory_timer)
            if time_left > 0:
                message = f"🌋 CRATERE RAGGIUNTO! Fontana di lava! Vittoria tra {time_left:.1f}s"
                text = font_big.render(message, True, (255, 255, 0))
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100))
                # Sfondo semi-trasparente
                bg_surface = pygame.Surface((text_rect.width + 20, text_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (0, 0, 0, 150), bg_surface.get_rect())
                screen.blit(bg_surface, (text_rect.x - 10, text_rect.y - 5))
                screen.blit(text, text_rect)

        # Game over overlay
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            font_big = pygame.font.Font(None, 74)
            text_go = font_big.render("Game Over", True, (255, 0, 0))
            screen.blit(text_go, (SCREEN_WIDTH // 2 - text_go.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            font_small = pygame.font.Font(None, 48)
            text_r = font_small.render("R - Restart, ESC - Menu", True, (255, 0, 0))
            screen.blit(text_r, (SCREEN_WIDTH // 2 - text_r.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
    
    elif game_state == "victory":
        final_score = collectible_manager.get_score()
        level_reached = level_manager.current_index
        collectibles_collected = len([c for c in collectible_manager.collectibles if c.collected])
        victory_screen.draw(screen, final_score, level_reached, collectibles_collected)

    pygame.display.flip()

pygame.quit()
sys.exit()
