import pygame
import sys
import time
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TIME, 
                      MENU, PLAYING, GAME_OVER, SCORE_LIST, ENTER_NAME)
from player import WobblyBall
from platforms import PlatformManager
from background_manager import BackgroundManager
from levels import LevelManager, LEVEL_DEFS
from enemies import EnemyManager, penalties
from ui_system import UISystem
from save_system import add_score
from fountain import LavaParticle, SmokeParticle
import game_states

# --- Inizializza pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()

# --- Sistemi di gioco ---
ui_system = UISystem()

# --- Variabili globali ---
total_scroll_distance = 0
game_state = MENU
final_score = 0

# Variabili per la vittoria
victory_fountain_active = False
fountain_start_time = 0
fountain_particles = []
victory_timer = 0

# --- Istanze oggetti di gioco (create quando si inizia a giocare) ---
player = None
platform_manager = None
level_manager = None
background_manager = None
enemy_manager = None
cooling_time = 0

def calculate_score():
    """Calcola il punteggio basato sulla distanza percorsa e tempo rimanente."""
    distance_score = total_scroll_distance // 10  # 1 punto ogni 10 pixel
    time_bonus = max(0, cooling_time) * 10  # Bonus tempo
    return int(distance_score + time_bonus)

def init_game():
    """Inizializza una nuova partita."""
    global player, platform_manager, level_manager, background_manager, enemy_manager
    global total_scroll_distance, cooling_time, victory_fountain_active, fountain_start_time
    global fountain_particles, victory_timer
    
    player = WobblyBall(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    platform_manager = PlatformManager(num_platforms=10)
    level_manager = LevelManager(LEVEL_DEFS)
    background_manager = BackgroundManager()
    enemy_manager = EnemyManager()
    
    # Prima generazione piattaforme
    platform_manager.generate_initial_platforms(player)
    if platform_manager.platforms:
        first_platform = platform_manager.platforms[0]
        player.y = first_platform.rect.top - player.radius - 5
    
    total_scroll_distance = 0
    cooling_time = GAME_TIME
    
    # Reset vittoria
    victory_fountain_active = False
    fountain_start_time = 0
    fountain_particles = []
    victory_timer = 0

def update_fountain():
    """Aggiorna l'effetto fontana di vittoria."""
    global fountain_particles
    
    if not victory_fountain_active:
        return
    
    # Genera nuove particelle
    fountain_x = SCREEN_WIDTH // 2
    fountain_y = SCREEN_HEIGHT // 2  # Al centro dello schermo
    
    for _ in range(6):
        fountain_particles.append(LavaParticle(fountain_x, fountain_y))
    
    for _ in range(4):
        fountain_particles.append(SmokeParticle(fountain_x, fountain_y))
    
    # Aggiorna particelle esistenti
    for particle in fountain_particles:
        particle.update()
    
    # Rimuovi particelle vecchie
    fountain_particles = [p for p in fountain_particles 
                         if hasattr(p, 'age') and p.age < p.max_age or
                         hasattr(p, 'y') and p.y < SCREEN_HEIGHT + 50]

def draw_fountain(screen):
    """Disegna l'effetto fontana."""
    if not victory_fountain_active:
        return
    
    # Disegna prima il fumo, poi la lava
    smoke_particles = [p for p in fountain_particles if hasattr(p, 'age')]
    lava_particles = [p for p in fountain_particles if not hasattr(p, 'age')]
    
    for particle in smoke_particles:
        particle.draw(screen)
    
    for particle in lava_particles:
        particle.draw(screen)

def update_game(dt):
    """Aggiorna la logica di gioco."""
    global total_scroll_distance, game_state, final_score, victory_fountain_active
    global fountain_start_time, victory_timer, cooling_time
    
    if player is None:
        return
    
    # Controlla se ha raggiunto il cratere
    if background_manager and background_manager.check_crater_reached(total_scroll_distance):
        if not victory_fountain_active:
            victory_fountain_active = True
            fountain_start_time = time.time()
            print("🎉 VITTORIA! Cratere raggiunto!")
    
    # Se la fontana è attiva, aggiorna il timer della vittoria
    if victory_fountain_active:
        victory_timer = time.time() - fountain_start_time
        update_fountain()
        
        # Dopo 60 secondi (1 minuto) mostra schermata inserimento nome
        if victory_timer >= 60:
            final_score = calculate_score()
            ui_system.reset_input()
            game_state = ENTER_NAME
            return
    
    # Aggiorna player solo se non in modalità fontana
    if not victory_fountain_active:
        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update(dt)

        # Collisioni piattaforme
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
            dy = int(SCREEN_HEIGHT * 0.4 - player.y)
            player.y += dy
            platform_manager.update(dy)
            background_manager.update(dy)
            total_scroll_distance += dy
        
        # Aggiorna livello in base alla posizione
        level_manager.update(total_scroll_distance)

        # Aggiorna nemici
        enemy_manager.update()

        # Collisione nemici
        hits = enemy_manager.check_collision(player)
        for enemy in hits:
            cooling_time -= penalties.get(enemy.kind, 5)
            enemy_manager.enemies.remove(enemy)

        # Controllo game over
        if player.y - player.radius > SCREEN_HEIGHT or cooling_time <= 0:
            final_score = calculate_score()
            game_state = GAME_OVER

def draw_game(screen):
    """Disegna tutti gli elementi di gioco."""
    if player is None:
        return
        
    screen.fill((0, 0, 0))
    background_manager.draw(screen)
    platform_manager.draw(screen)
    
    # Se la fontana è attiva, non disegnare il player
    if not victory_fountain_active:
        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)
        enemy_manager.draw(screen)
    
    # Disegna la fontana se attiva
    draw_fountain(screen)

    # HUD
    font = pygame.font.SysFont(None, 30)
    
    if not victory_fountain_active:
        text_level = font.render(f"Livello: {level_manager.get_current_level()['name']}", True, (255, 255, 255))
        screen.blit(text_level, (10, 10))
        text_timer = font.render(f"Raffreddamento: {int(cooling_time)}s", True, (255, 180, 0))
        screen.blit(text_timer, (10, 40))
        
        # Punteggio in tempo reale
        current_score = calculate_score()
        score_text = font.render(f"Punteggio: {current_score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 70))
    else:
        # Messaggio vittoria con timer
        victory_text = font.render("🎉 CRATERE RAGGIUNTO! 🎉", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(victory_text, victory_rect)
        
        time_left = max(0, 60 - int(victory_timer))
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
            elif action == 1:  # Classifiche
                game_state = SCORE_LIST
            elif action == 2:  # Esci
                running = False
        
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not victory_fountain_active:
                    player.jump()
                elif event.key == pygame.K_ESCAPE:
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
                # Salva il punteggio
                add_score(ui_system.input_text.strip(), final_score)
                ui_system.reset_input()
                game_state = SCORE_LIST
    
    # --- Aggiornamenti ---
    if game_state == PLAYING:
        update_game(dt)
    
    # --- Rendering ---
    if game_state == MENU:
        ui_system.draw_menu(screen)
    
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
    
    pygame.display.flip()

pygame.quit()
sys.exit()
