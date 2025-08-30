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
    screen.blit(effects_surface, (0, 0))

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

# Definizione delle altezze dei livelli in km
KM_PER_LEVEL = {
    LEVEL_MANTELLO: 15,    # 0-15 km: Mantello
    LEVEL_CROSTA: 30,      # 15-30 km: Crosta
    LEVEL_VULCANO: 40      # 30-40 km: Vulcano
}

level_names = ["Mantello", "Crosta Terrestre", "Vulcano"]

# Costanti per la generazione delle piattaforme
PLATFORM_VERTICAL_SPACING = 80  # Distanza verticale tra le piattaforme
GAME_MAP = []  # lasciamo vuoto: usiamo generation dinamica

PIXEL_PER_KM = 50  # come prima

# Altezze dei livelli in pixel
MANTELLO_HEIGHT_PX = 15 * PIXEL_PER_KM
CROSTA_HEIGHT_PX = 30 * PIXEL_PER_KM
VULCANO_HEIGHT_PX = 40 * PIXEL_PER_KM



level_heights = [MANTELLO_HEIGHT_PX, (CROSTA_HEIGHT_PX - MANTELLO_HEIGHT_PX), (VULCANO_HEIGHT_PX - CROSTA_HEIGHT_PX)]

level_colors = [
    (255, 100, 0),    # Mantello
    (139, 69, 19),    # Crosta
    (169, 169, 169)   # Vulcano
]

# ----------------- Volcano Top + Sky -----------------
CRATER_Y = 100  # altezza del cratere
eruption = False
particles = []


def draw_scene():
    # Cielo
    screen.fill((135, 206, 235))  # azzurro
    pygame.draw.circle(screen, (255, 223, 0), (WIDTH-80, 80), 40)  # Sole
    
    # Nuvole (esempio statiche)
    pygame.draw.ellipse(screen, (255, 255, 255), (100, 50, 120, 60))
    pygame.draw.ellipse(screen, (255, 255, 255), (300, 70, 150, 80))
    
    # Pareti vulcano (triangolo grigio scuro)
    pygame.draw.polygon(screen, (90, 60, 30), [(0, HEIGHT), (WIDTH//2, CRATER_Y), (WIDTH, HEIGHT)])
    
    # Cratere
    pygame.draw.ellipse(screen, (50, 30, 20), (WIDTH//2-100, CRATER_Y-20, 200, 40))

def trigger_eruption():
    global eruption
    eruption = True
    for i in range(80):  # particelle di lava
        x = WIDTH//2 + random.randint(-40, 40)
        y = CRATER_Y
        particles.append([x, y, random.uniform(-3,3), random.uniform(-9,-5), random.randint(30,50)])

def update_particles():
    for p in particles[:]:
        p[0] += p[2]   # vx
        p[1] += p[3]   # vy
        p[3] += 0.25   # gravità
        p[4] -= 1      # vita
        color = random.choice([(255, 50, 0), (255, 120, 0), (200, 200, 200)])
        pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), 5)
        if p[4] <= 0:
            particles.remove(p)

# ----------------- Volcano Section -----------------
def draw_volcano_section(surface, scroll_y):
    width, height = surface.get_size()
    center_x = width // 2
    
    # Disegno cielo in cima
    pygame.draw.rect(surface, (135, 206, 235), (0, 0, width, 200))  # cielo azzurro
    pygame.draw.circle(surface, (255, 255, 0), (width - 100, 100), 50)  # sole
    
    # Nuvole
    for i in range(3):
        pygame.draw.ellipse(surface, (255, 255, 255), (100 + i*150, 80, 120, 60))
    
    # Sezione del vulcano (poligono a cono)
    top_y = 200 - scroll_y
    base_y = height
    cone_width_top = 150
    cone_width_base = 500
    
    pygame.draw.polygon(surface, (80, 50, 20), [
        (center_x - cone_width_base//2, base_y),
        (center_x + cone_width_base//2, base_y),
        (center_x + cone_width_top//2, top_y),
        (center_x - cone_width_top//2, top_y)
    ])

    # Cratere (buca nera in cima)
    pygame.draw.ellipse(surface, (30, 30, 30), (center_x-60, top_y-20, 120, 40))

# ----------------- Lava Flow -----------------
lava_particles = []

# ----------------- Funzioni Eruzione -----------------
def spawn_lava(lava_list, x, y):
    """Genera una nuova colata di lava."""
    lava_list.append({"x": x, "y": y, "color": (255, 140, 0), "life": 255})

def update_lava(screen, lava_list):
    """Aggiorna e disegna le colate di lava con gradiente di colore."""
    for lava in lava_list:
        lava["y"] += 2
        lava["life"] -= 3
        if lava["life"] > 170:
            lava["color"] = (255, 140, 0)  # arancione
        elif lava["life"] > 80:
            lava["color"] = (200, 0, 0)    # rosso
        else:
            lava["color"] = (50, 50, 50)   # nero/ossidiana
        pygame.draw.circle(screen, lava["color"], (lava["x"], lava["y"]), 5)


# ----------------- Smoke -----------------
smoke_particles = []

def spawn_smoke(center_x, crater_y):
    if random.random() < 0.2:
        smoke_particles.append({
            "x": center_x + random.randint(-15, 15),
            "y": crater_y - 40,
            "vy": random.uniform(-1.5, -0.5),
            "alpha": 255
        })

def update_smoke(surface):
    global smoke_particles
    new_particles = []
    for s in smoke_particles:
        s["y"] += s["vy"]
        s["alpha"] -= 2
        if s["alpha"] > 0:
            surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(surf, (100, 100, 100, s["alpha"]), (15, 15), 15)
            surface.blit(surf, (s["x"], s["y"]))
            new_particles.append(s)
    smoke_particles = new_particles


# ----------------- Funzioni di Background -----------------
def draw_scrolling_background(screen, bg_tiles, scroll_y):
    """Simula un nastro trasportatore verticale per i livelli di background."""
    h = bg_tiles[0].get_height()
    for i in range(len(bg_tiles)):
        y = (i * h + scroll_y) % (h * len(bg_tiles))
        screen.blit(bg_tiles[i], (0, y - h))

# Sezione vulcano in sezione
def draw_volcano_section(screen, height, progress):
    """Disegna il vulcano in sezione con pareti che si restringono man mano."""
    base_width = 500
    crater_width = 100
    slope = (base_width - crater_width) / height

    for y in range(height):
        half_width = base_width/2 - slope * (y + progress)
        pygame.draw.line(screen, (80, 40, 20),
                         (300 - half_width, 800 - y),
                         (300 + half_width, 800 - y))



# ----------------- Load Background Tiles -----------------
bg_tiles = [
    pygame.image.load("./RoundedBlocks/lava.png").convert(),
    pygame.image.load("./RoundedBlocks/stone.png").convert(),
    pygame.image.load("./RoundedBlocks/ground.png").convert_alpha()
]

for i in range(len(bg_tiles)):
    bg_tiles[i] = pygame.transform.scale(bg_tiles[i], (WIDTH, HEIGHT))

# ----------------- Platforms -----------------
def create_static_platforms():
    platforms = []
    platform_types = []
    platform_width = 100

    def add_platform(x, y, level):
        platform = pygame.Rect(x, y, platform_width, 16)
        platforms.append(platform)
        platform_types.append(level)
        log_debug(f"Creata piattaforma a x={x}, y={y}, livello={level_names[level]}")

    # Piattaforma iniziale
    start_y = HEIGHT - 50
    add_platform(WIDTH//2 - 50, start_y, LEVEL_MANTELLO)
    current_y = start_y

    # Calcola numero di piattaforme su tutta l'altezza di gioco
    total_height_px = VULCANO_HEIGHT_PX
    platforms_needed = int(total_height_px / PLATFORM_VERTICAL_SPACING) + 40

    for i in range(platforms_needed):
        current_y -= PLATFORM_VERTICAL_SPACING
        x = random.choice([
            random.randint(50, WIDTH//3),
            random.randint(WIDTH//3, 2*WIDTH//3),
            random.randint(2*WIDTH//3, WIDTH-150)
        ])

        # livello in base all'altezza (usa height dal fondo del mondo)
        height_km = abs(start_y - current_y) / PIXEL_PER_KM
        if height_km <= KM_PER_LEVEL[LEVEL_MANTELLO]:
            level = LEVEL_MANTELLO
        elif height_km <= KM_PER_LEVEL[LEVEL_CROSTA]:
            level = LEVEL_CROSTA
        else:
            level = LEVEL_VULCANO

        add_platform(x, current_y, level)

    log_debug(f"Generate {len(platforms)} piattaforme in totale")
    return platforms, platform_types

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
            self.vx *= friction

    def update_physics(self, dt, gravity=0.8):
        max_fall_speed = 15
        self.vy = min(self.vy + gravity, max_fall_speed)
        self.x += self.vx
        self.y += self.vy

        bounce_factor = 0.7
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * bounce_factor
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -abs(self.vx) * bounce_factor

        self.trail.insert(0, (self.x, self.y))
        if len(self.trail) > self.MAX_TRAIL:
            self.trail.pop()

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
    """
    Collision robusta: confronta la posizione corrente del fondo della palla
    con la top della piattaforma usando anche la posizione precedente della palla
    (approssimata) per evitare di saltare la collisione quando lo scroll è forte.
    """
    for i, plat in enumerate(platforms):
        plat_rect = plat.copy()
        plat_rect.y += world_offset  # coordinate sullo schermo

        # collisione orizzontale semplice
        if ball.x + ball.radius > plat_rect.left and ball.x - ball.radius < plat_rect.right:
            # consideriamo solo caduta (atterraggio dall'alto)
            if ball.vy >= 0:
                ball_bottom = ball.y + ball.radius
                # approssimazione posizione precedente
                prev_y = ball.y - ball.vy
                prev_bottom = prev_y + ball.radius

                margin = 8
                # se il bottom era sopra (o vicino) alla top e ora è pari/sotto la top -> atterraggio
                if prev_bottom <= plat_rect.top + margin and ball_bottom >= plat_rect.top - margin:
                    log_debug(f"Collisione con piattaforma {i} - Tipo: {platform_types[i]} - plat_top(screen)={plat_rect.top:.1f} ball_bottom={ball_bottom:.1f} prev_bottom={prev_bottom:.1f}")
                    return True, i

    return False, None

# ----------------- Reset Game -----------------
def reset_game():
    global player, world_offset, score, GAME_OVER, tiles_revealed, platforms, platform_types, current_level

    platforms, platform_types = create_static_platforms()

    start_platform = platforms[0]
    player.x = start_platform.centerx
    player.y = start_platform.top - player.radius
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

# scale tiles
for i in range(len(bg_tiles)):
    bg_tiles[i] = pygame.transform.scale(bg_tiles[i], (WIDTH, HEIGHT))

class LavaParticle:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = random.uniform(2, 5)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        self.size = random.randint(4, 8)
        self.temperature = 1.0  # 1 = caldissimo, 0 = freddo
        self.lifetime = random.randint(60, 120)
        self.alpha = 255
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.1  # Gravità
        self.temperature *= 0.99  # Raffreddamento
        self.lifetime -= 1
        self.alpha = min(255, int(255 * (self.lifetime / 60)))
    
    def draw(self, surface):
        if self.temperature > 0.7:
            # Arancione brillante -> Rosso
            color = (255, int(165 * self.temperature), 0, self.alpha)
        elif self.temperature > 0.4:
            # Rosso -> Rosso scuro
            t = (self.temperature - 0.4) / 0.3
            color = (int(255 * t), 0, 0, self.alpha)
        else:
            # Rosso scuro -> Nero
            t = self.temperature / 0.4
            color = (int(100 * t), 0, 0, self.alpha)
        
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class LavaStream:
    def __init__(self, x, y, direction=1):
        self.points = [(x, y)]
        self.width = random.randint(4, 8)
        self.direction = direction  # 1 = destra, -1 = sinistra
        self.temperature = 1.0
        self.lifetime = random.randint(180, 300)
        self.particles = []
    
    def update(self):
        if len(self.points) > 0:
            x, y = self.points[-1]
            # Movimento della lava influenzato dalla gravità e dalla direzione
            new_x = x + random.uniform(-0.5, 0.5) + (self.direction * random.uniform(0.5, 1.5))
            new_y = y + random.uniform(1, 2)
            self.points.append((new_x, new_y))
            
            # Genera particelle occasionalmente
            if random.random() < 0.1:
                self.particles.append(LavaParticle(new_x, new_y))
        
        # Aggiorna particelle
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()
        
        self.temperature *= 0.995
        self.lifetime -= 1
        
        # Limita la lunghezza del flusso
        if len(self.points) > 30:
            self.points.pop(0)
    
    def draw(self, surface):
        if len(self.points) < 2:
            return
        
        # Disegna il flusso di lava
        for i in range(len(self.points) - 1):
            t = 1 - (i / len(self.points))  # Temperatura relativa
            temp = t * self.temperature
            
            if temp > 0.7:
                color = (255, int(165 * temp), 0)
            elif temp > 0.4:
                t = (temp - 0.4) / 0.3
                color = (int(255 * t), 0, 0)
            else:
                t = temp / 0.4
                color = (int(100 * t), 0, 0)
            
            start = self.points[i]
            end = self.points[i + 1]
            pygame.draw.line(surface, color, start, end, self.width)
        
        # Disegna particelle
        for particle in self.particles:
            particle.draw(surface)

class EruptionManager:
    def __init__(self):
        self.particles = []
        self.lava_streams = []
        self.last_stream_time = 0
        self.erupting = False
        
    def start_eruption(self, center_x, top_y):
        self.erupting = True
        
        # Crea esplosione iniziale di particelle
        num_particles = 30
        for i in range(num_particles):
            angle = random.uniform(-math.pi/3, math.pi/3)  # Angolo verso l'alto
            particle = LavaParticle(center_x, top_y, angle)
            self.particles.append(particle)
        
        # Inizia flussi di lava
        self.lava_streams.append(LavaStream(center_x, top_y, 1))
        self.lava_streams.append(LavaStream(center_x, top_y, -1))
    
    def update(self, center_x, top_y):
        if not self.erupting:
            return
        
        # Aggiorna particelle esistenti
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()
        
        # Aggiorna flussi di lava
        self.lava_streams = [s for s in self.lava_streams if s.lifetime > 0]
        for stream in self.lava_streams:
            stream.update()
        
        # Aggiungi nuove particelle continuamente
        if random.random() < 0.3:  # 30% di probabilità per frame
            angle = random.uniform(-math.pi/3, math.pi/3)
            self.particles.append(LavaParticle(center_x, top_y, angle))
        
        # Aggiungi nuovi flussi occasionalmente
        current_time = pygame.time.get_ticks()
        if current_time - self.last_stream_time > 2000:  # Ogni 2 secondi
            self.lava_streams.append(LavaStream(center_x, top_y, random.choice([-1, 1])))
            self.last_stream_time = current_time
    
    def draw(self, surface):
        if not self.erupting:
            return
        
        # Disegna tutti i flussi di lava
        for stream in self.lava_streams:
            stream.draw(surface)
        
        # Disegna tutte le particelle
        for particle in self.particles:
            particle.draw(surface)

# Crea il manager dell'eruzione
eruption_manager = EruptionManager()

def draw_volcano_walls(km_height):
    """Disegna le pareti del vulcano usando tile in stile platform"""
    # Calcola la progressione nel vulcano (0 = inizio, 1 = cratere)
    volcano_progress = (km_height - KM_PER_LEVEL[LEVEL_CROSTA]) / (KM_PER_LEVEL[LEVEL_VULCANO] - KM_PER_LEVEL[LEVEL_CROSTA])
    volcano_progress = max(0, min(1, volcano_progress))
    
    # Calcola la larghezza del passaggio che si restringe verso l'alto
    max_width = WIDTH * 0.8  # Larghezza massima all'inizio
    min_width = WIDTH * 0.3  # Larghezza minima al cratere
    passage_width = max_width - (max_width - min_width) * volcano_progress
    
    # Dimensione dei tile
    TILE_SIZE = 32
    num_rows = HEIGHT // TILE_SIZE
    
    # Crea una superficie per i tile del vulcano
    wall_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    crater_left = None
    crater_right = None
    crater_top = None
    
    # Per ogni riga di tile, dal basso verso l'alto
    for row in range(num_rows):
        # Calcola quanto deve restringersi questa riga
        row_progress = row / num_rows  # 0 = basso, 1 = alto
        row_width = max_width - (max_width - min_width) * row_progress * volcano_progress
        
        # Calcola quanti tile servono per ogni lato
        left_edge = (WIDTH - row_width) // 2
        right_edge = WIDTH - left_edge
        left_tiles = int(left_edge // TILE_SIZE) + 1
        right_tiles = int((WIDTH - right_edge) // TILE_SIZE) + 1
        
        y = HEIGHT - (row + 1) * TILE_SIZE
        
        # Se questa è la riga più alta, salva le informazioni del cratere
        if row == num_rows - 1:
            crater_left = left_edge
            crater_right = right_edge
            crater_top = y
        
        # Disegna i tile della parete sinistra
        for i in range(left_tiles):
            x = i * TILE_SIZE
            tile_type = get_volcano_tile_type(i, row, "left")
            # Aggiungi effetto di riscaldamento per i tile vicini al cratere
            if row > num_rows * 0.8:  # Solo nella parte alta del vulcano
                heat_factor = (row / num_rows) * 0.3  # Più caldo verso l'alto
                draw_volcano_tile(wall_surface, tile_type, x, y, heat_factor)
            else:
                draw_volcano_tile(wall_surface, tile_type, x, y)
        
        # Disegna i tile della parete destra
        for i in range(right_tiles):
            x = right_edge + i * TILE_SIZE
            tile_type = get_volcano_tile_type(i, row, "right")
            # Aggiungi effetto di riscaldamento per i tile vicini al cratere
            if row > num_rows * 0.8:  # Solo nella parte alta del vulcano
                heat_factor = (row / num_rows) * 0.3  # Più caldo verso l'alto
                draw_volcano_tile(wall_surface, tile_type, x, y, heat_factor)
            else:
                draw_volcano_tile(wall_surface, tile_type, x, y)
    
    return wall_surface, (crater_left, crater_right, crater_top)

def get_volcano_tile_type(x_index, y_index, side):
    """Determina il tipo di tile da usare in base alla posizione"""
    if x_index == 0:  # Bordo interno
        return "edge"
    elif y_index == 0:  # Base
        return "bottom"
    else:  # Tile normale della parete
        return "wall"

def draw_volcano_tile(surface, tile_type, x, y, heat_factor=0):
    """Disegna un singolo tile della parete del vulcano con effetti di calore"""
    tile_size = 32
    
    # Colori base per i diversi tipi di tile
    base_colors = {
        "edge": (139, 69, 19),    # Marrone per il bordo
        "bottom": (160, 80, 20),   # Marrone più chiaro per la base
        "wall": (120, 60, 15)      # Marrone scuro per le pareti
    }
    
    # Applica l'effetto di calore al colore base
    base_color = base_colors[tile_type]
    if heat_factor > 0:
        # Aumenta il rosso e diminuisci il blu/verde per dare l'effetto di calore
        r = min(255, base_color[0] + int(heat_factor * 100))
        g = max(0, base_color[1] - int(heat_factor * 30))
        b = max(0, base_color[2] - int(heat_factor * 50))
        color = (r, g, b)
    else:
        color = base_color
    
    # Disegna il tile base
    pygame.draw.rect(surface, color, (x, y, tile_size, tile_size))
    
    # Aggiungi dettagli al tile
    if tile_type == "edge":
        # Bordo più scuro per il lato interno
        dark_color = tuple(max(0, c - 30) for c in color)
        pygame.draw.line(surface, dark_color, (x + tile_size - 1, y), 
                        (x + tile_size - 1, y + tile_size), 2)
        
        # Se c'è effetto di calore, aggiungi un bagliore
        if heat_factor > 0:
            glow_color = (255, int(200 * heat_factor), 0, int(100 * heat_factor))
            glow_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, glow_color, (0, 0, tile_size, tile_size))
            surface.blit(glow_surface, (x, y))
            
    elif tile_type == "wall":
        # Piccole crepe o texture per le pareti
        if heat_factor > 0:
            # Aggiungi dettagli di lava nelle crepe
            crack_color = (255, int(100 * heat_factor), 0)
            for _ in range(2):
                cx = x + random.randint(5, tile_size-5)
                cy = y + random.randint(5, tile_size-5)
                pygame.draw.circle(surface, crack_color, (cx, cy), 2)
        for _ in range(2):
            crack_x = x + random.randint(4, tile_size-4)
            crack_y = y + random.randint(4, tile_size-4)
            crack_size = random.randint(2, 6)
            pygame.draw.circle(surface, (90, 45, 10), (crack_x, crack_y), crack_size)
    
    # Aggiungi ombreggiatura 3D
    light_color = tuple(min(255, int(c * 1.2)) for c in color)
    dark_color = tuple(max(0, int(c * 0.8)) for c in color)
    
    pygame.draw.line(surface, light_color, (x, y), (x + tile_size, y))
    pygame.draw.line(surface, dark_color, (x, y + tile_size - 1), (x + tile_size, y + tile_size - 1))

def draw_background(world_offset):
    # Calcola l'altezza in km e la posizione di scroll
    km_height = world_offset / PIXEL_PER_KM
    scroll_y = int(world_offset % HEIGHT)
    
    def draw_scrolling_tile(tile, offset_y):
        # Disegna il tile con scorrimento continuo
        y_pos = (offset_y + scroll_y) % HEIGHT
        screen.blit(tile, (0, y_pos))
        screen.blit(tile, (0, y_pos - HEIGHT))
        if y_pos > 0:
            screen.blit(tile, (0, y_pos + HEIGHT))
    
    # Determina il livello corrente e gestisce le transizioni
    current_level = LEVEL_MANTELLO
    if km_height >= KM_PER_LEVEL[LEVEL_CROSTA]:
        current_level = LEVEL_VULCANO
        # Nel livello vulcano, disegna le pareti e gli effetti
        screen.fill((0, 0, 0))  # Sfondo nero
        volcano_walls, crater_info = draw_volcano_walls(km_height)
        screen.blit(volcano_walls, (0, 0))
        
        # Aggiungi effetti di eruzione se siamo vicini al cratere
        if km_height > KM_PER_LEVEL[LEVEL_VULCANO] * 0.9:
            draw_eruption_effects(crater_info, km_height)
            
    elif km_height >= KM_PER_LEVEL[LEVEL_MANTELLO]:
        current_level = LEVEL_CROSTA
    
    # Gestione dello scorrimento e delle transizioni tra livelli per mantello e crosta
    if current_level == LEVEL_MANTELLO:
        if km_height < KM_PER_LEVEL[LEVEL_MANTELLO] - 1:
            # Solo mantello
            draw_scrolling_tile(bg_tiles[LEVEL_MANTELLO], 0)
        elif km_height < KM_PER_LEVEL[LEVEL_MANTELLO] + 1:
            # Transizione mantello-crosta
            progress = (km_height - (KM_PER_LEVEL[LEVEL_MANTELLO] - 1)) / 2
            progress = max(0, min(1, progress))
            transition_y = int(-HEIGHT + (HEIGHT * progress))
            
            # Disegna entrambi i livelli con la transizione
            draw_scrolling_tile(bg_tiles[LEVEL_MANTELLO], 0)
            draw_scrolling_tile(bg_tiles[LEVEL_CROSTA], transition_y)
        else:
            # Dopo la transizione, mostra solo la crosta
            draw_scrolling_tile(bg_tiles[LEVEL_CROSTA], 0)
    elif km_height < KM_PER_LEVEL[LEVEL_CROSTA] - 1:
        # Solo crosta
        draw_scrolling_tile(bg_tiles[LEVEL_CROSTA], 0)
    elif km_height >= KM_PER_LEVEL[LEVEL_CROSTA]:
        # Sezione del vulcano con pareti
        draw_scrolling_tile(bg_tiles[LEVEL_VULCANO], 0)
        
        # Disegna le pareti del vulcano e ottieni il contorno del cratere
        wall_surface, crater_info = draw_volcano_walls(km_height)
        screen.blit(wall_surface, (0, 0))
        
        # Gestisci l'eruzione quando si è vicini alla cima
        volcano_progress = (km_height - KM_PER_LEVEL[LEVEL_CROSTA]) / (KM_PER_LEVEL[LEVEL_VULCANO] - KM_PER_LEVEL[LEVEL_CROSTA])
        
        if volcano_progress > 0.9:  # Inizia l'eruzione vicino alla cima
            left_edge, right_edge, crater_top = crater_info
            
            # Effetto di riscaldamento dei tile del cratere
            for x in range(int(left_edge), int(right_edge), 4):
                heat = random.random()  # Valore casuale per l'effetto di bagliore
                if heat > 0.7:
                    glow_size = random.randint(4, 8)
                    glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                    # Disegna un bagliore arancione/rosso
                    pygame.draw.circle(glow_surface, (255, 165, 0, 100), (glow_size, glow_size), glow_size)
                    pygame.draw.circle(glow_surface, (255, 69, 0, 50), (glow_size, glow_size), glow_size//2)
                    screen.blit(glow_surface, (x - glow_size, crater_top - glow_size))
            
            # Crea particelle di lava che seguono il contorno del cratere
            num_particles = random.randint(2, 5)
            for _ in range(num_particles):
                x = random.uniform(left_edge, right_edge)
                y = crater_top
                size = random.randint(3, 6)
                speed = random.uniform(2, 4)
                angle = random.uniform(-math.pi/4, math.pi/4)  # Direzione verso l'alto
                
                # Disegna la particella con effetto bagliore
                particle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (255, 165, 0, 200), (size, size), size)
                pygame.draw.circle(particle_surface, (255, 255, 200, 150), (size, size), size//2)
                screen.blit(particle_surface, (x - size, y - size))
                
                # Disegna la scia della particella
                for i in range(3):
                    trail_y = y + i * 4
                    trail_size = size * (1 - i/3)
                    trail_surface = pygame.Surface((int(trail_size*2), int(trail_size*2)), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surface, (255, 69, 0, 100-i*30), 
                                    (int(trail_size), int(trail_size)), int(trail_size))
                    screen.blit(trail_surface, (x - trail_size, trail_y - trail_size))
            
            # Effetto colata di lava lungo le pareti
            lava_points = []
            for x in range(int(left_edge), int(right_edge), 8):
                if random.random() > 0.7:
                    y_offset = random.uniform(0, 50)
                    for y in range(int(crater_top), min(int(crater_top + 150), HEIGHT), 4):
                        lava_size = random.randint(2, 4)
                        lava_alpha = max(0, 255 - (y - crater_top))
                        x_offset = math.sin((y + y_offset) / 20) * 8  # Movimento ondulatorio
                        lava_color = (255, int(69 + (y - crater_top)/2), 0, lava_alpha)
                        
                        lava_surface = pygame.Surface((lava_size*2, lava_size*2), pygame.SRCALPHA)
                        pygame.draw.circle(lava_surface, lava_color, (lava_size, lava_size), lava_size)
                        screen.blit(lava_surface, (x + x_offset - lava_size, y - lava_size))
    
    # Debug info
    log_debug(f"Background - Altezza: {km_height:.1f}km, Livello: {level_names[current_level]}")

# ----------------- Game Loop -----------------
start_platform = platforms[0]
player = WobblyBall(start_platform.centerx, start_platform.top - 32)
world_offset = 0.0
t_global = 0.0
score = 0
GAME_OVER = False
tiles_revealed = 1
jumps_made = 0
current_level = LEVEL_MANTELLO

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
                        player.vy = -14
                    else:
                        player.vy = -10
                elif ev.key == pygame.K_r and GAME_OVER:
                    reset_game()

        keys = pygame.key.get_pressed()
        player.apply_input(keys)
        player.update_physics(dt)

        # SCROLL
        SCROLL_THRESH = HEIGHT * 0.4
        SCROLL_SPEED = 0.3

        if player.y < SCROLL_THRESH:
            target_dy = SCROLL_THRESH - player.y
            actual_dy = target_dy * SCROLL_SPEED
            max_scroll = 15
            actual_dy = min(max_scroll, actual_dy)

            # world_offset aumenta mentre saliamo (coerente)
            world_offset += actual_dy
            player.y += actual_dy
            score += int(actual_dy * 0.2)

            km_height = world_offset / PIXEL_PER_KM
            log_debug(f"Scroll - km: {km_height:.2f}, world_offset: {world_offset:.1f}, player.y: {player.y:.1f}, player.vy: {player.vy:.2f}")

            # aggiorna tiles_revealed / livello
            if km_height >= KM_PER_LEVEL[LEVEL_CROSTA]:
                current_level = LEVEL_VULCANO
                if tiles_revealed < 3:
                    tiles_revealed = 3
                    log_debug(f"Passaggio al Vulcano a {km_height:.1f}km")
            elif km_height >= KM_PER_LEVEL[LEVEL_MANTELLO]:
                current_level = LEVEL_CROSTA
                if tiles_revealed < 2:
                    tiles_revealed = 2
                    log_debug(f"Passaggio alla Crosta a {km_height:.1f}km")
            else:
                current_level = LEVEL_MANTELLO

            if km_height >= KM_PER_LEVEL[LEVEL_VULCANO]:
                GAME_OVER = True
                score += 10000

        # collision e rimbalzo
        grounded, idx = check_platform_collision(player, platforms, world_offset)
        if grounded and player.vy >= 0:
            plat = platforms[idx]
            # plat.top + world_offset è y sullo schermo
            player.y = plat.top + world_offset - player.radius
            player.vy = -14
            log_debug(f"Rimbalzo - Pos Y schermo: {player.y:.1f}, Vel Y: {player.vy:.1f}, Piattaforma idx: {idx}")
            player.particles.extend([
                [player.x + random.uniform(-20,20),
                 player.y + player.radius,
                 random.uniform(1,3),
                 random.randint(20,30)]
                for _ in range(5)
            ])

        # game over se cade sotto lo schermo
        if player.y - player.radius > HEIGHT + 200:
            GAME_OVER = True
            log_debug(f"GAME OVER - Pos Y: {player.y:.1f}, Vel Y: {player.vy:.1f}")

        # ----------------- Draw -----------------
        screen.fill((0,0,0))
        draw_background(world_offset)

        # Mostra altezza in km coerente
        height_km = world_offset / PIXEL_PER_KM
        height_text = FONT.render(f"Altezza: {height_km:.2f} km", True, (255, 255, 255))
        level_text = FONT.render(f"Livello: {level_names[current_level]}", True, (255, 255, 255))
        screen.blit(height_text, (10, 10))
        screen.blit(level_text, (10, 40))

        for i, plat in enumerate(platforms):
            rect = plat.copy()
            rect.y += world_offset
            plat_y = rect.y
            plat_height_km = (plat.y + world_offset) / PIXEL_PER_KM
            if plat_height_km >= KM_PER_LEVEL[LEVEL_CROSTA]:
                color = (169, 169, 169)
            elif plat_height_km >= KM_PER_LEVEL[LEVEL_MANTELLO]:
                color = (139, 69, 19)
            else:
                color = (255, 100, 0)
            pygame.draw.rect(screen, color, rect)

        player.draw_trail(screen)
        player.draw_particles(screen)
        player.draw_wobbly(screen, t_global)

        # progresso nel livello (usiamo world_offset in pixel)
        current_height_px = world_offset
        # calcola progress percentuale nel livello corrente
        level_start_px = 0
        if current_height_px <= level_heights[0]:
            lvl = LEVEL_MANTELLO
            prog = current_height_px / level_heights[0]
        elif current_height_px <= level_heights[0] + level_heights[1]:
            lvl = LEVEL_CROSTA
            prog = (current_height_px - level_heights[0]) / level_heights[1]
        else:
            lvl = LEVEL_VULCANO
            prog = (current_height_px - (level_heights[0] + level_heights[1])) / level_heights[2]

        total_score = score + int((world_offset/PIXEL_PER_KM) * 10)  # esempio: 10 punti per km
        txt = FONT.render(f"Score: {total_score}", True, (255,255,255))
        screen.blit(txt, (10,100))

        level_txt = FONT.render(f"Livello: {level_names[lvl]}", True, level_colors[lvl])
        screen.blit(level_txt, (10,40))
        progress = int(max(0, min(1, prog)) * 100)
        progress_txt = FONT.render(f"Progresso: {progress}%", True, (255,220,100))
        screen.blit(progress_txt, (10,70))

        if GAME_OVER:
            if (world_offset / PIXEL_PER_KM) > KM_PER_LEVEL[LEVEL_VULCANO]:
                # Continua a mostrare il vulcano e gli effetti durante la vittoria
                draw_background(world_offset)
                if not eruption:
                    trigger_eruption()
                # Aggiorna gli effetti di particelle
                update_particles()
                
                # Aggiungi un overlay semi-trasparente per rendere il testo più leggibile
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(128)
                screen.blit(overlay, (0, 0))
                
                # Disegna il testo di vittoria con un effetto glow
                def draw_glowing_text(text, pos_y):
                    # Disegna il glow
                    glow_txt = FONT.render(text, True, (128, 107, 0))
                    for offset in [(2,2), (-2,2), (2,-2), (-2,-2)]:
                        screen.blit(glow_txt, (WIDTH//2-180 + offset[0], pos_y + offset[1]))
                    # Disegna il testo principale
                    main_txt = FONT.render(text, True, (255, 215, 0))
                    screen.blit(main_txt, (WIDTH//2-180, pos_y))
                
                draw_glowing_text("VITTORIA! - Eruzione Completata!", HEIGHT//2)
                draw_glowing_text("Bonus Completamento: +10000", HEIGHT//2+30)
            else:
                # Game over normale
                txtg = FONT.render("GAME OVER - Press R to restart", True, (255,0,0))
                screen.blit(txtg, (WIDTH//2-140, HEIGHT//2))
            final_score = FONT.render(f"Punteggio Finale: {total_score}", True, (255,200,0))
            screen.blit(final_score, (WIDTH//2-100, HEIGHT//2+60))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
