import pygame, random, math, sys, json, os
import logging
from datetime import datetime

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    print("Audio not available, running without sound")
    pygame.mixer = None

# Configurazione del logging solo per eventi importanti
log_filename = f"volcano_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

def log_game_event(message):
    """Logga solo eventi di gioco importanti"""
    print(f"🌋 {message}")
    logging.info(message)

def debug_input_event(ev, prefix="KEYDOWN"):
    if not ENABLE_INPUT_DEBUG:
        return
    try:
        key_name = pygame.key.name(ev.key)
    except Exception:
        key_name = str(getattr(ev, 'key', '?'))
    logging.info(f"[INPUT] {prefix} key={key_name} code={getattr(ev,'key','?')} state={_state_to_name(game_state)}")

# ----------------- Audio System -----------------
class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.audio_available = pygame.mixer is not None
        if self.audio_available:
            try:
                # Crea suoni procedurali se non ci sono file audio
                self.create_procedural_sounds()
            except Exception as e:
                print(f"Audio non disponibile: {e}")
                self.audio_available = False

    def create_procedural_sounds(self):
        # Crea suoni procedurali usando onde sinusoidali
        self.sounds['jump'] = self.create_tone(300, 0.1)
        self.sounds['powerup'] = self.create_tone(500, 0.3)
        self.sounds['collect'] = self.create_tone(800, 0.2)
        self.sounds['lava_hit'] = self.create_tone(150, 0.5)
        self.sounds['eruption'] = self.create_tone(100, 1.0)

    def create_tone(self, frequency, duration):
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = []
        for i in range(frames):
            wave = 4096 * math.sin(2 * math.pi * frequency * i / sample_rate)
            arr.append([int(wave), int(wave)])
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        return sound

    def play(self, sound_name):
        if self.audio_available and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Errore riproduzione suono '{sound_name}': {e}")

audio = AudioManager()

# ----------------- Save System -----------------
SAVE_FILE = "volcano_scores.json"

def load_scores():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Errore caricamento punteggi: {e}")
    return []

def save_score(name, score, height_km):
    scores = load_scores()
    scores.append({
        'name': name,
        'score': score,
        'height': height_km,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    scores.sort(key=lambda x: x['score'], reverse=True)
    scores = scores[:10]  # Mantieni solo top 10

    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except Exception as e:
        print(f"Errore salvataggio punteggi: {e}")
    return scores

# ----------------- Game States -----------------
MENU = 0
PLAYING = 1
GAME_OVER = 2
LEADERBOARD = 3
ENTER_NAME = 4

game_state = MENU
player_name = ""
high_scores = load_scores()

# Debug input: abilita/disabilita log dei tasti premuti
ENABLE_INPUT_DEBUG = True

def _state_to_name(value):
    return {0: "MENU", 1: "PLAYING", 2: "GAME_OVER", 3: "LEADERBOARD", 4: "ENTER_NAME"}.get(value, str(value))

def draw_eruption_effects(crater_info, km_height):
    """Disegna gli effetti di eruzione usando le informazioni del cratere"""
    crater_left, crater_right, crater_top = crater_info
    crater_width = crater_right - crater_left
    crater_center = (crater_left + crater_right) // 2

    # Calcola l'intensità dell'eruzione in base alla vicinanza al cratere
    max_height = KM_PER_LEVEL[LEVEL_VULCANO]
    eruption_intensity = min(1.0, (km_height - max_height * 0.9) / (max_height * 0.1))
    
    # Usa il tempo per animare gli effetti
    current_time = pygame.time.get_ticks()
    wave = math.sin(current_time * 0.003) * 0.3 + 0.7  # Varia tra 0.4 e 1.0

    # Crea una superficie per gli effetti con alpha blending
    effects_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Disegna la colonna principale di lava che sale
    column_height = int(200 * eruption_intensity * wave)
    column_points = []
    base_width = crater_width * 0.7
    
    for y in range(column_height, 0, -10):
        progress = y / column_height
        width = base_width * (1 - progress * 0.7)  # Si restringe verso l'alto
        wobble = math.sin(current_time * 0.005 + y * 0.1) * (20 * progress)
        left = crater_center - width/2 + wobble
        right = crater_center + width/2 + wobble
        column_points.append((left, crater_top - y))
        column_points.append((right, crater_top - y))
    
    # Disegna la colonna di lava con gradiente
    if len(column_points) >= 4:
        for i in range(0, len(column_points) - 2, 2):
            points = [column_points[i], column_points[i+1],
                     column_points[i+3], column_points[i+2]]
            progress = 1 - (i / len(column_points))
            alpha = int(200 * progress * eruption_intensity)
            color = (255, int(150 * progress + 50), 0, alpha)
            pygame.draw.polygon(effects_surface, color, points)

    # Disegna particelle di lava esplosive
    num_particles = int(40 * eruption_intensity * wave)
    for _ in range(num_particles):
        angle = random.uniform(0, math.pi)  # Particelle verso l'alto
        speed = random.uniform(5, 15) * eruption_intensity
        distance = random.uniform(0, 150) * wave
        x = crater_center + math.cos(angle) * distance
        y = crater_top - math.sin(angle) * distance - random.uniform(0, 50)
        size = random.randint(3, 8)
        alpha = int(random.uniform(150, 255) * (1 - distance/200))
        color = (255, random.randint(150, 200), 0, alpha)
        
        # Disegna la particella con bagliore
        glow_size = size * 2
        glow_alpha = alpha // 2
        glow_color = (255, 100, 0, glow_alpha)
        pygame.draw.circle(effects_surface, glow_color, (int(x), int(y)), glow_size)
        pygame.draw.circle(effects_surface, color, (int(x), int(y)), size)

    # Disegna un intenso bagliore attorno al cratere
    crater_glow = pygame.Surface((crater_width + 100, 150), pygame.SRCALPHA)
    for i in range(3):  # Strati multipli di bagliore
        glow_alpha = int(100 * eruption_intensity * wave * (3-i)/3)
        glow_color = (255, 50, 0, glow_alpha)
        glow_rect = pygame.Rect(50-i*20, 50-i*20, crater_width+i*40, 100+i*40)
        pygame.draw.ellipse(crater_glow, glow_color, glow_rect)
    effects_surface.blit(crater_glow, (crater_left-50, crater_top-50))

    # Aggiungi colate di lava lungo le pareti
    num_flows = int(8 * eruption_intensity)
    for i in range(num_flows):
        # Distribuisci i punti di partenza uniformemente
        angle = (i / num_flows) * math.pi
        start_x = crater_center + math.cos(angle) * crater_width/2
        start_y = crater_top
        
        # Crea un percorso di lava che scende
        points = [(start_x, start_y)]
        current_x = start_x
        current_y = start_y
        
        # Usa una curva più naturale per il flusso
        for step in range(random.randint(8, 20)):
            progress = step / 20
            current_x += math.sin(current_time * 0.001 + progress * 10) * 8
            current_y += 15 - progress * 5  # Rallenta verso il basso
            current_x = max(crater_left - 50, min(crater_right + 50, current_x))
            points.append((current_x, current_y))
        
        # Disegna il flusso di lava con effetto pulsante
        if len(points) > 1:
            pulse = (math.sin(current_time * 0.004 + i) * 0.3 + 0.7)
            for thickness in range(6, 0, -2):
                progress = thickness / 6
                alpha = int(200 * progress * eruption_intensity * pulse)
                color = (255, int(100 * progress + 50), 0, alpha)
                pygame.draw.lines(effects_surface, color, False, points, thickness)

    # Applica gli effetti allo schermo
    screen.blit(effects_surface, (0, 0))

    # Applica gli effetti allo schermo
    screen.blit(effects_surface, (0, 0))

# ----------------- Window -----------------
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Volcano Jump - Enhanced Edition")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)
TITLE_FONT = pygame.font.SysFont("Arial", 36, bold=True)
SMALL_FONT = pygame.font.SysFont("Arial", 16)

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

# Feature flags / configurazioni
ENABLE_VICTORY_AT_CRATER = False  # Evita fine partita automatica appena si entra nel vulcano

# ----------------- Volcano Static Map (x/o) -----------------
# 'x' = barriera solida, 'o' = spazio libero
# Ogni carattere rappresenta un tile di dimensione TILE_SIZE
TILE_SIZE = 32

# Mappa semplice di esempio (larghezza adattata allo schermo)
# Puoi sostituirla con una mappa più lunga/complessa o caricarla da file
# Sezione di un vulcano a cono con cratere in cima
VOLCANO_MAP = [
    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "xooooooooooooooooooooooooooooooooooooooooooooooooooox",
    "xxoooooooooooooooooooooooooooooooooooooooooooooooooxx",
    "xxxoooooooooooooooooooooooooooooooooooooooooooooooxxx",
    "xxxxoooooooooooooooooooooooooooooooooooooooooooooxxxx",
    "xxxxxoooooooooooooooooooooooooooooooooooooooooooxxxxx",
    "xxxxxxoooooooooooooooooooooooooooooooooooooooooxxxxxx",
    "xxxxxxxoooooooooooooooooooooooooooooooooooooooxxxxxxx",
    "xxxxxxxxoooooooooooooooooooooooooooooooooooooxxxxxxxx",
    "xxxxxxxxxoooooooooooooooooooooooooooooooooooxxxxxxxxx",
    "xxxxxxxxxxoooooooooooooooooooooooooooooooooxxxxxxxxxx",
    "xxxxxxxxxxxoooooooooooooooooooooooooooooooxxxxxxxxxxx",
    "xxxxxxxxxxxxoooooooooooooooooooooooooooooxxxxxxxxxxxx",
    "xxxxxxxxxxxxxoooooooooooooooooooooooooooxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxoooooooooooooooooooooooooxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxoooooooooooooooooooooooxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxoooooooooooooooooooooxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxoooooooooooooooooooxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxoooooooooooooooooxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxoooooooooooooooxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxoooooooooooooxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxoooooooooooxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxoooooooooxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxoooooooxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxoooooxxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxxoooxxxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxxxoxxxxxxxxxxxxxxxxxxxxxxxxxx",
]

# Calcola dimensioni della mappa in pixel
VOLCANO_MAP_HEIGHT_PX = len(VOLCANO_MAP) * TILE_SIZE
VOLCANO_MAP_WIDTH_PX = len(VOLCANO_MAP[0]) * TILE_SIZE

def get_volcano_collision_rects():
    """Genera i rettangoli solidi (barriere) dalla mappa statica del vulcano."""
    rects = []
    for row_idx, row in enumerate(VOLCANO_MAP):
        for col_idx, ch in enumerate(row):
            if ch == 'x':
                x = col_idx * TILE_SIZE
                y = (len(VOLCANO_MAP) - 1 - row_idx) * TILE_SIZE  # 0 in basso
                rects.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
    return rects

VOLCANO_COLLISION_RECTS = get_volcano_collision_rects()

def build_volcano_platforms():
    """Crea piattaforme orizzontali sulle superfici superiori dei blocchi 'x'
    (solo dove sopra c'è aria 'o', così da avere sporgenze su cui saltare)."""
    platforms = []
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    # Stesso ancoraggio usato nel draw
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    rows = len(VOLCANO_MAP)
    cols = len(VOLCANO_MAP[0])

    for row_idx in range(rows):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        col = 0
        while col < cols:
            ch = row[col]
            above_open = (row_idx == 0) or (VOLCANO_MAP[row_idx-1][col] == 'o')
            if ch == 'x' and above_open:
                start_col = col
                # Estende finché restano 'x' con aria sopra
                while col < cols and row[col] == 'x' and ((row_idx == 0) or (VOLCANO_MAP[row_idx-1][col] == 'o')):
                    col += 1
                width = (col - start_col) * TILE_SIZE
                x_world = start_col * TILE_SIZE
                platforms.append(pygame.Rect(x_world, y_world, width, 12))
            else:
                col += 1
    return platforms

VOLCANO_PLATFORMS = build_volcano_platforms()

def draw_volcano_static(surface, world_offset):
    """Disegna la sezione del vulcano basata sulla mappa statica ('x'/'o') allineata ai km di livello."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM

    # Posizione mondo della riga superiore della mappa in modo che quando world_offset == start_px
    # la mappa occupi esattamente lo schermo (top = 0)
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    # Disegno solo le righe visibili per performance
    first_visible_row = max(0, int((0 - world_offset - map_top_world_y) // TILE_SIZE))
    last_visible_row = min(len(VOLCANO_MAP)-1, int((HEIGHT - world_offset - map_top_world_y) // TILE_SIZE) + 1)

    for row_idx in range(first_visible_row, last_visible_row + 1):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        y_screen = int(y_world + world_offset)
        for col_idx, ch in enumerate(row):
            if ch == 'x':
                x_world = col_idx * TILE_SIZE
                x_screen = int(x_world)
                # Disegno blocco roccia
                color = (90, 45, 10)
                pygame.draw.rect(surface, color, (x_screen, y_screen, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surface, (120, 60, 15), (x_screen+2, y_screen+2, TILE_SIZE-4, TILE_SIZE-4), 1)

def check_volcano_tile_collision(ball, world_offset):
    """Collisione con i blocchi 'x' della mappa vulcano.
    Ritorna (landed: bool, landing_y_world: float|None)"""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    landed = False
    landing_y = None
    margin = 8

    # Determina righe e colonne della zona attorno al player
    player_left = int((ball.x - ball.radius) // TILE_SIZE)
    player_right = int((ball.x + ball.radius) // TILE_SIZE) + 1
    player_world_y = ball.y
    player_row = int((player_world_y - map_top_world_y) // TILE_SIZE)

    row_start = max(0, player_row - 2)
    row_end = min(len(VOLCANO_MAP)-1, player_row + 2)
    col_start = max(0, player_left - 1)
    col_end = min(len(VOLCANO_MAP[0])-1, player_right + 1)

    for row_idx in range(row_start, row_end + 1):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        tile_top = y_world
        tile_bottom = y_world + TILE_SIZE
        for col_idx in range(col_start, col_end + 1):
            if row[col_idx] != 'x':
                continue
            x_world = col_idx * TILE_SIZE
            tile_left = x_world
            tile_right = x_world + TILE_SIZE

            # Check overlap in X
            if (ball.x + ball.radius) > tile_left and (ball.x - ball.radius) < tile_right:
                # Solo gestione atterraggio dall'alto
                if ball.vy >= 0:
                    ball_bottom = ball.y + ball.radius
                    prev_bottom = (ball.y - ball.vy) + ball.radius
                    if prev_bottom <= tile_top + margin and ball_bottom >= tile_top - margin:
                        landing_y = tile_top
                        landed = True
    return landed, landing_y

# ----------------- Volcano Top + Sky -----------------
CRATER_Y = 100  # altezza del cratere
eruption = False
particles = []
eruption_mode = False  # modalità eruzione/vittoria
eruption_start_time = 0
eruption_award_given = False
eruption_world_offset = None
crater_world_cache = None  # (left, right, top_world)

def get_crater_world_info():
    """Restituisce (crater_left, crater_right, crater_top_world) dalla mappa statica."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    for row_idx, row in enumerate(VOLCANO_MAP):
        if 'o' in row:
            min_c = None
            max_c = None
            for col_idx, ch in enumerate(row):
                if ch == 'o':
                    if min_c is None:
                        min_c = col_idx
                    max_c = col_idx
            if min_c is not None and max_c is not None:
                crater_left = min_c * TILE_SIZE
                crater_right = (max_c + 1) * TILE_SIZE
                crater_top_world = map_top_world_y + row_idx * TILE_SIZE
                return int(crater_left), int(crater_right), int(crater_top_world)
    # Fallback
    return WIDTH//3, WIDTH*2//3, 0

def draw_lava_jet(center_x, crater_top_screen, t_ms):
    """Disegna un getto centrale brillante per rappresentare la goccia trasformata."""
    jet_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    wave = math.sin(t_ms * 0.004) * 0.2 + 0.8
    jet_height = int(260 * wave)
    base_width = int(40 * wave + 20)
    for i in range(jet_height):
        y = crater_top_screen - i
        width = int(base_width * (1 - i / (jet_height + 1)) + 8)
        alpha = max(0, 220 - int(i * 0.7))
        color = (255, 140 + min(115, i // 2), 0, alpha)
        pygame.draw.line(jet_surface, color, (center_x - width//2, y), (center_x + width//2, y))
    # Bagliore alla base
    glow = pygame.Surface((160, 80), pygame.SRCALPHA)
    for r in range(70, 0, -10):
        a = int(60 * (r / 70))
        pygame.draw.ellipse(glow, (255, 80, 0, a), (80 - r, 40 - r//2, 2*r, r))
    screen.blit(jet_surface, (0, 0))
    screen.blit(glow, (center_x - 80, crater_top_screen - 30))
eruption_mode = False  # quando True, la goccia diventa fontana di lava dal cratere

def get_crater_info_from_static_map(world_offset):
    """Restituisce (crater_left, crater_right, crater_top) in coordinate schermo
    usando la prima riga dall'alto con 'o' (spazio aperto) come bordo del cratere."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    # Cerca la prima riga con spazi aperti 'o' (dall'alto)
    for row_idx, row in enumerate(VOLCANO_MAP):
        if 'o' in row:
            min_c = None
            max_c = None
            for col_idx, ch in enumerate(row):
                if ch == 'o':
                    if min_c is None:
                        min_c = col_idx
                    max_c = col_idx
            if min_c is not None and max_c is not None:
                crater_left = min_c * TILE_SIZE
                crater_right = (max_c + 1) * TILE_SIZE
                crater_top_world = map_top_world_y + row_idx * TILE_SIZE
                crater_top_screen = int(crater_top_world + world_offset)
                return int(crater_left), int(crater_right), int(crater_top_screen)
    # Fallback: centro schermo
    return WIDTH//3, WIDTH*2//3, HEIGHT//3

# ----------------- Power-ups -----------------
class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.collected = False
        self.radius = 20
        self.animation_time = 0
        self.effect_duration = 5.0  # secondi

        # Tipi di power-up vulcanologici
        self.types = {
            'thermal_boost': {'color': (255, 140, 0), 'effect': 'speed'},
            'magma_jump': {'color': (255, 0, 0), 'effect': 'jump'},
            'gas_shield': {'color': (0, 255, 255), 'effect': 'shield'},
            'volcanic_time': {'color': (255, 255, 0), 'effect': 'slow_time'}
        }

    def update(self, dt):
        self.animation_time += dt * 3

    def draw(self, surface, world_offset):
        if self.collected:
            return

        screen_y = self.y + world_offset
        if -50 < screen_y < HEIGHT + 50:
            # Animazione pulsante
            pulse = math.sin(self.animation_time) * 0.3 + 1.0
            radius = int(self.radius * pulse)

            color = self.types[self.type]['color']

            # Bagliore esterno
            glow_surface = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, 50), (radius*2, radius*2), radius*2)
            surface.blit(glow_surface, (self.x - radius*2, screen_y - radius*2))

            # Power-up principale
            pygame.draw.circle(surface, color, (int(self.x), int(screen_y)), radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(screen_y)), radius, 3)

            # Icona del power-up
            icon_color = (255, 255, 255)
            if self.type == 'thermal_boost':
                # Freccia verso l'alto
                points = [(self.x, screen_y-8), (self.x-6, screen_y+4), (self.x+6, screen_y+4)]
                pygame.draw.polygon(surface, icon_color, points)
            elif self.type == 'magma_jump':
                # Doppia freccia
                pygame.draw.polygon(surface, icon_color, [(self.x, screen_y-10), (self.x-4, screen_y-2), (self.x+4, screen_y-2)])
                pygame.draw.polygon(surface, icon_color, [(self.x, screen_y-2), (self.x-4, screen_y+6), (self.x+4, screen_y+6)])
            elif self.type == 'gas_shield':
                # Cerchio di protezione
                pygame.draw.circle(surface, icon_color, (int(self.x), int(screen_y)), 8, 2)
            elif self.type == 'volcanic_time':
                # Orologio
                pygame.draw.circle(surface, icon_color, (int(self.x), int(screen_y)), 6, 2)
                pygame.draw.line(surface, icon_color, (self.x, screen_y), (self.x, screen_y-4), 2)

    def check_collision(self, player):
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)

# ----------------- Collectibles -----------------
class Collectible:
    def __init__(self, x, y, value=100):
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.radius = 10
        self.animation_time = 0
        self.type = random.choice(['crystal', 'gem', 'mineral'])

        self.colors = {
            'crystal': (0, 255, 255),
            'gem': (255, 0, 255),
            'mineral': (255, 215, 0)
        }

    def update(self, dt):
        self.animation_time += dt * 4

    def draw(self, surface, world_offset):
        if self.collected:
            return

        screen_y = self.y + world_offset
        if -50 < screen_y < HEIGHT + 50:
            # Rotazione e scala
            rotation = self.animation_time
            scale = 0.9 + 0.1 * math.sin(self.animation_time * 2)

            color = self.colors[self.type]
            radius = int(self.radius * scale)

            # Stella brillante
            points = []
            for i in range(8):
                angle = rotation + i * math.pi / 4
                if i % 2 == 0:
                    r = radius
                else:
                    r = radius * 0.5

                x = self.x + r * math.cos(angle)
                y = screen_y + r * math.sin(angle)
                points.append((x, y))

            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)

            # Particelle scintillanti
            for i in range(3):
                px = self.x + random.randint(-15, 15)
                py = screen_y + random.randint(-15, 15)
                size = random.randint(1, 3)
                alpha = int(255 * random.random())
                sparkle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surface, (*color, alpha), (size, size), size)
                surface.blit(sparkle_surface, (px-size, py-size))

    def check_collision(self, player):
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)

# ----------------- Enemies -----------------
class Enemy:
    def __init__(self, x, y, enemy_type='lava_blob'):
        self.x = x
        self.y = y
        self.start_x = x
        self.type = enemy_type
        self.health = 1
        self.radius = 15
        self.vx = 0
        self.vy = 0
        self.animation_time = 0
        self.patrol_distance = 100
        self.direction = 1

        # Tipi di nemici vulcanologici
        if enemy_type == 'lava_blob':
            self.color = (255, 69, 0)
            self.speed = 1
            self.damage = 1
        elif enemy_type == 'gas_cloud':
            self.color = (128, 128, 128)
            self.speed = 0.5
            self.damage = 1
            self.radius = 25
        elif enemy_type == 'rock_fragment':
            self.color = (139, 69, 19)
            self.speed = 2
            self.damage = 2
        elif enemy_type == 'pyroclastic_flow':
            self.color = (64, 64, 64)
            self.speed = 3
            self.damage = 3
            self.radius = 30

    def update(self, dt, world_offset):
        self.animation_time += dt * 2

        if self.type == 'lava_blob':
            # Movimento di pattugliamento
            self.x += self.direction * self.speed
            if abs(self.x - self.start_x) > self.patrol_distance:
                self.direction *= -1

        elif self.type == 'gas_cloud':
            # Movimento fluttuante
            self.x += math.sin(self.animation_time) * 0.5
            self.y += math.cos(self.animation_time * 0.7) * 0.3

        elif self.type == 'rock_fragment':
            # Movimento erratico
            if random.random() < 0.1:
                self.vx = random.uniform(-2, 2)
                self.vy = random.uniform(-1, 1)
            self.x += self.vx * dt
            self.y += self.vy * dt

        elif self.type == 'pyroclastic_flow':
            # Movimento verso il basso
            self.y += self.speed

    def draw(self, surface, world_offset):
        screen_y = self.y + world_offset
        if -50 < screen_y < HEIGHT + 50:
            if self.type == 'lava_blob':
                # Blob di lava pulsante
                pulse = 0.8 + 0.2 * math.sin(self.animation_time * 3)
                radius = int(self.radius * pulse)

                # Bagliore
                glow_surface = pygame.Surface((radius*3, radius*3), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 100, 0, 100), (radius*1.5, radius*1.5), radius*1.5)
                surface.blit(glow_surface, (self.x - radius*1.5, screen_y - radius*1.5))

                # Corpo principale
                pygame.draw.circle(surface, self.color, (int(self.x), int(screen_y)), radius)
                pygame.draw.circle(surface, (255, 200, 0), (int(self.x), int(screen_y)), radius//2)

            elif self.type == 'gas_cloud':
                # Nuvola di gas semitrasparente
                for i in range(5):
                    offset_x = random.randint(-10, 10)
                    offset_y = random.randint(-10, 10)
                    size = random.randint(self.radius//2, self.radius)
                    alpha = random.randint(50, 100)

                    cloud_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(cloud_surface, (*self.color, alpha), (size, size), size)
                    surface.blit(cloud_surface, (self.x + offset_x - size, screen_y + offset_y - size))

            elif self.type == 'rock_fragment':
                # Frammento di roccia angolare
                points = []
                for i in range(6):
                    angle = i * math.pi / 3 + self.animation_time
                    variance = random.uniform(0.8, 1.2)
                    x = self.x + self.radius * variance * math.cos(angle)
                    y = screen_y + self.radius * variance * math.sin(angle)
                    points.append((x, y))

                pygame.draw.polygon(surface, self.color, points)
                pygame.draw.polygon(surface, (200, 200, 200), points, 2)

            elif self.type == 'pyroclastic_flow':
                # Flusso piroclastico
                for i in range(10):
                    x_offset = random.randint(-self.radius, self.radius)
                    y_offset = random.randint(-self.radius//2, self.radius//2)
                    size = random.randint(5, self.radius//2)
                    alpha = random.randint(100, 200)

                    flow_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(flow_surface, (*self.color, alpha), (size, size), size)
                    surface.blit(flow_surface, (self.x + x_offset - size, screen_y + y_offset - size))

    def check_collision(self, player):
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)

# ----------------- Enhanced Background with Smooth Transitions -----------------
def draw_enhanced_background(world_offset):
    km_height = world_offset / PIXEL_PER_KM

    # Transizioni fluide tra livelli
    if km_height < KM_PER_LEVEL[LEVEL_MANTELLO]:
        # Solo mantello
        draw_level_background(LEVEL_MANTELLO, 1.0, world_offset)
    elif km_height < KM_PER_LEVEL[LEVEL_MANTELLO] + 2:
        # Transizione mantello-crosta
        transition_progress = (km_height - KM_PER_LEVEL[LEVEL_MANTELLO]) / 2
        transition_progress = max(0, min(1, transition_progress))

        # Disegna entrambi i livelli con alpha blending
        draw_level_background(LEVEL_MANTELLO, 1 - transition_progress, world_offset)
        draw_level_background(LEVEL_CROSTA, transition_progress, world_offset)

        # Effetti di transizione
        draw_transition_effects(transition_progress, LEVEL_MANTELLO, LEVEL_CROSTA)

    elif km_height < KM_PER_LEVEL[LEVEL_CROSTA]:
        # Solo crosta
        draw_level_background(LEVEL_CROSTA, 1.0, world_offset)
    elif km_height < KM_PER_LEVEL[LEVEL_CROSTA] + 2:
        # Transizione crosta-vulcano
        transition_progress = (km_height - KM_PER_LEVEL[LEVEL_CROSTA]) / 2
        transition_progress = max(0, min(1, transition_progress))

        draw_level_background(LEVEL_CROSTA, 1 - transition_progress, world_offset)
        draw_volcano_section(transition_progress, world_offset, km_height)

        # Effetti di transizione
        draw_transition_effects(transition_progress, LEVEL_CROSTA, LEVEL_VULCANO)

    else:
        # Sezione vulcano completa
        draw_volcano_section(1.0, world_offset, km_height)

def draw_level_background(level, alpha, world_offset):
    scroll_y = int(world_offset % HEIGHT)

    # Crea superficie con alpha per le transizioni
    level_surface = pygame.Surface((WIDTH, HEIGHT))
    if alpha < 1.0:
        level_surface.set_alpha(int(255 * alpha))

    # Disegna il tile di background del livello
    tile = bg_tiles[level]
    y_pos = (scroll_y) % HEIGHT
    level_surface.blit(tile, (0, y_pos))
    level_surface.blit(tile, (0, y_pos - HEIGHT))
    if y_pos > 0:
        level_surface.blit(tile, (0, y_pos + HEIGHT))

    # Aggiungi effetti ambientali per ogni livello
    add_environmental_effects(level_surface, level, world_offset)

    screen.blit(level_surface, (0, 0))

def add_environmental_effects(surface, level, world_offset):
    if level == LEVEL_MANTELLO:
        # Particelle di magma fluttuanti
        for _ in range(15):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(2, 5)
            alpha = random.randint(50, 150)

            particle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color = (255, random.randint(100, 200), 0, alpha)
            pygame.draw.circle(particle_surface, color, (size, size), size)
            surface.blit(particle_surface, (x-size, y-size))

    elif level == LEVEL_CROSTA:
        # Cristalli e minerali
        for _ in range(8):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)

            # Cristallo brillante
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                radius = random.randint(3, 8)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))

            color = random.choice([(100, 200, 255), (200, 255, 100), (255, 200, 100)])
            pygame.draw.polygon(surface, color, points)

    elif level == LEVEL_VULCANO:
        # Scintille e braci
        for _ in range(20):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)

            spark_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color = (255, 255, random.randint(0, 100), random.randint(100, 255))
            pygame.draw.circle(spark_surface, color, (size, size), size)
            surface.blit(spark_surface, (x-size, y-size))

def draw_transition_effects(progress, from_level, to_level):
    # Effetti speciali durante le transizioni
    if from_level == LEVEL_MANTELLO and to_level == LEVEL_CROSTA:
        # Effetto di solidificazione del magma
        num_effects = int(20 * progress)
        for _ in range(num_effects):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(5, 15)

            # Cerchi che si espandono e si raffreddano
            color_intensity = 1 - progress
            color = (int(255 * color_intensity), int(100 * color_intensity), 0)

            effect_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surface, (*color, int(100 * progress)), (size, size), size, 2)
            screen.blit(effect_surface, (x-size, y-size))

    elif from_level == LEVEL_CROSTA and to_level == LEVEL_VULCANO:
        # Effetto di riscaldamento e crepe
        num_cracks = int(10 * progress)
        for _ in range(num_cracks):
            start_x = random.randint(0, WIDTH)
            start_y = random.randint(0, HEIGHT)

            # Crea una crepa che si illumina
            crack_points = [(start_x, start_y)]
            for i in range(random.randint(3, 8)):
                x = crack_points[-1][0] + random.randint(-20, 20)
                y = crack_points[-1][1] + random.randint(-20, 20)
                crack_points.append((x, y))

            # Disegna la crepa con bagliore
            if len(crack_points) > 1:
                glow_color = (255, int(150 * progress), 0, int(200 * progress))
                crack_color = (255, int(200 * progress), int(50 * progress))

                # Bagliore
                for i in range(len(crack_points) - 1):
                    pygame.draw.line(screen, crack_color, crack_points[i], crack_points[i+1], 3)

                # Linea principale
                for i in range(len(crack_points) - 1):
                    pygame.draw.line(screen, (255, 255, 100), crack_points[i], crack_points[i+1], 1)

def draw_volcano_section(alpha, world_offset, km_height):
    # Sezione vulcano con pareti e effetti
    screen.fill((0, 0, 0))

    # Disegna le pareti del vulcano
    volcano_walls, crater_info = draw_volcano_walls(km_height)
    screen.blit(volcano_walls, (0, 0))

    # Effetti di eruzione se vicini al cratere
    if km_height > KM_PER_LEVEL[LEVEL_VULCANO] * 0.9:
        draw_eruption_effects(crater_info, km_height)

# Rest of the existing volcano wall drawing functions remain the same...
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

# Load Background Tiles
try:
    bg_tiles = [
        pygame.image.load("./RoundedBlocks/lava.png").convert(),
        pygame.image.load("./RoundedBlocks/stone.png").convert(),
        pygame.image.load("./RoundedBlocks/ground.png").convert_alpha()
    ]

    for i in range(len(bg_tiles)):
        bg_tiles[i] = pygame.transform.scale(bg_tiles[i], (WIDTH, HEIGHT))
except Exception as e:
    # Fallback: crea tile procedurali se le immagini non esistono
    print(f"Errore caricamento immagini background: {e}. Uso tile procedurali.")
    bg_tiles = []
    colors = [(255, 100, 0), (139, 69, 19), (169, 169, 169)]
    for color in colors:
        tile = pygame.Surface((WIDTH, HEIGHT))
        tile.fill(color)
        bg_tiles.append(tile)

# ----------------- Game Objects Generation -----------------
def create_static_platforms():
    platforms = []
    platform_types = []
    powerups = []
    collectibles = []
    enemies = []

    platform_width = 100

    def add_platform(x, y, level):
        platform = pygame.Rect(x, y, platform_width, 16)
        platforms.append(platform)
        platform_types.append(level)

        # Aggiungi power-ups occasionalmente
        if random.random() < 0.15:  # 15% chance
            powerup_type = random.choice(['thermal_boost', 'magma_jump', 'gas_shield', 'volcanic_time'])
            powerups.append(PowerUp(x + platform_width//2, y - 30, powerup_type))

        # Aggiungi collectibles
        if random.random() < 0.3:  # 30% chance
            collectibles.append(Collectible(x + platform_width//2, y - 25))

        # Aggiungi nemici nei livelli superiori
        if level >= LEVEL_CROSTA and random.random() < 0.2:  # 20% chance
            enemy_types = ['lava_blob', 'gas_cloud', 'rock_fragment']
            if level == LEVEL_VULCANO:
                enemy_types.append('pyroclastic_flow')

            enemy_type = random.choice(enemy_types)
            enemies.append(Enemy(x + platform_width + 50, y, enemy_type))

        pass  # Rimosso debug generazione piattaforme

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

        # livello in base all'altezza
        height_km = abs(start_y - current_y) / PIXEL_PER_KM
        if height_km <= KM_PER_LEVEL[LEVEL_MANTELLO]:
            level = LEVEL_MANTELLO
        elif height_km <= KM_PER_LEVEL[LEVEL_CROSTA]:
            level = LEVEL_CROSTA
        else:
            level = LEVEL_VULCANO

        add_platform(x, current_y, level)

    pass  # Rimosso debug generazione livello
    return platforms, platform_types, powerups, collectibles, enemies

platforms, platform_types, powerups, collectibles, enemies = create_static_platforms()

# ----------------- Enhanced WobblyBall with Power-ups -----------------
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

        # Power-up system
        self.active_powerups = {}
        self.shield_active = False
        self.shield_time = 0
        self.health = 3
        self.max_health = 3
        self.invulnerable_time = 0

    def apply_input(self, keys):
        accel = 1.2
        max_speed = 8
        friction = 0.85

        # Power-up: thermal boost aumenta velocità
        if 'thermal_boost' in self.active_powerups:
            accel *= 1.5
            max_speed *= 1.3

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = max(-max_speed, self.vx - accel)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = min(max_speed, self.vx + accel)
        else:
            self.vx *= friction

    def jump(self):
        base_jump = -14

        # Power-up: magma jump aumenta altezza salto
        if 'magma_jump' in self.active_powerups:
            base_jump *= 1.5

        self.vy = base_jump
        audio.play('jump')

    def update_physics(self, dt, gravity=0.8):
        max_fall_speed = 15

        # Power-up: volcanic time rallenta il tempo
        if 'volcanic_time' in self.active_powerups:
            gravity *= 0.5
            max_fall_speed *= 0.7

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

        # Update power-ups
        self.update_powerups(dt)

        # Update invulnerability
        if self.invulnerable_time > 0:
            self.invulnerable_time -= dt

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

    def update_powerups(self, dt):
        # Aggiorna durata power-ups
        for powerup_type in list(self.active_powerups.keys()):
            self.active_powerups[powerup_type] -= dt
            if self.active_powerups[powerup_type] <= 0:
                del self.active_powerups[powerup_type]

        # Update shield
        if 'gas_shield' in self.active_powerups:
            self.shield_active = True
            self.shield_time += dt
        else:
            self.shield_active = False

    def activate_powerup(self, powerup_type, duration=5.0):
        self.active_powerups[powerup_type] = duration
        audio.play('powerup')

    def take_damage(self):
        if self.invulnerable_time > 0 or self.shield_active:
            return False

        self.health -= 1
        self.invulnerable_time = 1.0  # 1 secondo di invulnerabilità
        audio.play('lava_hit')

        # Effetto di danno
        for _ in range(10):
            self.particles.append([
                self.x + random.uniform(-10, 10),
                self.y + random.uniform(-10, 10),
                random.uniform(2, 4),
                random.randint(20, 30)
            ])

        return True

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

        # Effetto di invulnerabilità (lampeggio)
        if self.invulnerable_time > 0 and int(t * 10) % 2:
            return

        # Shield effect
        if self.shield_active:
            shield_radius = self.radius + 10 + 5 * math.sin(self.shield_time * 4)
            shield_surface = pygame.Surface((shield_radius*2, shield_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (0, 255, 255, 100), (shield_radius, shield_radius), shield_radius, 3)
            surf.blit(shield_surface, (cx - shield_radius, cy - shield_radius))

        # Corpo principale con effetti power-up
        color = self.color
        if 'thermal_boost' in self.active_powerups:
            color = (255, 100, 0)  # Più caldo
        elif 'magma_jump' in self.active_powerups:
            color = (255, 255, 100)  # Più luminoso

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
        pygame.draw.polygon(surf, color, points)
        pygame.draw.aalines(surf, (255,220,140), True, points, 1)

# ----------------- UI System -----------------
def draw_menu():
    screen.fill((50, 20, 20))

    # Titolo con effetto lava
    title_y = 150
    title_text = TITLE_FONT.render("VOLCANO JUMP", True, (255, 165, 0))
    title_shadow = TITLE_FONT.render("VOLCANO JUMP", True, (100, 50, 0))

    screen.blit(title_shadow, (WIDTH//2 - title_text.get_width()//2 + 3, title_y + 3))
    screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, title_y))

    # Sottotitolo
    subtitle = FONT.render("Enhanced Edition", True, (255, 255, 255))
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, title_y + 60))

    # Menu options
    menu_options = ["GIOCA", "CLASSIFICA", "ESCI"]
    selected_option = getattr(draw_menu, 'selected', 0)

    for i, option in enumerate(menu_options):
        y = 350 + i * 50
        color = (255, 200, 0) if i == selected_option else (255, 255, 255)
        text = FONT.render(option, True, color)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, y))

    # Istruzioni
    instructions = [
        "Usa FRECCE o WASD per muoverti",
        "SPAZIO per saltare",
        "Raccogli power-ups e cristalli!",
        "Evita i nemici vulcanici"
    ]

    for i, instruction in enumerate(instructions):
        text = SMALL_FONT.render(instruction, True, (200, 200, 200))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, 500 + i * 25))

def draw_leaderboard():
    screen.fill((30, 30, 50))

    title = TITLE_FONT.render("CLASSIFICA", True, (255, 215, 0))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

    if high_scores:
        for i, score_entry in enumerate(high_scores[:10]):
            y = 150 + i * 40
            name_text = FONT.render(f"{i+1}. {score_entry['name']}", True, (255, 255, 255))
            score_text = FONT.render(f"{score_entry['score']} ({score_entry['height']:.1f}km)", True, (255, 215, 0))
            date_text = SMALL_FONT.render(score_entry['date'], True, (150, 150, 150))

            screen.blit(name_text, (50, y))
            screen.blit(score_text, (250, y))
            screen.blit(date_text, (450, y + 5))
    else:
        no_scores = FONT.render("Nessun punteggio registrato", True, (150, 150, 150))
        screen.blit(no_scores, (WIDTH//2 - no_scores.get_width()//2, 300))

    back_text = SMALL_FONT.render("Premi ESC per tornare al menu", True, (200, 200, 200))
    screen.blit(back_text, (WIDTH//2 - back_text.get_width()//2, HEIGHT - 50))

def draw_game_over():
    # Crea un overlay scuro semi-trasparente che pulsa
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    pulse = (math.sin(pygame.time.get_ticks() * 0.002) * 0.1 + 0.7)  # Varia tra 0.6 e 0.8
    overlay.set_alpha(int(160 * pulse))  # L'overlay pulsa leggermente
    screen.blit(overlay, (0, 0))

    # Testo "GAME OVER" con effetto glow rosso pulsante
    glow_size = int(4 + math.sin(pygame.time.get_ticks() * 0.004) * 2)  # Varia tra 2 e 6
    for offset in range(glow_size, 0, -1):
        glow_color = (128, 0, 0, int(255 / offset))
        game_over_text = TITLE_FONT.render("GAME OVER", True, glow_color)
        pos_x = WIDTH//2 - game_over_text.get_width()//2
        pos_y = HEIGHT//2 - 100
        screen.blit(game_over_text, (pos_x - offset, pos_y))
        screen.blit(game_over_text, (pos_x + offset, pos_y))
        screen.blit(game_over_text, (pos_x, pos_y - offset))
        screen.blit(game_over_text, (pos_x, pos_y + offset))
    
    # Testo principale "GAME OVER"
    game_over_text = TITLE_FONT.render("GAME OVER", True, (255, 0, 0))
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))

    # Punteggio finale
    final_score_text = FONT.render(f"Punteggio Finale: {score}", True, (255, 255, 255))
    screen.blit(final_score_text, (WIDTH//2 - final_score_text.get_width()//2, HEIGHT//2 - 20))

    # Istruzioni per ricominciare/uscire con effetto pulsante
    pulse_color = int(200 + math.sin(pygame.time.get_ticks() * 0.005) * 55)  # Varia tra 145 e 255
    restart_text = FONT.render("Premi R per riprovare", True, (pulse_color, pulse_color, pulse_color))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 40))
    
    quit_text = FONT.render("Premi ESC per tornare al menu", True, (180, 180, 180))
    screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, HEIGHT//2 + 80))

    height_km = world_offset / PIXEL_PER_KM
    height_text = FONT.render(f"Altezza Raggiunta: {height_km:.2f} km", True, (255, 255, 255))
    screen.blit(height_text, (WIDTH//2 - height_text.get_width()//2, HEIGHT//2))

    restart_text = SMALL_FONT.render("Premi R per ricominciare o ESC per il menu", True, (200, 200, 200))
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 100))

def draw_name_input():
    screen.fill((30, 30, 60))

    title = TITLE_FONT.render("NUOVO RECORD!", True, (255, 215, 0))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 200))

    prompt = FONT.render("Inserisci il tuo nome:", True, (255, 255, 255))
    screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 300))

    # Input box
    input_box = pygame.Rect(WIDTH//2 - 150, 350, 300, 40)
    pygame.draw.rect(screen, (255, 255, 255), input_box, 2)

    name_surface = FONT.render(player_name, True, (255, 255, 255))
    screen.blit(name_surface, (input_box.x + 10, input_box.y + 10))

    instruction = SMALL_FONT.render("Premi ENTER per confermare", True, (200, 200, 200))
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, 420))

def draw_hud():
    # Salute
    for i in range(player.max_health):
        x = 10 + i * 30
        y = 10
        if i < player.health:
            pygame.draw.circle(screen, (255, 0, 0), (x + 10, y + 10), 8)
        else:
            pygame.draw.circle(screen, (100, 100, 100), (x + 10, y + 10), 8, 2)

    # Power-ups attivi
    y_offset = 50
    for powerup_type, time_left in player.active_powerups.items():
        text = SMALL_FONT.render(f"{powerup_type}: {time_left:.1f}s", True, (255, 255, 0))
        screen.blit(text, (10, y_offset))
        y_offset += 20

    # Altezza e punteggio
    height_km = world_offset / PIXEL_PER_KM
    height_text = FONT.render(f"Altezza: {height_km:.2f} km", True, (255, 255, 255))
    level_text = FONT.render(f"Livello: {level_names[current_level]}", True, (255, 255, 255))
    score_text = FONT.render(f"Punteggio: {score}", True, (255, 255, 255))

    screen.blit(height_text, (10, HEIGHT - 80))
    screen.blit(level_text, (10, HEIGHT - 60))
    screen.blit(score_text, (10, HEIGHT - 40))

# ----------------- Utilities -----------------
def lerp_color(c1, c2, t):
    return (int(c1[0]*(1-t)+c2[0]*t),
            int(c1[1]*(1-t)+c2[1]*t),
            int(c1[2]*(1-t)+c2[2]*t))

def check_platform_collision(ball, platforms, world_offset):
    """Collision robusta con logging migliorato"""
    for i, plat in enumerate(platforms):
        plat_rect = plat.copy()
        plat_rect.y += world_offset

        if ball.x + ball.radius > plat_rect.left and ball.x - ball.radius < plat_rect.right:
            if ball.vy >= 0:
                ball_bottom = ball.y + ball.radius
                prev_y = ball.y - ball.vy
                prev_bottom = prev_y + ball.radius

                margin = 8
                if prev_bottom <= plat_rect.top + margin and ball_bottom >= plat_rect.top - margin:
                    # Rimosso debug collisioni
                    return True, i

    return False, None

def reset_game():
    global player, world_offset, score, is_game_over, tiles_revealed, platforms, platform_types, current_level
    global powerups, collectibles, enemies, game_state
    global eruption_mode

    # Reset completo delle variabili di gioco
    world_offset = 0
    score = 0
    is_game_over = False
    game_state = PLAYING
    eruption_mode = False
    tiles_revealed = 1
    current_level = LEVEL_MANTELLO

    # Ricrea tutte le piattaforme
    platforms, platform_types, powerups, collectibles, enemies = create_static_platforms()

    # Reset completo del player
    start_platform = platforms[0]
    player.x = start_platform.centerx
    player.y = start_platform.top - player.radius
    player.vx = 0
    player.vy = 0
    player.radius = player.base_radius
    player.trail.clear()
    player.particles.clear()
    player.health = player.max_health
    player.active_powerups.clear()
    player.invulnerable_time = 0

    # Effetto sonoro di reset
    try:
        audio.play('reset')
    except:
        pass

    log_game_event("🔄 Nuova partita iniziata!")

# ----------------- Main Game Loop -----------------
start_platform = platforms[0]
player = WobblyBall(start_platform.centerx, start_platform.top - 32)
world_offset = 0.0
t_global = 0.0
score = 0
is_game_over = False
tiles_revealed = 1
jumps_made = 0
current_level = LEVEL_MANTELLO

def main():
    global t_global, world_offset, score, is_game_over, tiles_revealed, jumps_made, current_level
    global game_state, player_name, high_scores
    global eruption_mode

    menu_selected = 0
    running = True

    while running:
        dt = clock.tick(60)/1000.0
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
                            game_state = PLAYING
                            reset_game()
                        elif menu_selected == 1:  # CLASSIFICA
                            log_game_event("🏆 Visualizzazione classifica")
                            game_state = LEADERBOARD
                        elif menu_selected == 2:  # ESCI
                            log_game_event("👋 Uscita dal gioco")
                            running = False

                elif game_state == PLAYING:
                    if ev.key == pygame.K_SPACE:
                        grounded, idx = check_platform_collision(player, platforms, world_offset)
                        if grounded:
                            player.jump()
                        else:
                            player.vy = -10

                        # Gestiamo il Game Over sia dallo stato che dal flag is_game_over
            
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

                # Eruzione continua quando raggiungi la cima della mappa del vulcano
                vulcano_start_px = KM_PER_LEVEL[LEVEL_CROSTA] * PIXEL_PER_KM
                vulcano_end_px = vulcano_start_px + VOLCANO_MAP_HEIGHT_PX
                if not eruption_mode and world_offset >= (vulcano_end_px - HEIGHT * 0.6):
                    eruption_mode = True
                    eruption_start_time = pygame.time.get_ticks()
                    eruption_award_given = False
                    # Blocca la camera sul cratere: calcola world_offset da fissare
                    c_left, c_right, c_top_world = get_crater_world_info()
                    eruption_world_offset = (HEIGHT * 0.45) - c_top_world

            km_height = world_offset / PIXEL_PER_KM
            # Collisioni
            grounded, idx = (False, None)
            landing_source = None  # 'base', 'volcano_surface', 'volcano_dynamic', or None
            if km_height < KM_PER_LEVEL[LEVEL_CROSTA]:
                grounded, idx = check_platform_collision(player, platforms, world_offset)
                if grounded:
                    landing_source = 'base'
            else:
                # 1) Piattaforme di superficie del vulcano (derivate dalla mappa)
                grounded, idx = check_platform_collision(player, VOLCANO_PLATFORMS, world_offset)
                if grounded:
                    landing_source = 'volcano_surface'
                else:
                    # 2) Piattaforme dinamiche nella sezione vulcano
                    volcano_dyn_plats = [platforms[i] for i, t in enumerate(platform_types) if t == LEVEL_VULCANO]
                    grounded, idx = check_platform_collision(player, volcano_dyn_plats, world_offset)
                    if grounded:
                        landing_source = 'volcano_dynamic'
                    else:
                        # 3) Fallback: collisione diretta coi tile top
                        landed_tmp, _ = check_volcano_tile_collision(player, world_offset)
                        if landed_tmp:
                            grounded = True
                            landing_source = None
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
            screen.fill((0,0,0))
            draw_enhanced_background(world_offset)
            # Disegna la mappa statica del vulcano sopra al background quando siamo nel vulcano
            height_km = world_offset / PIXEL_PER_KM
            if height_km >= KM_PER_LEVEL[LEVEL_CROSTA]:
                draw_volcano_static(screen, world_offset)
                # Se in eruzione, disegna fontana di lava continua dal cratere e colate sui fianchi
                if eruption_mode:
                    crater_info = get_crater_info_from_static_map(world_offset)
                    draw_eruption_effects(crater_info, height_km)

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
                        pygame.draw.rect(screen, color, rect)
            else:
                # Piattaforme di superficie nel vulcano
                for plat in VOLCANO_PLATFORMS:
                    rect = plat.copy()
                    rect.y += world_offset
                    if -50 < rect.y < HEIGHT + 50:
                        pygame.draw.rect(screen, (110, 55, 20), rect)
                # Piattaforme dinamiche nel vulcano
                for i, plat in enumerate(platforms):
                    if platform_types[i] != LEVEL_VULCANO:
                        continue
                    rect = plat.copy()
                    rect.y += world_offset
                    if -50 < rect.y < HEIGHT + 50:
                        pygame.draw.rect(screen, (169, 169, 169), rect)

            # Draw power-ups
            for powerup in powerups:
                powerup.draw(screen, world_offset)

            # Draw collectibles
            for collectible in collectibles:
                collectible.draw(screen, world_offset)

            # Draw enemies (evita durante eruzione per pulizia visiva)
            if not eruption_mode:
                for enemy in enemies:
                    enemy.draw(screen, world_offset)

            # Draw player: durante eruzione, la goccia è rappresentata dal getto centrale
            if not eruption_mode:
                player.draw_trail(screen)
                player.draw_particles(screen)
                player.draw_wobbly(screen, t_global)

            # Draw HUD
            draw_hud()

            if game_state == GAME_OVER:
                draw_game_over()

            # Overlay eruzione: fontana al cratere e premio/leaderboard
            if height_km >= KM_PER_LEVEL[LEVEL_CROSTA] and eruption_mode:
                c_left, c_right, c_top_world = get_crater_world_info()
                crater_top_screen = int(c_top_world + world_offset)
                crater_info = (int(c_left), int(c_right), crater_top_screen)
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