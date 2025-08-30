import pygame, random, math, sys
import logging
from datetime import datetime

pygame.init()

# Configurazione del logging
log_filename = f"volcano_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

def log_debug(message):
    print(f"DEBUG - {message}")
    logging.debug(message)

# ----------------- Window -----------------
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Volcano Jump - PNG Background")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)

# ----------------- Game Levels -----------------
LEVEL_MANTELLO = 0
LEVEL_CROSTA = 1
LEVEL_VULCANO = 2

level_names = ["Mantello", "Crosta Terrestre", "Vulcano"]

# Definizione della mappa come lista di coordinate
# Formato: (x, y_offset, livello)
# x: posizione orizzontale
# y_offset: distanza dalla piattaforma precedente
# livello: 0=mantello, 1=crosta, 2=vulcano
GAME_MAP = [
    # Piattaforma iniziale
    (WIDTH//2 - 50, 50, 0),  # Piattaforma di partenza più larga
    
    # Livello Mantello
    (100, 120, 0),    (400, 100, 0),
    (200, 120, 0),    (450, 100, 0),
    (150, 120, 0),    (380, 100, 0),
    (250, 120, 0),    (420, 100, 0),
    (180, 120, 0),    (350, 100, 0),
    (120, 120, 0),    (400, 100, 0),
    (220, 120, 0),    (380, 100, 0),
    (150, 120, 0),    (450, 100, 0),
    
    # Livello Crosta
    (200, 120, 1),    (420, 100, 1),
    (150, 120, 1),    (380, 100, 1),
    (250, 120, 1),    (420, 100, 1),
    (180, 120, 1),    (350, 100, 1),
    (120, 120, 1),    (400, 100, 1),
    (220, 120, 1),    (380, 100, 1),
    (150, 120, 1),    (450, 100, 1),
    (200, 120, 1),    (400, 100, 1),
    
    # Livello Vulcano
    (200, 120, 2),    (420, 100, 2),
    (150, 120, 2),    (380, 100, 2),
    (250, 120, 2),    (420, 100, 2),
    (180, 120, 2),    (350, 100, 2),
    (120, 120, 2),    (400, 100, 2),
    (220, 120, 2),    (380, 100, 2),
    (150, 120, 2),    (450, 100, 2),
    (200, 120, 2),    (400, 100, 2),
]

# Altezze dei livelli calcolate in base alla mappa
def calculate_level_heights():
    heights = [0, 0, 0]  # mantello, crosta, vulcano
    current_height = 0
    
    for _, y_offset, level in GAME_MAP:
        current_height += y_offset
        heights[level] = max(heights[level], current_height)
    
    return heights

level_heights = calculate_level_heights()
MANTELLO_END = level_heights[0]
CROSTA_END = level_heights[1]
VULCANO_END = level_heights[2]

level_colors = [
    (255, 100, 0),    # Mantello: rosso-arancio caldo
    (139, 69, 19),    # Crosta: marrone
    (169, 169, 169)   # Vulcano: grigio
]

# ----------------- Load Background Tiles -----------------
bg_tiles = [
    pygame.image.load("./RoundedBlocks/lava.png").convert(),    # mantello
    pygame.image.load("./RoundedBlocks/stone.png").convert(),   # crosta
    pygame.image.load("./RoundedBlocks/ground.png").convert_alpha()  # vulcano
]

# scale tiles
for i in range(len(bg_tiles)):
    bg_tiles[i] = pygame.transform.scale(bg_tiles[i], (WIDTH, HEIGHT))

# ----------------- Platforms -----------------
# Definizione delle piattaforme statiche per ogni livello
def create_static_platforms():
    platforms = []
    platform_types = []
    platform_width = 100
    current_y = HEIGHT - 50  # Altezza iniziale
    
    # Crea le piattaforme dalla mappa definita
    for x, y_offset, level in GAME_MAP:
        # Calcola la posizione y sottraendo l'offset dall'altezza corrente
        current_y -= y_offset
        
        # Crea la piattaforma
        platform = pygame.Rect(x, current_y, platform_width, 16)
        platforms.append(platform)
        platform_types.append(level)
        
        log_debug(f"Creata piattaforma a x={x}, y={current_y}, livello={level_names[level]}")
    
    return platforms, platform_types

# Inizializza le piattaforme statiche
platforms, platform_types = create_static_platforms()

# ----------------- WobblyBall -----------------
class WobblyBall:
    def __init__(self, x, y, radius=32, color=(255,165,0)):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = radius
        self.base_radius = radius
        self.color = color
        self.trail = []
        self.MAX_TRAIL = 36
        self.particles = []

    def apply_input(self, keys):
        accel = 1.2
        max_speed = 8
        friction = 0.85
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = max(-max_speed, self.vx - accel)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = min(max_speed, self.vx + accel)
        else:
            self.vx *= friction  # scivolamento graduale

    def update_physics(self, dt, gravity=0.8):
        # Limita la velocità massima di caduta
        max_fall_speed = 15
        self.vy = min(self.vy + gravity, max_fall_speed)
        
        # Aggiorna posizione
        self.x += self.vx
        self.y += self.vy

        # Rimbalzo dalle pareti con effetto elastico
        bounce_factor = 0.7
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * bounce_factor
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -abs(self.vx) * bounce_factor

        # trail
        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.MAX_TRAIL:
            self.trail.pop()

        # particles
        if abs(self.vx) > 0.5 or abs(self.vy) > 0.5:
            for _ in range(1):
                self.particles.append([
                    self.x + random.uniform(-4,4),
                    self.y + random.uniform(-4,4),
                    random.uniform(1.8,3.6),
                    random.randint(18,34)
                ])
        for p in self.particles:
            p[1] += 1.5
            p[2] *= 0.96
            p[3] -= 1
        self.particles = [p for p in self.particles if p[3] > 0 and p[2] > 0.5]

        # wobble
        speed_factor = math.hypot(self.vx, self.vy)
        target_radius = self.base_radius * (1.0 + min(0.5, speed_factor*0.03))
        self.radius += (target_radius - self.radius) * 0.12

    def draw_trail(self, surf, orange=(255,165,0), red=(255,0,0), black=(10,10,20)):
        if not self.trail:
            return
        L = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = i / max(1, L-1)
            if t < 0.5:
                col = lerp_color(orange, red, t * 2)
            else:
                col = lerp_color(red, black, (t - 0.5) * 2)
            alpha = int(255 * (1 - t))
            size = int(self.radius * (0.5 + 0.5 * (1 - t)))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (size, size), size)
            surf.blit(s, (tx - size, ty - size))

    def draw_particles(self, surf):
        for p in self.particles:
            alpha = max(0, int(255 * (p[3] / 34)))
            r = max(1, int(p[2]))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255,180,60,alpha), (r,r), r)
            surf.blit(s, (p[0]-r, p[1]-r))

    def draw_wobbly(self, surf, t):
        cx, cy = int(self.x), int(self.y)
        points = []
        segments = 32
        speed_factor = math.hypot(self.vx, self.vy)
        for i in range(segments):
            ang = i * (2*math.pi / segments)
            wobble = math.sin(t*6 + i*0.7) * 4.0
            r = self.radius * (1 + wobble*0.01) * (0.95 + min(0.2, speed_factor*0.02))
            x = cx + r * math.cos(ang) * (1.0 + 0.02*self.vx)
            y = cy + r * math.sin(ang) * (1.0 + -0.01*self.vy)
            points.append((x,y))
        pygame.draw.polygon(surf, self.color, points)
        pygame.draw.aalines(surf, (255,220,140), True, points, 1)

# ----------------- Utilities -----------------
def lerp_color(c1, c2, t):
    return (int(c1[0]*(1-t)+c2[0]*t),
            int(c1[1]*(1-t)+c2[1]*t),
            int(c1[2]*(1-t)+c2[2]*t))

def check_platform_collision(ball, platforms, world_offset):
    for i, plat in enumerate(platforms):
        plat_rect = plat.copy()
        plat_rect.y += world_offset
        
        # Verifica collisione orizzontale
        if ball.x + ball.radius > plat_rect.left and ball.x - ball.radius < plat_rect.right:
            # Verifica collisione verticale solo quando la palla sta scendendo (vy >= 0)
            if ball.vy >= 0:
                ball_bottom = ball.y + ball.radius
                # Aumenta il margine di collisione per rendere più facile atterrare
                margin = 10
                if ball_bottom >= plat_rect.top - margin and ball_bottom <= plat_rect.top + ball.vy + margin:
                    print(f"DEBUG - Collisione con piattaforma {i} - Tipo: {platform_types[i]}")
                    print(f"DEBUG - Posizione piattaforma: y={plat_rect.y}, player y={ball.y}")
                    return True, i
        
    return False, None



# ----------------- Reset Game -----------------

def reset_game():
    global player, world_offset, score, GAME_OVER, tiles_revealed, platforms, platform_types, current_level
    
    # Reinizializza le piattaforme statiche
    platforms, platform_types = create_static_platforms()
    
    # Posiziona il player esattamente sulla prima piattaforma
    start_platform = platforms[0]  # La prima piattaforma è quella di partenza
    player.x = start_platform.centerx
    player.y = start_platform.top - player.radius  # Posiziona il player esattamente sopra la piattaforma
    player.vx = 0
    player.vy = 0
    player.radius = player.base_radius
    player.trail.clear()
    player.particles.clear()
    
    world_offset = 0
    score = 0
    GAME_OVER = False
    tiles_revealed = 1
    current_level = LEVEL_MANTELLO
    
    log_debug(f"Gioco resettato - Player posizionato a x={player.x}, y={player.y} sulla piattaforma iniziale")

def draw_background():
    # Disegna lo sfondo in base al livello corrente
    current_height = -world_offset
    tile_height = HEIGHT  # Altezza di ogni tile
    
    # Calcola quanti tile per ogni livello dobbiamo disegnare
    mantello_tiles = max(1, int(MANTELLO_END / tile_height))
    crosta_tiles = max(1, int((CROSTA_END - MANTELLO_END) / tile_height))
    vulcano_tiles = max(1, int((VULCANO_END - CROSTA_END) / tile_height))
    
    # Disegna i tile del livello MANTELLO
    mantello_start = 0
    for i in range(mantello_tiles):
        y_pos = i * tile_height + world_offset
        if y_pos + tile_height > 0:  # Solo se il tile è visibile
            screen.blit(bg_tiles[LEVEL_MANTELLO], (0, y_pos))
    
    # Disegna i tile del livello CROSTA
    if current_height > MANTELLO_END:
        crosta_start = MANTELLO_END
        for i in range(crosta_tiles):
            y_pos = crosta_start + i * tile_height + world_offset
            if y_pos + tile_height > 0:  # Solo se il tile è visibile
                screen.blit(bg_tiles[LEVEL_CROSTA], (0, y_pos))
    
    # Disegna i tile del livello VULCANO
    if current_height > CROSTA_END:
        vulcano_start = CROSTA_END
        for i in range(vulcano_tiles):
            y_pos = vulcano_start + i * tile_height + world_offset
            if y_pos + tile_height > 0:  # Solo se il tile è visibile
                screen.blit(bg_tiles[LEVEL_VULCANO], (0, y_pos))
    
    log_debug(f"Background - Altezza: {current_height}, Livello: {level_names[current_level]}")

# ----------------- Game Loop -----------------
# Inizializza il player alla posizione di partenza
start_platform = platforms[0]  # La prima piattaforma è quella di partenza
player = WobblyBall(start_platform.centerx, start_platform.top - 32)  # 32 è il raggio predefinito
world_offset = 0
t_global = 0
score = 0
GAME_OVER = False
tiles_revealed = 1
jumps_made = 0
current_level = LEVEL_MANTELLO  # Inizializza il livello corrente

def main():
    global t_global, world_offset, score, GAME_OVER, tiles_revealed, jumps_made, current_level
    running = True
    while running:
        dt = clock.tick(60)/1000.0
        t_global += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE and not GAME_OVER:
                    grounded, idx = check_platform_collision(player, platforms, world_offset)
                    if grounded:
                        player.vy = -14  # Salto standard per tutte le piattaforme
                    else:
                        player.vy = -10  # Salto ridotto per piattaforme più alte

                elif ev.key == pygame.K_r and GAME_OVER:
                    reset_game()

        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update_physics(dt)

        # scroll e gestione livelli
        SCROLL_THRESH = HEIGHT * 0.4  # Aumentato leggermente per dare più spazio
        SCROLL_SPEED = 0.3  # Fattore di smoothing per lo scroll
        
        if player.y < SCROLL_THRESH:
            target_dy = SCROLL_THRESH - player.y
            actual_dy = target_dy * SCROLL_SPEED  # Scroll più graduale
            
            # Limita lo scroll massimo per frame
            max_scroll = 15
            actual_dy = min(max_scroll, actual_dy)
            
            world_offset += actual_dy
            player.y += actual_dy  # Aggiorna anche la posizione del giocatore
            score += int(actual_dy * 0.2)
            
            # Determina il livello corrente in base all'altezza in km
            current_level = LEVEL_MANTELLO
            current_height = -world_offset
            height_km = current_height / 1000  # Converti in km
            log_debug(f"Stato gioco - Altezza: {height_km:.2f} km, World offset: {world_offset}, Player y: {player.y}, Velocità y: {player.vy}")
            
            # Cambio livello basato sull'altezza
            if current_height > MANTELLO_END:
                current_level = LEVEL_CROSTA
                if not tiles_revealed == 2:
                    log_debug(f"Passaggio alla Crosta Terrestre a altezza {current_height}")
                    tiles_revealed = 2
            if current_height > CROSTA_END:
                current_level = LEVEL_VULCANO
                if not tiles_revealed == 3:
                    log_debug(f"Passaggio al Vulcano a altezza {current_height}")
                    tiles_revealed = 3
            log_debug(f"Livello corrente: {level_names[current_level]}")
            
            # Genera piattaforme specifiche per il livello
            # Non generiamo più piattaforme dinamicamente
            # Aggiorniamo solo il livello corrente in base all'altezza
            current_height = -world_offset
            height_km = current_height / 1000
            log_debug(f"Altezza attuale: {height_km:.2f} km")
            
            # Aggiorna il background in base al livello
            if current_height > sum(level_heights):
                # Il giocatore ha raggiunto la cima del vulcano!
                GAME_OVER = True
                score += 10000  # bonus completamento

        # collision e rimbalzo
        grounded, idx = check_platform_collision(player, platforms, world_offset)
        if grounded and player.vy >= 0:  # Solo quando sta scendendo o è fermo
            plat = platforms[idx]
            player.y = plat.top + world_offset - player.radius  # Correggi la posizione considerando l'offset
            
            # Tutte le piattaforme hanno lo stesso rimbalzo
            player.vy = -14  # Rimbalzo standard per tutte le piattaforme
            log_debug(f"Rimbalzo - Pos Y: {player.y}, Velocità Y: {player.vy}, Piattaforma Y: {plat.top + world_offset}")            # Effetto sonoro e particelle (opzionale)
            player.particles.extend([
                [player.x + random.uniform(-20,20),
                 player.y + player.radius,
                 random.uniform(1,3),
                 random.randint(20,30)]
                for _ in range(5)
            ])
            

        # game over
        if player.y - player.radius > HEIGHT:
            GAME_OVER = True
            log_debug(f"GAME OVER - Pos Y: {player.y}, Velocità Y: {player.vy}, Ultima piattaforma Y: {platforms[-1].y + world_offset}")

        # ----------------- Draw -----------------
        screen.fill((0,0,0))
        draw_background()
        
        # Mostra altezza e livello corrente
        height_text = FONT.render(f"Altezza: {(-world_offset/1000):.2f} km", True, (255, 255, 255))
        level_text = FONT.render(f"Livello: {level_names[current_level]}", True, (255, 255, 255))
        screen.blit(height_text, (10, 10))
        screen.blit(level_text, (10, 40))

        for i, plat in enumerate(platforms):
            rect = plat.copy()
            rect.y += world_offset
            if platform_types[i]==0:
                color=(150,80,40)
            elif platform_types[i]==1:
                color=(100,255,255)
            else:
                color=(255,100,200)
            pygame.draw.rect(screen, color, rect)

        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, t_global)

        # Determina il livello corrente e progresso
        current_height = -world_offset
        current_level = LEVEL_MANTELLO
        level_progress = 0
        
        if current_height > level_heights[LEVEL_MANTELLO]:
            current_level = LEVEL_CROSTA
            level_progress = (current_height - level_heights[LEVEL_MANTELLO]) / level_heights[LEVEL_CROSTA]
        elif current_height > 0:
            level_progress = current_height / level_heights[LEVEL_MANTELLO]
            
        if current_height > level_heights[LEVEL_MANTELLO] + level_heights[LEVEL_CROSTA]:
            current_level = LEVEL_VULCANO
            level_progress = (current_height - (level_heights[LEVEL_MANTELLO] + level_heights[LEVEL_CROSTA])) / level_heights[LEVEL_VULCANO]
        
        # Visualizza informazioni
        total_score = score + int(current_height * 0.1)
        txt = FONT.render(f"Score: {total_score}", True, (255,255,255))
        screen.blit(txt, (10,10))
        
        # Mostra livello corrente e progresso
        level_txt = FONT.render(f"Livello: {level_names[current_level]}", True, level_colors[current_level])
        screen.blit(level_txt, (10,40))
        
        # Barra di progresso del livello
        progress = int(level_progress * 100)
        progress_txt = FONT.render(f"Progresso: {progress}%", True, (255,220,100))
        screen.blit(progress_txt, (10,70))
        
        if GAME_OVER:
            if current_height > sum(level_heights):
                # Vittoria!
                victory_txt = FONT.render("VITTORIA! - Eruzione Completata!", True, (255,215,0))
                screen.blit(victory_txt, (WIDTH//2-180, HEIGHT//2))
                bonus_txt = FONT.render("Bonus Completamento: +10000", True, (255,215,0))
                screen.blit(bonus_txt, (WIDTH//2-140, HEIGHT//2+30))
            else:
                # Game Over normale
                txt = FONT.render("GAME OVER - Press R to restart", True, (255,0,0))
                screen.blit(txt, (WIDTH//2-140, HEIGHT//2))
            
            final_score = FONT.render(f"Punteggio Finale: {total_score}", True, (255,200,0))
            screen.blit(final_score, (WIDTH//2-100, HEIGHT//2+60))

        pygame.display.flip()

main()
pygame.quit()
sys.exit()
