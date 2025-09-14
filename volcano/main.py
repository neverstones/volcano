import pygame
import sys
import random
import time
from constants import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TIME, 
                      MENU, PLAYING, GAME_OVER, SCORE_LIST, ENTER_NAME)
from player import WobblyBall
from platforms import PlatformManager
from collectibles import Collectible
from background_manager import BackgroundManager
from levels import LevelManager, LEVEL_DEFS
from enemies import EnemyManager, penalties
from ui_system import UISystem
from save_system import add_score
from fountain import Fountain
import game_states

# --- Inizializza pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Volcano Wobbly Jump")
clock = pygame.time.Clock()


# --- Sistemi di gioco ---

ui_system = UISystem()
HOW_TO_PLAY = 10  # nuovo stato menu


# --- Collezionabili ---
collectibles = []
# Flag per bloccare la generazione on demand subito dopo cambio livello
block_on_demand_collectibles = False

def spawn_magma_bubbles_on_platforms():
    """Posiziona una bolla di magma su ogni piattaforma di ogni livello, senza offset y."""
    global collectibles
    collectibles = []
    for plat in platform_manager.platforms:
        # Solo su alcune piattaforme (es. 80% di probabilità)
        if random.random() < 0.8:
            if not any(c.type == 'magma_bubble' and c.platform == plat for c in collectibles):
                x = plat.rect.centerx
                # Posiziona la bolla completamente sopra la piattaforma lasciando uno spazio
                radius = 10  # Deve corrispondere a Collectible.radius
                offset = 16  # Spazio extra tra piattaforma e bolla
                y = plat.rect.top - offset - radius
                bubble = Collectible(x, y, value=200)
                bubble.type = 'magma_bubble'
                bubble.platform = plat  # Associa la piattaforma
                collectibles.append(bubble)

def add_magma_bubble_for_platform(plat):
    """Aggiunge una bolla di magma su ogni nuova piattaforma, senza offset y."""
    # Solo su alcune piattaforme (es. 80% di probabilità)
    if random.random() < 0.8:
        if not any(c.type == 'magma_bubble' and c.platform == plat for c in collectibles):
            x = plat.rect.centerx
            radius = 10  # Deve corrispondere a Collectible.radius
            offset = 16  # Spazio extra tra piattaforma e bolla
            y = plat.rect.top - offset - radius
            bubble = Collectible(x, y, value=200)
            bubble.type = 'magma_bubble'
            bubble.platform = plat  # Associa la piattaforma
            collectibles.append(bubble)

def update_collectibles(dt):
    for c in collectibles:
        c.update(dt)

def draw_collectibles(screen, world_offset):
    # Rimuovi collectibles che sono completamente fuori dallo schermo in basso
    global collectibles
    # Rimuovi collectibles che sono completamente fuori dallo schermo in basso rispetto al world_offset
    # Pruning centralizzato in collectibles.py
    from collectibles import prune_orphaned_or_offscreen
    prune_orphaned_or_offscreen(collectibles, platform_manager, world_offset, SCREEN_HEIGHT)
    for c in collectibles:
        c.draw(screen, world_offset)

def check_collectibles_collision(player):
    global collectibles
    collected = 0
    for c in collectibles:
        if not c.collected and c.type == 'magma_bubble' and c.check_collision(player):
            c.collected = True
            c.trigger_float_text(f'+{c.value}')
            collected += c.value
    return collected

def get_world_offset():
    # Calcola l'offset verticale del mondo per disegnare i collezionabili
    # Si basa sulla posizione del player e sullo scroll
    return 0  # Se serve, puoi implementare uno scroll effettivo


# --- Variabili globali ---
total_scroll_distance = 0
game_state = MENU
final_score = 0
score = 0  # Punteggio reale, parte da 0

# Variabili per la vittoria
victory_fountain_active = False
fountain_start_time = 0
victory_timer = 0
fountain = None

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
    spawn_magma_bubbles_on_platforms()
    
    total_scroll_distance = 0
    cooling_time = GAME_TIME
    score = 0
    # Reset vittoria
    victory_fountain_active = False
    fountain_start_time = 0
    victory_timer = 0
    global fountain
    fountain = None


def draw_cooling_bar(screen, current_time, max_time):
    """Disegna la barra di raffreddamento in alto a destra."""
    # Dimensioni e posizione della barra
    bar_width = 200
    bar_height = 20
    bar_x = SCREEN_WIDTH - bar_width - 20
    bar_y = 20
    
    # Calcola la percentuale di raffreddamento rimanente
    percentage = max(0, current_time / max_time)
    fill_width = int(bar_width * percentage)
    
    # Colori basati sulla percentuale rimanente
    if percentage > 0.6:
        bar_color = (0, 255, 0)  # Verde
    elif percentage > 0.3:
        bar_color = (255, 255, 0)  # Giallo
    else:
        bar_color = (255, 0, 0)  # Rosso
    
    # Disegna il bordo della barra
    border_rect = pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4)
    pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)
    
    # Disegna lo sfondo della barra (grigio scuro)
    background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, (40, 40, 40), background_rect)
    
    # Disegna il riempimento della barra
    if fill_width > 0:
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, bar_color, fill_rect)
        
        # Effetto gradiente (opzionale)
        for i in range(bar_height):
            alpha = 255 - int((i / bar_height) * 100)
            gradient_color = (*bar_color, alpha)
            if i < fill_width:
                gradient_surface = pygame.Surface((fill_width, 1), pygame.SRCALPHA)
                gradient_surface.fill(gradient_color)
                screen.blit(gradient_surface, (bar_x, bar_y + i))
    
    # Testo "Raffreddamento" sopra la barra
    font = pygame.font.SysFont(None, 24)
    label_text = font.render("Raffreddamento", True, (255, 255, 255))
    label_rect = label_text.get_rect()
    label_rect.centerx = bar_x + bar_width // 2
    label_rect.bottom = bar_y - 5
    screen.blit(label_text, label_rect)
    
    # Timer sotto la barra in formato MM:SS
    timer_font = pygame.font.SysFont(None, 20)
    time_remaining = max(0, int(current_time))
    minutes = time_remaining // 60
    seconds = time_remaining % 60
    timer_text = timer_font.render(f"{minutes:02d}:{seconds:02d}", True, (255, 180, 0))
    timer_rect = timer_text.get_rect()
    timer_rect.centerx = bar_x + bar_width // 2
    timer_rect.top = bar_y + bar_height + 5
    screen.blit(timer_text, timer_rect)

def update_game(dt):
    """Aggiorna la logica di gioco."""
    global total_scroll_distance, game_state, final_score, victory_fountain_active
    global fountain_start_time, victory_timer, cooling_time

    if player is None:
        return

    # Aggiorna SEMPRE il movimento delle piattaforme mobili (anche senza scroll)
    platform_manager.update(0, level_manager)
    
    # Controlla se ha raggiunto il cratere
    if background_manager and background_manager.check_crater_reached(total_scroll_distance):
        if not victory_fountain_active:
            victory_fountain_active = True
            fountain_start_time = time.time()
            global fountain
            fountain = Fountain(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            print("🎉 VITTORIA! Cratere raggiunto!")
    
    # Se la fontana è attiva, aggiorna il timer della vittoria e la fontana
    if victory_fountain_active:
        victory_timer = time.time() - fountain_start_time
        if fountain is not None:
            fountain.emit()
            fountain.update()
        # Dopo 10 secondi mostra schermata inserimento nome
        if victory_timer >= 10:  # Cambiato da 60 a 10 secondi
            final_score = calculate_score()
            ui_system.reset_input()
            game_state = ENTER_NAME
            return
    
    # Decrementa il timer di raffreddamento nel tempo (solo se non in modalità vittoria)
    if not victory_fountain_active:
        cooling_time -= dt  # Sottrai il tempo trascorso (dt è in secondi)
    
    # Aggiorna player solo se non in modalità fontana
    if not victory_fountain_active:
        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update(dt)

        # Collisioni piattaforme
        platform_manager.check_collision(player)

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
            # Cambio livello: NON rigenerare piattaforme, mantieni quelle esistenti
            # Puoi eventualmente aggiungere collectibles sulle nuove piattaforme se necessario
            spawn_magma_bubbles_on_platforms()
            block_on_demand_collectibles = True
        else:
            block_on_demand_collectibles = False

        # Aggiorna nemici (con offset per effetto salita)
        enemy_manager.update(dt, dy, total_scroll_distance)

        # Collisione nemici
        hits = enemy_manager.check_collision(player)
        for enemy in hits:
            cooling_time -= penalties.get(enemy.kind, 5)
            enemy_manager.enemies.remove(enemy)

        # Controllo cratere raggiunto (solo nel livello vulcano)
        if level_manager.get_current_level()['name'] == "Vulcano" and not victory_fountain_active:
            if background_manager.check_crater_reached(player.y):
                victory_fountain_active = True
                victory_timer = 0.0
                fountain_start_time = time.time()

        # Aggiorna collezionabili
        update_collectibles(dt)

        # Gestione raccolta bolle di magma
        global score
        collected_score = check_collectibles_collision(player)
        if collected_score > 0:
            score += (collected_score // 200) * 100  # 100 punti per ogni bolla raccolta (valore 200)

        # Se la fontana è attiva, aggiorna timer (fontana gestita automaticamente nel background_manager)
        if victory_fountain_active:
            victory_timer = time.time() - fountain_start_time
            # La fontana viene aggiornata automaticamente nel background_manager.draw()
            
            # Dopo 10 secondi mostra schermata inserimento nome
            if victory_timer >= 10:  # Cambiato da 60 a 10 secondi
                final_score = calculate_score()
                ui_system.reset_input()
                game_state = ENTER_NAME
                return

        # Controllo game over (solo se non in modalità vittoria)
        if not victory_fountain_active and (player.y - player.radius > SCREEN_HEIGHT or cooling_time <= 0):
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
    draw_collectibles(screen, get_world_offset())
    
    # Se la fontana è attiva, non disegnare il player
    if not victory_fountain_active:
        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, pygame.time.get_ticks() / 1000.0)
        enemy_manager.draw(screen)
    
    # Disegna la fontana di vittoria se attiva
    if victory_fountain_active and fountain is not None:
        fountain.draw(screen)

    # HUD
    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 24)
    
    if not victory_fountain_active:
        # Livello e punteggio a sinistra
        text_level = font.render(f"Livello: {level_manager.get_current_level()['name']}", True, (255, 255, 255))
        screen.blit(text_level, (10, 10))

        current_score = calculate_score()
        score_text = font.render(f"Punteggio: {current_score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 40))

        # Barra di raffreddamento in alto a destra
        draw_cooling_bar(screen, cooling_time, GAME_TIME)
    else:
        # Messaggio vittoria con timer
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
                    import pygame
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
