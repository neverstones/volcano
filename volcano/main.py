import pygame
import os
import sys
import random
import time
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TIME, 
                      MENU, PLAYING, GAME_OVER, SCORE_LIST, ENTER_NAME)
from player import WobblyBall
from platforms import PlatformManager
from collectibles import Collectible, spawn_magma_bubbles_on_platforms, add_magma_bubble_for_platform, update_collectibles, draw_collectibles, check_collectibles_collision, get_world_offset, collectibles, block_on_demand_collectibles
from background_manager import BackgroundManager
from levels import LevelManager, LEVEL_DEFS
from enemies import EnemyManager, penalties
from ui_system import UISystem
from save_system import add_score
from fountain import Fountain, reset_victory_state, start_victory_fountain, update_victory_fountain, is_victory_active, get_victory_timer, get_fountain, set_victory_active
import game_states
from audio_manager import AudioManager

pygame.init()
try:
    pygame.mixer.init()
    print(f"DEBUG: mixer init -> {pygame.mixer.get_init()}")
except Exception as e:
    print(f"DEBUG: mixer init fallita: {e}")

# --- Inizializza pygame ---

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
audio_manager = AudioManager(os.path.join(os.path.dirname(__file__), 'audio'))
print(f"DEBUG: audio_manager.sounds = {audio_manager.sounds}")
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# --- Sistemi di gioco ---

ui_system = UISystem()
HOW_TO_PLAY = 10  # nuovo stato menu




# --- Variabili globali ---
total_scroll_distance = 0
game_state = MENU
final_score = 0
score = 0  # Punteggio reale, parte da 0



# --- Istanze oggetti di gioco (create quando si inizia a giocare) ---
player = None
platform_manager = None
level_manager = None
background_manager = None
enemy_manager = None
cooling_time = 0

def calculate_score():
    """Restituisce il punteggio reale basato solo sui collectibles raccolti."""
    return score

def init_game():
    # Reset tracking per punteggio salita
    update_game.last_score_scroll = 0
    """Inizializza una nuova partita."""
    global player, platform_manager, level_manager, background_manager, enemy_manager
    global total_scroll_distance, cooling_time, victory_fountain_active, fountain_start_time
    global victory_timer, score
    
    player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    platform_manager = PlatformManager(num_platforms=10)
    level_manager = LevelManager(LEVEL_DEFS)
    background_manager = BackgroundManager()
    enemy_manager = EnemyManager()
    
    # Collega il background manager al platform manager per i limiti del vulcano
    platform_manager.set_background_manager(background_manager)
    

    # Prima generazione piattaforme con livello (più profonda, stile Doodle Jump)
    platform_manager.generate_initial_platforms(player, level_manager, depth_multiplier=8)
    if platform_manager.platforms:
        first_platform = platform_manager.platforms[0]
        player.y = first_platform.rect.top - player.radius - 5

    # Genera bolle di magma sulle piattaforme
        spawn_magma_bubbles_on_platforms(platform_manager, density=1.0 if level_manager.get_current_level()['name'] == 'Mantello' else 0.8)
    
    total_scroll_distance = 0
    cooling_time = GAME_TIME  # 2 minuti
    score = 0
    # Reset vittoria
    reset_victory_state()



def update_game(dt):
    global score
    """Aggiorna la logica di gioco."""
    global total_scroll_distance, game_state, final_score, cooling_time

    if player is None:
        return

    # Aggiorna SEMPRE il movimento delle piattaforme mobili (anche senza scroll)
    platform_manager.update(0, level_manager)

    # Musica di background: Mantello o fontana
    current_level_name = level_manager.get_current_level()['name']
    if not hasattr(update_game, "last_bg_level"):
        update_game.last_bg_level = None
    if is_victory_active() and game_state != MENU:
        if update_game.last_bg_level != "ERUPTION":
            audio_manager.play_background_eruption(os.path.join(os.path.dirname(__file__), 'audio'))
            update_game.last_bg_level = "ERUPTION"
    elif update_game.last_bg_level == "ERUPTION" and game_state == MENU:
        audio_manager.stop_background()
        update_game.last_bg_level = None
    elif current_level_name == "Mantello" and update_game.last_bg_level != "Mantello":
        audio_manager.play_background_lava(os.path.join(os.path.dirname(__file__), 'audio'))
        update_game.last_bg_level = "Mantello"
    elif current_level_name == "Vulcano" and not is_victory_active() and update_game.last_bg_level != "WIND":
        audio_manager.play_background_wind(os.path.join(os.path.dirname(__file__), 'audio'))
        update_game.last_bg_level = "WIND"
    elif current_level_name != "Vulcano" and update_game.last_bg_level == "WIND":
        audio_manager.stop_background()
        update_game.last_bg_level = current_level_name
    elif current_level_name != "Mantello" and update_game.last_bg_level == "Mantello":
        audio_manager.stop_background()
        update_game.last_bg_level = current_level_name
    
    # Controlla se ha raggiunto il cratere
    if background_manager and background_manager.check_crater_reached(total_scroll_distance):
        if not is_victory_active():
            start_victory_fountain(SCREEN_WIDTH, SCREEN_HEIGHT)
            print("🎉 VITTORIA! Cratere raggiunto!")

    # Se la fontana è attiva, aggiorna il timer della vittoria e la fontana
    if is_victory_active():
        victory_timer = update_victory_fountain()
        if victory_timer >= 10:  # Cambiato da 60 a 10 secondi
            final_score = calculate_score()
            ui_system.reset_input()
            game_state = ENTER_NAME
            return
    
    # Decrementa il timer di raffreddamento nel tempo (solo se non in modalità vittoria)
    if not is_victory_active():
        cooling_time -= dt  # Sottrai il tempo trascorso (dt è in secondi)
    
    # Aggiorna player solo se non in modalità fontana
    if not is_victory_active():
        keys = pygame.key.get_pressed()
        # Suono salto
        if keys[pygame.K_SPACE] and hasattr(player, 'on_ground') and player.on_ground:
            audio_manager.play('jump')
        player.apply_input(keys)
        player.update(dt)

        # Collisioni piattaforme
        jump_automatico = platform_manager.check_collision(player)
        if jump_automatico:
            audio_manager.play('jump')

        # Collisioni con pareti del vulcano (solo nel livello vulcano)
        if level_manager.get_current_level()['name'] == "Vulcano":
            background_manager.check_volcano_collision(player)

        # Limiti orizzontali (solo se non siamo nel vulcano, che ha le sue pareti)
        if level_manager.get_current_level()['name'] != "Vulcano":
            if player.x - player.radius < 50:
                player.x = 50 + player.radius
                player.vx = 0
            elif player.x + player.radius > SCREEN_WIDTH - 50:
                player.x = SCREEN_WIDTH - 50 - player.radius
                player.vx = 0


        # Scroll verticale
        dy = 0
        if player.y < SCREEN_HEIGHT * 0.4:
            dy = int(SCREEN_HEIGHT * 0.4 - player.y)
            player.y += dy
            platform_manager.update(dy, level_manager)
            background_manager.update(dy, total_scroll_distance)
            total_scroll_distance += dy

            # Incrementa il punteggio ogni 100 pixel di salita (basato su total_scroll_distance)
            if not hasattr(update_game, "last_score_scroll"):
                update_game.last_score_scroll = 0
            while total_scroll_distance - update_game.last_score_scroll >= 100:
                score += 100
                update_game.last_score_scroll += 100

            # Quando vengono aggiunte nuove piattaforme, aggiungi bolle di magma solo se non bloccato
            global block_on_demand_collectibles
            if not block_on_demand_collectibles:
                for plat in platform_manager.platforms[-3:]:
                    if not any(abs(c.x - plat.rect.centerx) < 5 and abs(c.y - (plat.rect.top - 12)) < 5 for c in collectibles if c.type == 'magma_bubble'):
                        add_magma_bubble_for_platform(plat)

        # Aggiorna livello in base alla posizione
        old_level = level_manager.get_current_level()['name']
        level_manager.update(total_scroll_distance)
        new_level = level_manager.get_current_level()['name']
        if new_level != old_level:
            # Cambio livello immediato
            platform_manager.generate_initial_platforms(player, level_manager, depth_multiplier=8)
            spawn_magma_bubbles_on_platforms(platform_manager)
            block_on_demand_collectibles = True
        else:
            block_on_demand_collectibles = False

        # Aggiorna nemici (con offset per effetto salita)
        enemy_manager.update(dt, dy, total_scroll_distance, level_manager.get_current_level()['name'])

        # Collisione nemici
        hits = enemy_manager.check_collision(player)
        for enemy in hits:
            cooling_time -= penalties.get(enemy.kind, 5)
            print(f"DEBUG: collisione con nemico/minerale {enemy.kind}, timer abbassato a {cooling_time}")
            audio_manager.play('enemy_hit')
            print(f"DEBUG: chiamata audio_manager.play('enemy_hit')")
            enemy_manager.enemies.remove(enemy)

        # Controllo cratere raggiunto (solo nel livello vulcano)
        if level_manager.get_current_level()['name'] == "Vulcano" and not is_victory_active():
            if background_manager.check_crater_reached(player.y):
                set_victory_active(True)
                reset_victory_state()
                start_victory_fountain(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Aggiorna collezionabili
        update_collectibles(dt)

        # Gestione raccolta bolle di magma
        collected_score = check_collectibles_collision(player)
        if collected_score > 0:
            score += (collected_score // 200) * 100  # 100 punti per ogni bolla raccolta (valore 200)
            audio_manager.play('collect')

        # Se la fontana è attiva, aggiorna timer (fontana gestita automaticamente nel background_manager)
        if is_victory_active():
            victory_timer = update_victory_fountain()
            if victory_timer >= 10:
                final_score = calculate_score()
        if collected_score > 0:
            score += (collected_score // 200) * 100  # 100 punti per ogni bolla raccolta (valore 200)
            audio_manager.play('bubble')
            return

        # Controllo game over (solo se non in modalità vittoria)
        if not is_victory_active() and (player.y - player.radius > SCREEN_HEIGHT or cooling_time <= 0):
            final_score = calculate_score()
            game_state = GAME_OVER

def draw_game(screen):
    """Disegna tutti gli elementi di gioco."""
    if player is None:
        return
        
    screen.fill((0, 0, 0))
    background_manager.draw(screen)
    platform_manager.draw(screen)
    # Disegna le bolle di magma
    draw_collectibles(screen, get_world_offset(), platform_manager)
    
    # Se la fontana è attiva, non disegnare il player
    if not is_victory_active():
        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)
        enemy_manager.draw(screen)
    
    # Disegna la fontana di vittoria se attiva
    fountain = get_fountain()
    if is_victory_active() and fountain is not None:
        fountain.draw(screen)

    # HUD
    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 24)
    if not is_victory_active():
        # Livello e punteggio a sinistra
        text_level = font.render(f"Livello: {level_manager.get_current_level()['name']}", True, (255, 255, 255))
        screen.blit(text_level, (10, 10))

        current_score = calculate_score()
        score_text = font.render(f"Punteggio: {current_score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 40))

        # Barra di raffreddamento in alto a destra
        ui_system.draw_cooling_bar(screen, cooling_time, GAME_TIME)
    else:
        # Messaggio vittoria con timer
        victory_timer = get_victory_timer()
        victory_text = font.render("🎉 CRATERE RAGGIUNTO! 🎉", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(victory_text, victory_rect)

        time_left = max(0, 10 - int(victory_timer))  # Cambiato da 60 a 10
        timer_text = font.render(f"Inserimento nome tra: {time_left}s", True, (255, 255, 255))
        timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(timer_text, timer_rect)

# --- Loop principale ---
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    
    # Aggiorna UI
    ui_system.update(dt)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif game_state == MENU:
            action = ui_system.handle_menu_input(event)
            if action == 0:  # Gioca
                init_game()
                game_state = PLAYING
            elif action == 1:  # Come si gioca
                game_state = HOW_TO_PLAY
            elif action == 2:  # Classifiche
                game_state = SCORE_LIST
            elif action == 3:  # Esci
                running = False
        
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                # Salto con SPAZIO disabilitato temporaneamente
                if event.key == pygame.K_ESCAPE:
                    game_state = MENU
        
        elif game_state == GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    init_game()
                    game_state = PLAYING
                elif event.key == pygame.K_ESCAPE:
                    game_state = MENU
        
        elif game_state == SCORE_LIST:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = MENU
        
        elif game_state == ENTER_NAME:
            if ui_system.handle_name_input(event):
                from save_system import add_score, force_add_score, add_score_with_number
                name = ui_system.input_text.strip()
                result, scores = add_score(name, final_score)
                if result == 'duplicate':
                    font = pygame.font.SysFont(None, 32)
                    msg = f"Il nome '{name}' esiste già. Sovrascrivere? (S/N)"
                    text_surf = font.render(msg, True, (255,255,0))
                    screen.blit(text_surf, (50, 200))
                    pygame.display.flip()
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_s:
                                    force_add_score(name, final_score)
                                    ui_system.reset_input()
                                    game_state = SCORE_LIST
                                    waiting = False
                                elif event.key == pygame.K_n:
                                    add_score_with_number(name, final_score)
                                    ui_system.reset_input()
                                    game_state = SCORE_LIST
                                    waiting = False
                else:
                    # Nome non duplicato, salva normalmente
                    ui_system.reset_input()
                    game_state = SCORE_LIST
        elif game_state == HOW_TO_PLAY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = MENU
    
    # --- Aggiornamenti ---
    if game_state == PLAYING:
        update_game(dt)
    
    # --- Rendering ---
    if game_state == MENU:
        ui_system.draw_menu(screen)
    elif game_state == HOW_TO_PLAY:
        ui_system.draw_how_to_play(screen)
    elif game_state == PLAYING:
        draw_game(screen)
    elif game_state == GAME_OVER:
        if player is not None:
            draw_game(screen)  # Mostra il gioco in background
        ui_system.draw_game_over(screen)
    elif game_state == SCORE_LIST:
        ui_system.draw_scores(screen)
    elif game_state == ENTER_NAME:
        if player is not None:
            draw_game(screen)  # Mostra il gioco in background
        ui_system.draw_name_input(screen, final_score)

    # (RIMOSSO: la verifica duplicati ora avviene solo dopo INVIO)
    
    pygame.display.flip()

pygame.quit()
sys.exit()
