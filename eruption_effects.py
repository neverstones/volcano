def draw_enhanced_background(world_offset):
    # Sfondo gradiente semplice
    from game_constants import screen as SCREEN, WIDTH, HEIGHT
    top_color = (50, 20, 20)
    bottom_color = (255, 100, 0)
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = (
            int(top_color[0] * (1-t) + bottom_color[0] * t),
            int(top_color[1] * (1-t) + bottom_color[1] * t),
            int(top_color[2] * (1-t) + bottom_color[2] * t)
        )
        pygame.draw.line(SCREEN, color, (0, y), (WIDTH, y))

def draw_hud(world_offset, score, current_level, player):
    from game_constants import screen as SCREEN, WIDTH, HEIGHT, level_names
    import game_constants
    height_km = world_offset / game_constants.PIXEL_PER_KM
    font = game_constants.FONT
    score_text = font.render(f"Punteggio: {score}", True, (255,255,255))
    SCREEN.blit(score_text, (10, HEIGHT-40))
    level_text = font.render(f"Livello: {level_names[current_level]}", True, (255,255,255))
    SCREEN.blit(level_text, (10, HEIGHT-60))
    height_text = font.render(f"Altezza: {height_km:.2f} km", True, (255,255,255))
    SCREEN.blit(height_text, (10, HEIGHT-80))

def draw_game_over(score):
    from game_constants import screen as SCREEN, WIDTH, HEIGHT
    import game_constants
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(160)
    SCREEN.blit(overlay, (0, 0))
    title = game_constants.TITLE_FONT.render("GAME OVER", True, (255, 0, 0))
    SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
    score_text = game_constants.FONT.render(f"Punteggio Finale: {score}", True, (255,255,255))
    SCREEN.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 20))
    restart_text = game_constants.SMALL_FONT.render("Premi R per ricominciare o ESC per il menu", True, (200,200,200))
    SCREEN.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 100))
import pygame, math, random
from game_constants import WIDTH, HEIGHT, KM_PER_LEVEL, LEVEL_VULCANO, screen as SCREEN

def draw_eruption_effects(crater_info, km_height):
    crater_left, crater_right, crater_top = crater_info
    crater_width = crater_right - crater_left
    crater_center = (crater_left + crater_right) // 2
    max_height = KM_PER_LEVEL[LEVEL_VULCANO]
    eruption_intensity = min(1.0, (km_height - max_height * 0.9) / (max_height * 0.1))
    current_time = pygame.time.get_ticks()
    wave = math.sin(current_time * 0.003) * 0.3 + 0.7
    effects_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    column_height = int(200 * eruption_intensity * wave)
    column_points = []
    base_width = crater_width * 0.7
    for y in range(column_height, 0, -10):
        progress = y / column_height
        width = base_width * (1 - progress * 0.7)
        wobble = math.sin(current_time * 0.005 + y * 0.1) * (20 * progress)
        left = crater_center - width/2 + wobble
        right = crater_center + width/2 + wobble
        column_points.append((left, crater_top - y))
        column_points.append((right, crater_top - y))
    if len(column_points) >= 4:
        for i in range(0, len(column_points) - 2, 2):
            points = [column_points[i], column_points[i+1], column_points[i+3], column_points[i+2]]
            progress = 1 - (i / len(column_points))
            alpha = int(200 * progress * eruption_intensity)
            color = (255, int(150 * progress + 50), 0, alpha)
            pygame.draw.polygon(effects_surface, color, points)
    # ...continua con particelle e altri effetti come nel file originale...
    # ...alla fine...
    # screen.blit(effects_surface, (0, 0))

def draw_lava_jet(center_x, crater_top_screen, t_ms):
    time_sec = t_ms / 1000.0
    main_pulse = math.sin(time_sec * 2.0) * 0.3 + 0.7
    secondary_wave = math.sin(time_sec * 5.0) * 0.2
    base_height = int(300 * main_pulse)
    base_width = int(50 + secondary_wave * 15)
    jet_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    num_streams = 12
    for stream in range(num_streams):
        stream_angle = (stream / num_streams) * math.pi * 2
        stream_offset = math.sin(time_sec * 3.0 + stream * 0.5) * 8
        stream_height = base_height + stream_offset
        stream_start_x = center_x + math.cos(stream_angle) * (base_width // 4)
        points = []
        for i in range(int(stream_height // 4)):
            progress = i / (stream_height // 4)
            y = crater_top_screen - i * 4
            lateral_movement = math.sin(progress * math.pi * 4 + time_sec * 4) * 20 * (1 - progress)
            x = stream_start_x + lateral_movement
            points.append((int(x), int(y)))
        if len(points) > 1:
            for i in range(len(points) - 1):
                progress = i / len(points)
                r = int(255 * (1 - progress * 0.3))
                g = int((200 - progress * 150) * main_pulse)
                b = int(50 * (1 - progress))
                alpha = int(255 * (1 - progress * 0.5) * main_pulse)
                thickness = max(1, int(8 * (1 - progress)))
                glow_surface = pygame.Surface((thickness * 4, thickness * 4), pygame.SRCALPHA)
                glow_color = (r, max(50, g), b, alpha // 3)
                pygame.draw.circle(glow_surface, glow_color, (thickness * 2, thickness * 2), thickness * 2)
                jet_surface.blit(glow_surface, (points[i][0] - thickness * 2, points[i][1] - thickness * 2))
                pygame.draw.circle(jet_surface, (r, g, b, alpha), points[i], thickness)
    # ...continua con altri effetti come nel file originale...
    # screen.blit(jet_surface, (0, 0))

def draw_transition_effects(progress, from_level, to_level, screen):
    if from_level == 0 and to_level == 1:
        num_effects = int(20 * progress)
        for _ in range(num_effects):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(5, 15)
            color_intensity = 1 - progress
            color = (int(255 * color_intensity), int(100 * color_intensity), 0)
            effect_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surface, (*color, int(100 * progress)), (size, size), size, 2)
            screen.blit(effect_surface, (x-size, y-size))
    elif from_level == 1 and to_level == 2:
        num_cracks = int(15 * progress)
        base_width = WIDTH * 0.85
        current_width = WIDTH * (0.9 - 0.1 * progress)
        passage_left = (WIDTH - current_width) / 2
        passage_right = WIDTH - passage_left
        for i in range(num_cracks):
            if i % 2 == 0:
                start_x = random.randint(int(passage_left - 30), int(passage_left + 10))
            else:
                start_x = random.randint(int(passage_right - 10), int(passage_right + 30))
            start_y = random.randint(0, HEIGHT)
            crack_points = [(start_x, start_y)]
            for j in range(random.randint(3, 8)):
                x = crack_points[-1][0] + random.randint(-15, 15)
                y = crack_points[-1][1] + random.randint(-15, 15)
                x = max(0, min(WIDTH, x))
                crack_points.append((x, y))
            if len(crack_points) > 1:
                pulse = math.sin(pygame.time.get_ticks() * 0.005 + i) * 0.3 + 0.7
                glow_intensity = progress * pulse
                glow_color = (255, int(150 * glow_intensity), 0)
                crack_color = (255, int(200 * glow_intensity), int(50 * glow_intensity))
                for k in range(len(crack_points) - 1):
                    pygame.draw.line(screen, glow_color, crack_points[k], crack_points[k+1], int(5 * glow_intensity))
                for k in range(len(crack_points) - 1):
                    pygame.draw.line(screen, crack_color, crack_points[k], crack_points[k+1], 2)
def draw_eruption_effects(crater_info, km_height):
    """Disegna gli effetti di eruzione usando le informazioni del cratere"""
    crater_left, crater_right, crater_top = crater_info
    
    # Calcola l'intensità dell'eruzione in base alla vicinanza al cratere
    max_height = KM_PER_LEVEL[LEVEL_VULCANO]
    eruption_intensity = min(1.0, (km_height - max_height * 0.9) / (max_height * 0.1))
    
    # Crea una superficie per gli effetti con alpha blending
    effects_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Disegna particelle di lava dal cratere
    num_particles = int(20 * eruption_intensity)
    for _ in range(num_particles):
        x = random.randint(int(crater_left), int(crater_right))
        y = random.randint(int(crater_top), int(crater_top + 100))
        size = random.randint(2, 6)
        alpha = random.randint(100, 200)
        color = (255, random.randint(100, 200), 0, alpha)
        pygame.draw.circle(effects_surface, color, (x, y), size)
    
    # Disegna un bagliore rosso intorno al cratere
    glow_surface = pygame.Surface((crater_right - crater_left, 100), pygame.SRCALPHA)
    glow_color = (255, 50, 0, int(100 * eruption_intensity))
    pygame.draw.rect(glow_surface, glow_color, (0, 0, crater_right - crater_left, 100))
    effects_surface.blit(glow_surface, (crater_left, crater_top))
    
    # Aggiungi colate di lava lungo le pareti
    num_flows = int(6 * eruption_intensity)
    for _ in range(num_flows):
        # Scegli un punto di partenza lungo il cratere
        start_x = random.randint(int(crater_left), int(crater_right))
        start_y = crater_top
        
        # Crea un percorso di lava che scende
        points = [(start_x, start_y)]
        current_x = start_x
        current_y = start_y
        
        for _ in range(random.randint(5, 15)):
            current_x += random.randint(-10, 10)
            current_y += random.randint(10, 20)
            # Mantieni il flusso entro i limiti del vulcano
            current_x = max(crater_left, min(crater_right, current_x))
            points.append((current_x, current_y))
        
        # Disegna il flusso di lava
        if len(points) > 1:
            lava_color = (255, random.randint(50, 150), 0, int(150 * eruption_intensity))
            pygame.draw.lines(effects_surface, lava_color, False, points, 3)
            
            # Aggiungi un bagliore attorno al flusso
            glow_color = (255, 50, 0, int(50 * eruption_intensity))
            pygame.draw.lines(effects_surface, glow_color, False, points, 5)
    
    # Applica gli effetti allo schermo
    SCREEN.blit(effects_surface, (0, 0))
