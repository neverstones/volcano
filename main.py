
import pygame
import random
import sys
from game_constants import LEVEL_VULCANO, WIDTH, HEIGHT, KM_PER_LEVEL, PIXEL_PER_KM, LEVEL_CROSTA, LEVEL_MANTELLO, save_score, game_state, player_name, high_scores
from logging_utils import log_game_event, debug_input_event
from level_volcano import create_static_platforms, build_conical_volcano_platforms, check_platform_collision, check_crater_entry, get_crater_info_from_conical_volcano, check_conical_volcano_walls_collision, check_volcano_tile_collision
from eruption_effects import draw_eruption_effects, draw_lava_jet, draw_enhanced_background, draw_hud, draw_game_over
from game_states import MENU, PLAYING, GAME_OVER, LEADERBOARD, ENTER_NAME
try:
    from level_volcano import draw_menu, draw_leaderboard, draw_name_input
except ImportError:
    def draw_menu():
        import game_constants
        screen = game_constants.screen
        WIDTH, HEIGHT = game_constants.WIDTH, game_constants.HEIGHT
        screen.fill((50, 20, 20))
        title = game_constants.TITLE_FONT.render("VOLCANO JUMP", True, (255, 165, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        subtitle = game_constants.FONT.render("Enhanced Edition", True, (255, 255, 255))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 210))
        menu_options = ["GIOCA", "CLASSIFICA", "ESCI"]
        selected_option = getattr(draw_menu, 'selected', 0)
        for i, option in enumerate(menu_options):
            color = (255, 200, 0) if i == selected_option else (255, 255, 255)
            text = game_constants.FONT.render(option, True, color)
            y = 350 + i * 50
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
        instructions = [
            "Usa FRECCE o WASD per muoverti",
            "SPAZIO per saltare",
            "Raccogli power-ups e cristalli!",
            "Evita i nemici vulcanici"
        ]
        for i, instruction in enumerate(instructions):
            text = game_constants.SMALL_FONT.render(instruction, True, (200, 200, 200))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 500 + i * 25))
    def draw_leaderboard():
        import game_constants
        screen = game_constants.screen
        WIDTH, HEIGHT = game_constants.WIDTH, game_constants.HEIGHT
        screen.fill((30, 30, 50))
        title = game_constants.TITLE_FONT.render("CLASSIFICA", True, (255, 215, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        if high_scores:
            for i, score_entry in enumerate(high_scores[:10]):
                y = 150 + i * 40
                name_text = game_constants.FONT.render(f"{i+1}. {score_entry['name']}", True, (255, 255, 255))
                score_text = game_constants.FONT.render(f"{score_entry['score']} ({score_entry['height']:.1f}km)", True, (255, 215, 0))
                date_text = game_constants.SMALL_FONT.render(score_entry['date'], True, (150, 150, 150))
                screen.blit(name_text, (50, y))
                screen.blit(score_text, (250, y))
                screen.blit(date_text, (450, y + 5))
        else:
            no_scores = game_constants.FONT.render("Nessun punteggio registrato", True, (150, 150, 150))
            screen.blit(no_scores, (WIDTH//2 - no_scores.get_width()//2, 300))
        back_text = game_constants.SMALL_FONT.render("Premi ESC per tornare al menu", True, (200, 200, 200))
        screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, HEIGHT - 50))
    def draw_name_input(): pass
try:
    from game_constants import reset_game
except ImportError:
    def reset_game():
        global game_state
        game_state = MENU

def main():
    global game_state, player_name, high_scores
    # Inizializzazione variabili globali
    t_global = 0.0
    world_offset = 0.0
    score = 0
    is_game_over = False
    tiles_revealed = 0
    jumps_made = 0
    current_level = LEVEL_MANTELLO
    eruption_mode = False
    eruption_award_given = False
    eruption_start_time = 0
    eruption_world_offset = None
    pygame.init()
    import game_constants
    game_constants.FONT = pygame.font.SysFont("Arial", 20)
    game_constants.TITLE_FONT = pygame.font.SysFont("Arial", 36, bold=True)
    game_constants.SMALL_FONT = pygame.font.SysFont("Arial", 16)
    game_constants.screen = pygame.display.set_mode((game_constants.WIDTH, game_constants.HEIGHT))
    pygame.display.set_caption("Volcano Jump - Enhanced Edition")
    game_constants.clock = pygame.time.Clock()
    # game_state, player_name, high_scores rimangono global se servono, le altre sono locali
    from audio import AudioManager
    from player import WobblyBall
    audio = AudioManager()
    platforms, platform_types, powerups, collectibles, enemies = create_static_platforms()
    VOLCANO_PLATFORMS = build_conical_volcano_platforms()
    player = WobblyBall(WIDTH//2, HEIGHT//2)

    menu_selected = 0
    running = True

    def start_new_game():
        nonlocal world_offset, score, is_game_over, tiles_revealed, jumps_made, current_level, eruption_mode, eruption_award_given, eruption_start_time, eruption_world_offset, player
        world_offset = 0.0
        score = 0
        is_game_over = False
        tiles_revealed = 1
        jumps_made = 0
        current_level = LEVEL_MANTELLO
        eruption_mode = False
        eruption_award_given = False
        eruption_start_time = 0
        eruption_world_offset = None
        # Posiziona il player sulla prima piattaforma
        start_platform = platforms[0]
        player.x = start_platform.centerx
        player.y = start_platform.top - player.radius

    while running:
        dt = game_constants.clock.tick(60)/1000.0
        t_global += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                debug_input_event(ev, "KEYDOWN")
                if game_state == MENU:
                    if ev.key == pygame.K_UP:
                        menu_selected = (menu_selected - 1) % 3
                    elif ev.key == pygame.K_DOWN:
                        menu_selected = (menu_selected + 1) % 3
                    elif ev.key == pygame.K_RETURN:
                        if menu_selected == 0:  # GIOCA
                            log_game_event("🎮 Inizia nuova partita")
                            start_new_game()
                            game_state = PLAYING
                        elif menu_selected == 1:  # CLASSIFICA
                            log_game_event("🏆 Visualizzazione classifica")
                            game_state = LEADERBOARD
                        elif menu_selected == 2:  # ESCI
                            log_game_event("👋 Uscita dal gioco")
                            running = False

                elif game_state == PLAYING:
                    if ev.key == pygame.K_SPACE and not eruption_mode:  # Non saltare durante l'eruzione
                        grounded, idx = check_platform_collision(player, platforms, world_offset)
                        if grounded:
                            player.jump()
                        else:
                            player.vy = -10

                elif game_state == GAME_OVER or (is_game_over and game_state == PLAYING):
                    if ev.key == pygame.K_r:
                        log_game_event("🔄 Riavvio partita...")
                        reset_game()  # reset_game si occuperà di impostare sia game_state che GAME_OVER
                    elif ev.key == pygame.K_ESCAPE:
                        log_game_event("🏠 Ritorno al menu principale")
                        game_state = MENU
                        is_game_over = False  # Resettiamo anche il flag quando torniamo al menu

                elif game_state == LEADERBOARD:
                    if ev.key == pygame.K_ESCAPE:
                        game_state = MENU

                elif game_state == ENTER_NAME:
                    if ev.key == pygame.K_RETURN:
                        height_km = world_offset / PIXEL_PER_KM
                        high_scores = save_score(player_name, score, height_km)
                        player_name = ""
                        game_state = LEADERBOARD
                    elif ev.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        if len(player_name) < 10 and ev.unicode.isprintable():
                            player_name += ev.unicode

            elif ev.type == pygame.KEYUP:
                debug_input_event(ev, "KEYUP")

        # Store menu selection for drawing
        draw_menu.selected = menu_selected

        if game_state == PLAYING:
            keys = pygame.key.get_pressed()
            if eruption_mode:
                if eruption_world_offset is not None:
                    world_offset = eruption_world_offset
                player.vx = 0
                player.vy = 0
            else:
                player.apply_input(keys)
                player.update_physics(dt)

            # Update game objects
            for powerup in powerups:
                powerup.update(dt)
                if powerup.check_collision(player):
                    if not powerup.collected:
                        powerup.collected = True
                        player.activate_powerup(powerup.type)
                        score += 200

            for collectible in collectibles:
                collectible.update(dt)
                if collectible.check_collision(player):
                    if not collectible.collected:
                        collectible.collected = True
                        score += collectible.value
                        audio.play('collect')

            for enemy in enemies:
                enemy.update(dt, world_offset)
                if enemy.check_collision(player):
                    if player.take_damage():
                        if player.health <= 0:
                            is_game_over = True
                            game_state = GAME_OVER
                            log_game_event("❌ GAME OVER - Salute esaurita!")

            # SCROLL
            SCROLL_THRESH = HEIGHT * 0.4
            SCROLL_SPEED = 0.3

            if not eruption_mode and player.y < SCROLL_THRESH:
                target_dy = SCROLL_THRESH - player.y
                actual_dy = target_dy * SCROLL_SPEED
                max_scroll = 15
                actual_dy = min(max_scroll, actual_dy)

                world_offset += actual_dy
                player.y += actual_dy
                score += int(actual_dy * 0.2)

                km_height = world_offset / PIXEL_PER_KM
                pass  # Rimosso debug scroll

                # Update level
                if km_height >= KM_PER_LEVEL[LEVEL_CROSTA]:
                    current_level = LEVEL_VULCANO
                    if tiles_revealed < 3:
                        tiles_revealed = 3
                elif km_height >= KM_PER_LEVEL[LEVEL_MANTELLO]:
                    current_level = LEVEL_CROSTA
                    if tiles_revealed < 2:
                        tiles_revealed = 2
                else:
                    current_level = LEVEL_MANTELLO

                # Eruzione attivata quando la goccia entra nel cratere (solo nella sezione vulcano)
                if (not eruption_mode and 
                    km_height >= KM_PER_LEVEL[LEVEL_CROSTA] and 
                    check_crater_entry(player, world_offset)):
                    eruption_mode = True
                    eruption_start_time = pygame.time.get_ticks()
                    eruption_award_given = False
                    # Blocca la camera sul cratere conico
                    crater_info = get_crater_info_from_conical_volcano(world_offset)
                    c_left, c_right, crater_top_screen = crater_info
                    eruption_world_offset = world_offset  # Mantieni posizione attuale
                    log_game_event("🌋 ERUZIONE INIZIATA! La goccia è entrata nel cratere!")

            km_height = world_offset / PIXEL_PER_KM
            # Collisioni
            grounded, idx = (False, None)
            landing_source = None  # 'base', 'volcano_surface', 'volcano_dynamic', or None
            if km_height < KM_PER_LEVEL[LEVEL_CROSTA]:
                grounded, idx = check_platform_collision(player, platforms, world_offset)
                if grounded:
                    landing_source = 'base'
            else:
                # Nel vulcano conico - controlla collisioni con pareti e piattaforme
                # 1) Prima controlla collisione con le pareti del vulcano conico
                wall_collision = check_conical_volcano_walls_collision(player, world_offset)
                if wall_collision:
                    # La goccia ha colpito una parete, respingila verso il centro
                    pass  # Gestito dentro la funzione
                
                # 2) Piattaforme di superficie del vulcano (ora coniche)
                grounded, idx = check_platform_collision(player, VOLCANO_PLATFORMS, world_offset)
                if grounded:
                    landing_source = 'volcano_surface'
                else:
                    # 3) Piattaforme dinamiche nella sezione vulcano
                    volcano_dyn_plats = [platforms[i] for i, t in enumerate(platform_types) if t == LEVEL_VULCANO]
                    grounded, idx = check_platform_collision(player, volcano_dyn_plats, world_offset)
                    if grounded:
                        landing_source = 'volcano_dynamic'
                    else:
                        # 4) Fallback: collisione diretta coi tile top (disabilitata per il nuovo design)
                        pass  # landed_tmp, _ = check_volcano_tile_collision(player, world_offset)
            if grounded and player.vy >= 0:
                # Se proviene da piattaforme
                if idx is not None and landing_source is not None:
                    if landing_source == 'base':
                        plat = platforms[idx]
                    elif landing_source == 'volcano_surface':
                        plat = VOLCANO_PLATFORMS[idx]
                    elif landing_source == 'volcano_dynamic':
                        volcano_dyn_plats = [platforms[i] for i, t in enumerate(platform_types) if t == LEVEL_VULCANO]
                        plat = volcano_dyn_plats[idx]
                    else:
                        plat = None
                    if plat is not None:
                        player.y = plat.top + world_offset - player.radius
                else:
                    # Controllo collisione tile vulcano per ottenere la Y di atterraggio
                    landed, landing_y = check_volcano_tile_collision(player, world_offset)
                    if landed and landing_y is not None:
                        player.y = landing_y - player.radius
                player.jump()

                # Particle effect
                player.particles.extend([
                    [player.x + random.uniform(-20,20),
                     player.y + player.radius,
                     random.uniform(1,3),
                     random.randint(20,30)]
                    for _ in range(5)
                ])

                # Game over condition - se la goccia esce dalla visuale
            screen_y = player.y - world_offset  # Calcoliamo la posizione sullo schermo
            if not eruption_mode and screen_y > HEIGHT + 50 and not is_game_over:  # Ridotto da 200 a 50 per un game over più reattivo
                is_game_over = True
                game_state = GAME_OVER
                log_game_event("❌ GAME OVER - La goccia è caduta nel vuoto!")
                # Aggiungiamo un messaggio per i controlli
                log_game_event("🎮 Premi R per riprovare o ESC per tornare al menu")
            # Check for high score
            if is_game_over and score > 0:
                is_high_score = False
                if not high_scores or score > high_scores[0]['score']:
                    is_high_score = True
                
                if is_high_score:
                    game_state = ENTER_NAME
                else:
                    game_state = GAME_OVER

        # ----------------- Drawing -----------------
        if game_state == MENU:
            draw_menu()
        elif game_state == LEADERBOARD:
            draw_leaderboard()
        elif game_state == ENTER_NAME:
            draw_name_input()
        elif game_state == PLAYING or game_state == GAME_OVER:
            # Game rendering
            game_constants.screen.fill((0,0,0))
            draw_enhanced_background(world_offset)
            # Non disegnamo più la mappa statica del vulcano perché ora usiamo il nuovo design conico
            # height_km = world_offset / PIXEL_PER_KM
            # if height_km >= KM_PER_LEVEL[LEVEL_CROSTA]:
            #     draw_volcano_static(screen, world_offset)
            #     # Se in eruzione, disegna fontana di lava continua dal cratere e colate sui fianchi
            #     if eruption_mode:
            #         crater_info = get_crater_info_from_static_map(world_offset)
            #         draw_eruption_effects(crater_info, height_km)

            # Draw platforms (fino alla crosta) e nel vulcano disegna sia superfici che piattaforme dinamiche
            if (world_offset / PIXEL_PER_KM) < KM_PER_LEVEL[LEVEL_CROSTA]:
                for i, plat in enumerate(platforms):
                    rect = plat.copy()
                    rect.y += world_offset
                    if -50 < rect.y < HEIGHT + 50:
                        plat_height_km = (plat.y + world_offset) / PIXEL_PER_KM
                        if plat_height_km >= KM_PER_LEVEL[LEVEL_CROSTA]:
                            color = (169, 169, 169)
                        elif plat_height_km >= KM_PER_LEVEL[LEVEL_MANTELLO]:
                            color = (139, 69, 19)
                        else:
                            color = (255, 100, 0)
                        pygame.draw.rect(game_constants.screen, color, rect)
            else:
                # Nel vulcano non disegnamo più le piattaforme perché usiamo il nuovo design conico
                # Le piattaforme sono ora integrate visivamente nelle pareti del vulcano conico
                pass
                # Piattaforme dinamiche nel vulcano (se necessarie per il gameplay)
                for i, plat in enumerate(platforms):
                    if platform_types[i] != LEVEL_VULCANO:
                        continue
                    rect = plat.copy()
                    rect.y += world_offset
                    if -50 < rect.y < HEIGHT + 50:
                        # Rendiamo le piattaforme più sottili e integrate nel design
                        pygame.draw.rect(game_constants.screen, (139, 69, 19), rect, 2)  # Solo bordo

            # Draw power-ups
            for powerup in powerups:
                powerup.draw(game_constants.screen, world_offset)

            # Draw collectibles
            for collectible in collectibles:
                collectible.draw(game_constants.screen, world_offset)

            # Draw enemies (evita durante eruzione per pulizia visiva)
            if not eruption_mode:
                for enemy in enemies:
                    enemy.draw(game_constants.screen, world_offset)

            # Draw player: durante eruzione, transizione graduale da goccia a fontana
            if not eruption_mode:
                player.draw_trail(game_constants.screen)
                player.draw_particles(game_constants.screen)
                player.draw_wobbly(game_constants.screen, t_global)
            else:
                # Durante l'eruzione, transizione graduale
                elapsed_ms = pygame.time.get_ticks() - eruption_start_time
                transition_duration = 2000  # 2 secondi di transizione
                
                if elapsed_ms < transition_duration:
                    # Fase di transizione - mostra entrambi con fade
                    transition_progress = elapsed_ms / transition_duration
                    
                    # Fade out della goccia
                    if transition_progress < 0.8:  # Goccia scompare nei primi 1.6 secondi
                        goccia_alpha = int(255 * (1 - transition_progress / 0.8))
                        # Disegna goccia con alpha decrescente
                        fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        player.draw_trail(fade_surface)
                        player.draw_particles(fade_surface)
                        player.draw_wobbly(fade_surface, t_global)
                        fade_surface.set_alpha(goccia_alpha)
                        game_constants.screen.blit(fade_surface, (0, 0))

            # Draw HUD
            draw_hud(world_offset, score, current_level, player)

            if game_state == GAME_OVER:
                draw_game_over(score)

            # Overlay eruzione: fontana al cratere e premio/leaderboard
            height_km = world_offset / PIXEL_PER_KM
            if height_km >= KM_PER_LEVEL[LEVEL_CROSTA] and eruption_mode:
                # Usa il nuovo cratere conico
                crater_info = get_crater_info_from_conical_volcano(world_offset)
                c_left, c_right, crater_top_screen = crater_info
                draw_eruption_effects(crater_info, height_km)
                center_x = (c_left + c_right) // 2
                draw_lava_jet(center_x, crater_top_screen, pygame.time.get_ticks())
                # Premio e transizione dopo 4s
                if not eruption_award_given:
                    score += 20000
                    eruption_award_given = True
                    log_game_event("🏔️ Cima raggiunta! Bonus +20000")
                if pygame.time.get_ticks() - eruption_start_time > 4000:
                    game_state = LEADERBOARD

        # Aggiorna lo schermo ad ogni frame
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()