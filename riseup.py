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
        try:
            import numpy as np
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = 4096 * math.sin(2 * math.pi * frequency * i / sample_rate)
                arr.append([int(wave), int(wave)])
            
            # Usa numpy se disponibile, altrimenti disabilita audio
            arr_np = np.array(arr, dtype=np.int16)
            sound = pygame.sndarray.make_sound(arr_np)
            return sound
        except ImportError:
            # Se numpy non è disponibile, crea un suono silenzioso
            return pygame.mixer.Sound(buffer=bytes(1024))
        except Exception:
            # Per qualsiasi altro errore, ritorna un suono silenzioso
            return pygame.mixer.Sound(buffer=bytes(1024))

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

    # Disegna particelle di lava esplosive - VERSIONE STABILE
    num_particles = int(40 * eruption_intensity * wave)
    time_seed = int(pygame.time.get_ticks() / 100)  # Cambia ogni 100ms per movimento fluido
    
    for i in range(num_particles):
        # Usa l'indice della particella per valori deterministici
        particle_seed = (i + time_seed) * 37  # 37 è un numero primo per buona distribuzione
        
        # Angolo fisso basato su seed
        angle = (particle_seed % 314) / 100.0  # 0 a pi circa
        speed = (5 + (particle_seed % 10)) * eruption_intensity
        distance = ((particle_seed % 150)) * wave
        
        x = crater_center + math.cos(angle) * distance
        y = crater_top - math.sin(angle) * distance - ((particle_seed % 50))
        size = 3 + (particle_seed % 6)  # da 3 a 8
        alpha = int((150 + (particle_seed % 105)) * (1 - distance/200))  # 150-255
        color_variation = 150 + (particle_seed % 50)  # 150-200
        color = (255, color_variation, 0, alpha)
        
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
        
        # Usa una curva più naturale per il flusso - VERSIONE STABILE
        flow_steps = 8 + (i * 3) % 13  # da 8 a 20, deterministico per ogni flusso
        max_flow_length = 100  # Limita la lunghezza massima delle colate
        
        for step in range(flow_steps):
            if current_y - crater_top > max_flow_length:  # Limita la discesa
                break
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
MANTELLO_HEIGHT_PX = 69 * PIXEL_PER_KM
CROSTA_HEIGHT_PX = 40 * PIXEL_PER_KM
VULCANO_HEIGHT_PX = 60 * PIXEL_PER_KM

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
    "xxxxxxxxxxxxxxxxxxxxxxxxxooxxxxxxxxxxxxxxxxxxxxxxxxxxx",
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

def build_conical_volcano_platforms():
    """Crea piattaforme invisibili che seguono la forma conica del vulcano - VERSIONE CORRETTA"""
    platforms = []
    
    # Parametri del vulcano conico (devono corrispondere al nuovo design)
    base_width = WIDTH * 0.65      # Larghezza alla base (più stretta)
    crater_width = WIDTH * 0.15    # Larghezza al cratere (molto più stretta)
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    
    # Offset mondo della mappa
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    
    # Crea piattaforme a intervalli regolari seguendo la forma conica
    platform_spacing = 90  # Pixel tra una piattaforma e l'altra
    num_levels = int(VOLCANO_MAP_HEIGHT_PX / platform_spacing)
    
    for i in range(num_levels):
        # Altezza relativa di questa piattaforma (0 = base, 1 = cratere)
        height_ratio = i / num_levels
        y_world = map_top_world_y + (VOLCANO_MAP_HEIGHT_PX - i * platform_spacing)
        
        # Calcola la larghezza del passaggio a questa altezza
        current_passage_width = base_width - (base_width - crater_width) * height_ratio
        passage_left = (WIDTH - current_passage_width) / 2
        passage_right = WIDTH - passage_left
        
        # Crea piattaforme distribuite nel passaggio interno del cono
        platform_width = min(70, current_passage_width * 0.4)  # Adatta alla larghezza disponibile
        passage_usable = current_passage_width - platform_width - 20  # Margini di sicurezza
        
        if passage_usable > 0 and current_passage_width > 50:  # Solo se c'è spazio sufficiente
            # Numero di piattaforme adatto alla larghezza ristretta
            if current_passage_width > 200:
                num_platforms_at_level = 3
            elif current_passage_width > 120:
                num_platforms_at_level = 2
            else:
                num_platforms_at_level = 1
            
            for j in range(num_platforms_at_level):
                if num_platforms_at_level == 1:
                    x = (passage_left + passage_right) / 2 - platform_width / 2
                else:
                    spacing = passage_usable / (num_platforms_at_level - 1) if num_platforms_at_level > 1 else 0
                    x = passage_left + 10 + j * spacing  # 10 pixel di margine dal bordo
                
                # Assicurati che la piattaforma sia dentro i bordi con margine
                x = max(passage_left + 10, min(passage_right - platform_width - 10, x))
                
                platform = pygame.Rect(x, y_world, platform_width, 12)
                platforms.append(platform)
    
    # Aggiungi una piattaforma speciale vicino al cratere (punto di partenza per l'eruzione)
    crater_platform_y = map_top_world_y + VOLCANO_MAP_HEIGHT_PX - 150  # 150 pixel sotto il cratere
    crater_passage_width = crater_width + 40  # Un po' più largo del cratere
    crater_platform_x = (WIDTH - 80) / 2  # Piattaforma larga 80 pixel, centrata
    crater_platform = pygame.Rect(crater_platform_x, crater_platform_y, 80, 12)
    platforms.append(crater_platform)
    
    return platforms

def get_crater_info_from_conical_volcano(world_offset):
    """Restituisce (crater_left, crater_right, crater_top) in coordinate schermo
    per il nuovo vulcano conico"""
    # Parametri del cratere (larghezza minima del vulcano conico)
    crater_width = WIDTH * 0.15  # Aggiornato per corrispondere al nuovo design stretto
    crater_left = (WIDTH - crater_width) / 2
    crater_right = WIDTH - crater_left
    
    # Il cratere è sempre in cima allo schermo quando siamo nel vulcano
    crater_top = 80  # Poco sotto il bordo superiore
    
    return int(crater_left), int(crater_right), int(crater_top)

def check_crater_entry(player, y_offset):
    """Controlla se il giocatore è entrato nel cratere del vulcano"""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    
    # Coordinate del cratere (in cima al vulcano) - coordinate mondo
    crater_world_y = map_top_world_y + VOLCANO_MAP_HEIGHT_PX - 50  # 50 pixel sotto la cima
    
    # Dimensioni del cratere (apertura stretta)
    crater_width = WIDTH * 0.15
    crater_left = (WIDTH - crater_width) / 2
    crater_right = crater_left + crater_width
    
    # Controlla se il giocatore è nel cratere
    # player.y è già in coordinate mondo
    player_world_y = player.y
    player_center_x = player.x + player.radius  # Centro del giocatore
    
    # DEBUG: stampa per capire i valori
    # print(f"Player Y: {player_world_y}, Crater Y: {crater_world_y}, Player X: {player_center_x}")
    
    # Il giocatore deve essere:
    # 1. Nella zona verticale del cratere (sopra la soglia) - Y più piccolo = più in alto
    # 2. Nella zona orizzontale del cratere (tra i bordi)
    is_in_crater_vertically = player_world_y <= crater_world_y  # Cambiato <= per Y verso l'alto
    is_in_crater_horizontally = crater_left <= player_center_x <= crater_right
    
    return is_in_crater_vertically and is_in_crater_horizontally

def check_conical_volcano_walls_collision(ball, world_offset):
    """Controlla che la goccia rimanga nel passaggio del vulcano conico - VERSIONE CORRETTA"""
    # Parametri del vulcano conico (devono corrispondere a draw_conical_volcano_walls)
    base_width = WIDTH * 0.65      # Aggiornato per il nuovo design più stretto
    crater_width = WIDTH * 0.15    # Aggiornato per il nuovo design più stretto
    
    # Calcola l'altezza relativa nel vulcano
    volcano_start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    volcano_end_km = KM_PER_LEVEL[LEVEL_VULCANO]
    current_km = world_offset / PIXEL_PER_KM
    
    if current_km < volcano_start_km or current_km > volcano_end_km:
        return False
    
    # Progressione nel vulcano (0 = base, 1 = cratere)
    volcano_progress = (current_km - volcano_start_km) / (volcano_end_km - volcano_start_km)
    
    # Calcola la larghezza del passaggio alla posizione Y del giocatore
    screen_y = ball.y - world_offset
    height_ratio = (HEIGHT - screen_y) / HEIGHT  # 0 = basso schermo, 1 = alto schermo
    height_ratio = max(0, min(1, height_ratio))
    
    current_passage_width = base_width - (base_width - crater_width) * height_ratio
    passage_left = (WIDTH - current_passage_width) / 2
    passage_right = WIDTH - passage_left
    
    # Controlla solo se la goccia esce dai bordi del passaggio interno del cono
    collision = False
    
    # Parete sinistra - sposta dolcemente verso il centro
    if ball.x - ball.radius < passage_left:
        ball.x = passage_left + ball.radius + 2
        collision = True
        
    # Parete destra - sposta dolcemente verso il centro  
    elif ball.x + ball.radius > passage_right:
        ball.x = passage_right - ball.radius - 2
        collision = True
    
    return collision

VOLCANO_PLATFORMS = build_conical_volcano_platforms()

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
    """Disegna una fontana di lava organica che rappresenta la goccia trasformata."""
    # Parametri per movimento organico
    time_sec = t_ms / 1000.0
    main_pulse = math.sin(time_sec * 2.0) * 0.3 + 0.7  # Pulsazione principale
    secondary_wave = math.sin(time_sec * 5.0) * 0.2    # Oscillazione secondaria
    
    # Altezza e larghezza base della fontana
    base_height = int(300 * main_pulse)
    base_width = int(50 + secondary_wave * 15)
    
    # Superficie per effetti con alpha
    jet_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Disegna la fontana principale con forma organica
    num_streams = 12  # Numero di "fili" di lava
    
    for stream in range(num_streams):
        stream_angle = (stream / num_streams) * math.pi * 2
        stream_offset = math.sin(time_sec * 3.0 + stream * 0.5) * 8
        
        # Parametri unici per ogni filo
        stream_height = base_height + stream_offset
        stream_start_x = center_x + math.cos(stream_angle) * (base_width // 4)
        
        # Disegna ogni filo di lava con curve organiche
        points = []
        for i in range(int(stream_height // 4)):
            progress = i / (stream_height // 4)
            
            # Movimento organico verso l'alto
            y = crater_top_screen - i * 4
            
            # Curva laterale organica
            lateral_movement = math.sin(progress * math.pi * 4 + time_sec * 4) * 20 * (1 - progress)
            x = stream_start_x + lateral_movement
            
            points.append((int(x), int(y)))
        
        # Disegna il filo di lava con gradiente di colore
        if len(points) > 1:
            for i in range(len(points) - 1):
                progress = i / len(points)
                
                # Colore che cambia dall'arancione brillante al rosso scuro
                r = int(255 * (1 - progress * 0.3))
                g = int((200 - progress * 150) * main_pulse)
                b = int(50 * (1 - progress))
                alpha = int(255 * (1 - progress * 0.5) * main_pulse)
                
                # Spessore che diminuisce verso l'alto
                thickness = max(1, int(8 * (1 - progress)))
                
                # Disegna bagliore
                glow_surface = pygame.Surface((thickness * 4, thickness * 4), pygame.SRCALPHA)
                glow_color = (r, max(50, g), b, alpha // 3)
                pygame.draw.circle(glow_surface, glow_color, (thickness * 2, thickness * 2), thickness * 2)
                jet_surface.blit(glow_surface, (points[i][0] - thickness * 2, points[i][1] - thickness * 2))
                
                # Disegna il nucleo
                pygame.draw.circle(jet_surface, (r, g, b, alpha), points[i], thickness)
    
    # Effetto base del cratere - lava che ribolla
    base_glow_radius = int(80 + math.sin(time_sec * 6) * 20)
    for radius_layer in range(base_glow_radius, 20, -8):
        alpha = int((radius_layer / base_glow_radius) * 150 * main_pulse)
        glow_color = (255, max(100, 200 - radius_layer), 0, alpha)
        glow_surface = pygame.Surface((radius_layer * 2, radius_layer), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, glow_color, (0, 0, radius_layer * 2, radius_layer))
        jet_surface.blit(glow_surface, (center_x - radius_layer, crater_top_screen - radius_layer // 2))
    
    # Particelle di lava che volano via - VERSIONE STABILE
    num_particles = int(20 * main_pulse)
    time_offset = int(time_sec * 10) % 1000  # Seed temporale stabile
    
    for i in range(num_particles):
        particle_seed = (i * 47 + time_offset) % 1000  # Seed deterministico
        particle_angle = (particle_seed % 628) / 100.0  # 0 a ~6.28 (2*pi)
        distance_factor = 0.6 + ((particle_seed % 60) / 100.0)  # 0.6 a 1.2
        particle_distance = base_height * distance_factor
        particle_x = center_x + math.cos(particle_angle) * particle_distance * 0.3
        particle_y = crater_top_screen - particle_distance
        
        # Particelle che cadono con fisica
        fall_offset = (time_sec * 2) % 200  # Caduta ciclica
        particle_y += fall_offset
        
        if particle_y < HEIGHT:  # Solo se visibile
            particle_size = 2 + (particle_seed % 5)  # da 2 a 6
            particle_alpha = max(0, int(255 * (1 - fall_offset / 200)))
            color_variation = 150 + (particle_seed % 51)  # 150-200
            particle_color = (255, color_variation, 0, particle_alpha)
            
            particle_surface = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, particle_color, (particle_size, particle_size), particle_size)
            jet_surface.blit(particle_surface, (int(particle_x) - particle_size, int(particle_y) - particle_size))
    
    # Applica tutto allo schermo
    screen.blit(jet_surface, (0, 0))
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

            # Particelle scintillanti - VERSIONE STABILE
            time_seed = int(pygame.time.get_ticks() / 200) % 1000  # Cambia ogni 200ms
            crystal_seed = int(self.x + self.y) % 100  # Seed basato su posizione
            
            for i in range(3):
                particle_seed = (time_seed + crystal_seed + i * 17) % 1000
                px = self.x + ((particle_seed % 31) - 15)  # -15 a +15
                py = screen_y + (((particle_seed + 31) % 31) - 15)  # -15 a +15
                size = 1 + (particle_seed % 3)  # 1-3
                alpha = int(255 * ((particle_seed % 100) / 100.0))  # 0-255
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
            # Movimento erratico - VERSIONE STABILE
            time_check = int(pygame.time.get_ticks() / 100) % 100  # Ogni 100ms, ciclo 0-99
            fragment_id = int(self.x + self.y) % 100  # ID basato su posizione
            if (time_check + fragment_id) % 100 < 10:  # 10% probabilità stabile
                seed = (time_check + fragment_id) % 1000
                self.vx = ((seed % 400) - 200) / 100.0  # -2 a +2
                self.vy = ((seed % 200) - 100) / 100.0  # -1 a +1
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
                # Nuvola di gas semitrasparente - VERSIONE STABILE
                cloud_seed = int(self.x + self.y) % 1000  # Seed basato su posizione
                time_seed = int(pygame.time.get_ticks() / 500) % 100  # Cambia ogni 500ms
                
                for i in range(5):
                    particle_seed = (cloud_seed + time_seed + i * 13) % 1000
                    offset_x = ((particle_seed % 21) - 10)  # -10 a +10
                    offset_y = (((particle_seed + 21) % 21) - 10)  # -10 a +10
                    size = self.radius//2 + ((particle_seed % (self.radius//2 + 1)))
                    alpha = 50 + (particle_seed % 51)  # 50-100

                    cloud_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(cloud_surface, (*self.color, alpha), (size, size), size)
                    surface.blit(cloud_surface, (self.x + offset_x - size, screen_y + offset_y - size))

            elif self.type == 'rock_fragment':
                # Frammento di roccia angolare - VERSIONE STABILE
                fragment_seed = int(self.x + self.y) % 1000
                points = []
                for i in range(6):
                    angle = i * math.pi / 3 + self.animation_time
                    variance = 0.8 + ((fragment_seed + i * 7) % 40) / 100.0  # 0.8-1.2
                    x = self.x + self.radius * variance * math.cos(angle)
                    y = screen_y + self.radius * variance * math.sin(angle)
                    points.append((x, y))

                pygame.draw.polygon(surface, self.color, points)
                pygame.draw.polygon(surface, (200, 200, 200), points, 2)

            elif self.type == 'pyroclastic_flow':
                # Flusso piroclastico - VERSIONE STABILE
                flow_seed = int(self.x + self.y) % 1000
                time_seed = int(pygame.time.get_ticks() / 300) % 100  # Cambia ogni 300ms
                
                for i in range(10):
                    particle_seed = (flow_seed + time_seed + i * 11) % 1000
                    x_offset = ((particle_seed % (self.radius * 2 + 1)) - self.radius)
                    y_offset = (((particle_seed + 100) % (self.radius + 1)) - self.radius//2)
                    size = 5 + (particle_seed % (self.radius//2 - 4))  # 5 a radius//2
                    alpha = 100 + (particle_seed % 101)  # 100-200

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
        # Particelle di magma fluttuanti - VERSIONE STABILE
        time_seed = int(pygame.time.get_ticks() / 1000) % 1000  # Cambia ogni secondo
        offset_seed = int(world_offset / 100) % 100  # Basato sulla posizione
        
        for i in range(15):
            particle_seed = (time_seed + offset_seed + i * 23) % 1000
            x = (particle_seed % WIDTH)
            y = ((particle_seed + 200) % HEIGHT)
            size = 2 + (particle_seed % 4)  # 2-5
            alpha = 50 + (particle_seed % 101)  # 50-150

            particle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color_variation = 100 + (particle_seed % 101)  # 100-200
            color = (255, color_variation, 0, alpha)
            pygame.draw.circle(particle_surface, color, (size, size), size)
            surface.blit(particle_surface, (x-size, y-size))

    elif level == LEVEL_CROSTA:
        # Cristalli e minerali - VERSIONE STABILE
        time_seed = int(pygame.time.get_ticks() / 2000) % 1000  # Cambia ogni 2 secondi
        offset_seed = int(world_offset / 150) % 100
        
        for i in range(8):
            crystal_seed = (time_seed + offset_seed + i * 31) % 1000
            x = (crystal_seed % WIDTH)
            y = ((crystal_seed + 300) % HEIGHT)

            # Cristallo brillante
            points = []
            for j in range(6):
                angle = j * math.pi / 3
                radius = 3 + (crystal_seed % 6)  # 3-8
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))

            colors = [(100, 200, 255), (200, 255, 100), (255, 200, 100)]
            color = colors[crystal_seed % len(colors)]
            pygame.draw.polygon(surface, color, points)

    elif level == LEVEL_VULCANO:
        # Scintille e braci che seguono la forma conica - VERSIONE STABILE
        base_width = WIDTH * 0.85
        crater_width = WIDTH * 0.25
        time_seed = int(pygame.time.get_ticks() / 800) % 1000  # Cambia ogni 800ms
        offset_seed = int(world_offset / 200) % 100
        
        for i in range(20):
            spark_seed = (time_seed + offset_seed + i * 19) % 1000
            # Calcola posizione Y deterministica
            y = (spark_seed % HEIGHT)
            height_ratio = (HEIGHT - y) / HEIGHT  # 0 = basso, 1 = alto
            
            # Calcola larghezza del passaggio a questa altezza
            current_width = base_width - (base_width - crater_width) * height_ratio
            passage_left = (WIDTH - current_width) / 2
            passage_right = WIDTH - passage_left
            
            # Posiziona scintille nel passaggio o vicino alle pareti - VERSIONE STABILE
            placement_choice = (spark_seed + 100) % 100
            if placement_choice < 70:  # 70% nel passaggio
                # Scintille nel passaggio
                x_range = int(passage_right - passage_left)
                if x_range > 0:
                    x = int(passage_left) + ((spark_seed + 200) % x_range)
                else:
                    x = WIDTH // 2  # Fallback al centro
            else:
                # Scintille sulle pareti - VERSIONE STABILE
                wall_positions = [
                    max(0, int(passage_left - 20)),  # Parete sinistra
                    min(WIDTH, int(passage_right + 20))  # Parete destra
                ]
                x = wall_positions[(spark_seed + 300) % 2]
                x = max(0, min(WIDTH, x))
            
            size = 1 + (spark_seed % 4)  # 1-4
            spark_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            
            # Colore più intenso verso l'alto (più vicino al cratere)
            intensity = 0.5 + height_ratio * 0.5
            color = (255, int(255 * intensity), random.randint(0, int(100 * intensity)), 
                    random.randint(100, 255))
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
        # Effetto di ingresso nel vulcano conico con crepe che si allargano
        num_cracks = int(15 * progress)
        
        # Calcola la larghezza del passaggio durante la transizione
        base_width = WIDTH * 0.85
        current_width = WIDTH * (0.9 - 0.1 * progress)  # Si restringe durante la transizione
        passage_left = (WIDTH - current_width) / 2
        passage_right = WIDTH - passage_left
        
        for i in range(num_cracks):
            # Crepe che si formano lungo le pareti del vulcano
            if i % 2 == 0:
                start_x = random.randint(int(passage_left - 30), int(passage_left + 10))
            else:
                start_x = random.randint(int(passage_right - 10), int(passage_right + 30))
                
            start_y = random.randint(0, HEIGHT)
            
            # Crea una crepa che si illumina e pulsa
            crack_points = [(start_x, start_y)]
            for j in range(random.randint(3, 8)):
                x = crack_points[-1][0] + random.randint(-15, 15)
                y = crack_points[-1][1] + random.randint(-15, 15)
                x = max(0, min(WIDTH, x))  # Mantieni dentro i bordi
                crack_points.append((x, y))
            
            # Disegna la crepa con bagliore intenso
            if len(crack_points) > 1:
                pulse = math.sin(pygame.time.get_ticks() * 0.005 + i) * 0.3 + 0.7
                glow_intensity = progress * pulse
                glow_color = (255, int(150 * glow_intensity), 0)
                crack_color = (255, int(200 * glow_intensity), int(50 * glow_intensity))
                
                # Bagliore esterno
                for k in range(len(crack_points) - 1):
                    pygame.draw.line(screen, glow_color, crack_points[k], crack_points[k+1], 
                                   int(5 * glow_intensity))
                
                # Linea principale della crepa
                for k in range(len(crack_points) - 1):
                    pygame.draw.line(screen, crack_color, crack_points[k], crack_points[k+1], 2)
        
        # Effetto di restringimento delle pareti con particelle
        num_particles = int(30 * progress)
        for _ in range(num_particles):
            # Particelle di roccia che cadono dalle pareti che si restringono
            x = random.choice([
                random.randint(int(passage_left - 20), int(passage_left)),
                random.randint(int(passage_right), int(passage_right + 20))
            ])
            y = random.randint(0, HEIGHT)
            
            size = random.randint(2, 6)
            rock_color = (100 + random.randint(-20, 20), 
                         50 + random.randint(-10, 10), 
                         20 + random.randint(-5, 5))
            
            pygame.draw.circle(screen, rock_color, (x, y), size)
            # Piccola scia di polvere
            trail_color = tuple(min(255, c + 50) for c in rock_color)
            pygame.draw.circle(screen, trail_color, (x, y - 3), size // 2)

def draw_volcano_section(alpha, world_offset, km_height):
    # Sezione vulcano con pareti coniche e effetti
    screen.fill((20, 10, 5))  # Sfondo scuro vulcanico
    
    # Disegna le pareti coniche del vulcano
    draw_conical_volcano_walls(world_offset, km_height)
    
    # Effetti di eruzione se vicini al cratere
    if km_height > KM_PER_LEVEL[LEVEL_VULCANO] * 0.9:
        crater_info = get_crater_info_from_static_map(world_offset)
        draw_eruption_effects(crater_info, km_height)

def draw_conical_volcano_walls(world_offset, km_height):
    """Disegna pareti coniche del vulcano che si restringono verso l'alto - VERSIONE STABILE"""
    # Prima riempie tutto lo schermo con il cielo esterno
    draw_external_sky_background()
    
    # Calcola la progressione nel vulcano (0 = base, 1 = cratere)
    volcano_start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    volcano_end_km = KM_PER_LEVEL[LEVEL_VULCANO]
    volcano_progress = (km_height - volcano_start_km) / (volcano_end_km - volcano_start_km)
    volcano_progress = max(0, min(1, volcano_progress))
    
    # Parametri per la forma conica - ANGOLO PIÙ STRETTO
    base_width = WIDTH * 0.65      # Larghezza alla base (65% dello schermo)
    crater_width = WIDTH * 0.15    # Larghezza al cratere (15% dello schermo)
    
    # Numero di sezioni per disegnare il cono
    num_segments = HEIGHT // 4
    
    for i in range(num_segments):
        # Altezza relativa di questa sezione (0 = basso, 1 = alto)
        # AGGIUNGI LA PROGRESSIONE DEL GIOCATORE per far variare la larghezza
        segment_height = (i / num_segments) + volcano_progress * 0.3  # Effetto dinamico
        segment_height = min(1, segment_height)  # Non superare 1
        
        y = HEIGHT - (i + 1) * 4
        
        # Calcola la larghezza del passaggio a questa altezza
        current_passage_width = base_width - (base_width - crater_width) * segment_height
        
        # Posizioni delle pareti - il cono è al CENTRO dello schermo
        passage_left = (WIDTH - current_passage_width) / 2
        passage_right = WIDTH - passage_left
        
        # Colori per l'interno del vulcano (scuro e roccioso)
        heat_factor = segment_height * 0.7  # Più caldo verso l'alto
        base_rock_color = (40, 20, 15)  # Marrone scuro per l'interno
        
        if heat_factor > 0.4:
            # Roccia riscaldata verso rosso/arancione
            r = min(180, base_rock_color[0] + int(heat_factor * 140))
            g = max(15, base_rock_color[1] + int(heat_factor * 60))
            b = max(10, base_rock_color[2] + int(heat_factor * 25))
            interior_color = (r, g, b)
        else:
            interior_color = base_rock_color
        
        # Colore delle pareti rocciose (più chiaro)
        wall_color = tuple(min(255, int(c * 2.5)) for c in interior_color)
        shadow_color = tuple(max(0, int(c * 0.6)) for c in wall_color)
        
        # RIEMPIE L'INTERNO DEL CONO con colore scuro
        if current_passage_width > 0:
            interior_rect = pygame.Rect(passage_left, y, current_passage_width, 4)
            pygame.draw.rect(screen, interior_color, interior_rect)
        
        # Disegna i bordi delle pareti del cono (spessore delle pareti)
        wall_thickness = 8
        
        # Parete sinistra
        if passage_left > wall_thickness:
            # Superficie esterna della parete (illuminata)
            pygame.draw.line(screen, wall_color, 
                           (passage_left - wall_thickness, y), (passage_left, y), wall_thickness)
            # Bordo interno (più scuro)
            pygame.draw.line(screen, shadow_color, 
                           (passage_left - 1, y), (passage_left, y), 2)
        
        # Parete destra
        if passage_right < WIDTH - wall_thickness:
            # Superficie esterna della parete (illuminata)
            pygame.draw.line(screen, wall_color,
                           (passage_right, y), (passage_right + wall_thickness, y), wall_thickness)
            # Bordo interno (più scuro)
            pygame.draw.line(screen, shadow_color,
                           (passage_right, y), (passage_right + 1, y), 2)
        
        # Aggiungi texture rocciosa FISSA (non casuale) sulle pareti
        # Usa coordinate per pattern deterministico
        if ((i + int(world_offset / 100)) % 13) == 0:  # Pattern fisso ogni 13 segmenti
            # Crepe e irregolarità sulle pareti - POSIZIONI FISSE
            crack_seed = i % 3  # Pattern ripetitivo ogni 3
            
            # Parete sinistra
            if passage_left > wall_thickness:
                crack_x = int(passage_left - wall_thickness + (crack_seed * 3))
                crack_y = y
                crack_size = 1 + (crack_seed % 2)
                crack_color = tuple(max(0, int(c * 0.7)) for c in wall_color)
                pygame.draw.circle(screen, crack_color, (crack_x, crack_y), crack_size)
            
            # Parete destra
            if passage_right < WIDTH - wall_thickness:
                crack_x = int(passage_right + crack_seed * 2)
                crack_y = y
                crack_color = tuple(max(0, int(c * 0.7)) for c in wall_color)
                pygame.draw.circle(screen, crack_color, (crack_x, crack_y), crack_size)
        
        # Bagliore di lava nell'interno nelle zone calde (parte alta) - FISSO
        if segment_height > 0.8 and ((i + int(world_offset / 50)) % 20) == 0:
            glow_intensity = (segment_height - 0.8) / 0.2  # 0 a 1
            glow_color = (255, int(80 + glow_intensity * 120), 0, int(40 * glow_intensity))
            glow_surface = pygame.Surface((int(current_passage_width), 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, glow_color, (0, 0, int(current_passage_width), 6))
            screen.blit(glow_surface, (passage_left, y - 3))
    
    # Disegna il cratere in cima (apertura finale)
    crater_top_y = 60  # Posizione Y del cratere
    crater_width_final = WIDTH * 0.15
    crater_left = (WIDTH - crater_width_final) / 2
    crater_right = WIDTH - crater_left
    
    # Bordo del cratere con effetto lava
    crater_rim_color = (120, 60, 30)
    pygame.draw.line(screen, crater_rim_color, (crater_left - 5, crater_top_y), (crater_left, crater_top_y), 8)
    pygame.draw.line(screen, crater_rim_color, (crater_right, crater_top_y), (crater_right + 5, crater_top_y), 8)
    
    # Bagliore interno del cratere
    crater_glow = pygame.Surface((crater_width_final + 20, 40), pygame.SRCALPHA)
    for r in range(20, 0, -3):
        alpha = int(150 * (r / 20))
        glow_color = (255, 100, 0, alpha)
        pygame.draw.ellipse(crater_glow, glow_color, (10 + (20-r), 20 + (20-r)//2, crater_width_final + r*2, r))
    screen.blit(crater_glow, (crater_left - 10, crater_top_y - 10))

def draw_external_sky_background():
    """Disegna il cielo e le montagne sullo sfondo esterno al vulcano"""
    # Gradiente del cielo dal blu al celeste
    for y in range(HEIGHT):
        intensity = y / HEIGHT
        r = int(135 + intensity * 50)   # Da blu scuro a celeste
        g = int(206 + intensity * 40)   # 
        b = int(250)                    # Blu costante
        color = (min(255, r), min(255, g), b)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    # Disegna catena montuosa in lontananza - VERSIONE STABILE
    mountain_points = []
    num_peaks = 8
    for i in range(num_peaks + 1):
        x = (WIDTH * i) / num_peaks
        # Altezza delle montagne variabile - DETERMINISTICA
        base_height = HEIGHT * 0.7
        peak_seed = i * 37  # Seed deterministico per ogni picco
        peak_variation = ((peak_seed % 200) - 80)  # -80 a +120 circa
        y = base_height + math.sin(i * 0.7) * 60 + peak_variation
        mountain_points.append((x, y))
    
    # Aggiungi punti per completare il poligono
    mountain_points.append((WIDTH, HEIGHT))
    mountain_points.append((0, HEIGHT))
    
    # Disegna le montagne con colore più scuro
    mountain_color = (100, 80, 60)  # Marrone montagna
    pygame.draw.polygon(screen, mountain_color, mountain_points)
    
    # Aggiungi dettagli sulle montagne
    mountain_shadow = (80, 60, 40)
    for i in range(len(mountain_points) - 3):
        x1, y1 = mountain_points[i]
        x2, y2 = mountain_points[i + 1]
        # Ombra sui versanti
        if y1 < y2:  # Versante in discesa
            pygame.draw.line(screen, mountain_shadow, (x1, y1), (x2, y2), 3)
    
    # Nuvole sparse
    for _ in range(random.randint(3, 6)):
        cloud_x = random.randint(0, WIDTH)
        cloud_y = random.randint(50, HEIGHT//3)
        cloud_size = random.randint(20, 40)
        cloud_color = (255, 255, 255, 120)
        
        cloud_surface = pygame.Surface((cloud_size * 2, cloud_size), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud_surface, cloud_color, (0, 0, cloud_size * 2, cloud_size))
        screen.blit(cloud_surface, (cloud_x - cloud_size, cloud_y))

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

        # Aggiungi power-ups occasionalmente - VERSIONE STABILE
        platform_seed = int(x + y * 100) % 100  # Seed basato su posizione
        if platform_seed < 15:  # 15% chance deterministico
            powerup_types = ['thermal_boost', 'magma_jump', 'gas_shield', 'volcanic_time']
            powerup_type = powerup_types[platform_seed % len(powerup_types)]
            powerups.append(PowerUp(x + platform_width//2, y - 30, powerup_type))

        # Aggiungi collectibles - VERSIONE STABILE
        if (platform_seed + 37) % 100 < 30:  # 30% chance deterministico
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
            screen.fill((0,0,0))
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
                        pygame.draw.rect(screen, color, rect)
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
                        pygame.draw.rect(screen, (139, 69, 19), rect, 2)  # Solo bordo

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

            # Draw player: durante eruzione, transizione graduale da goccia a fontana
            if not eruption_mode:
                player.draw_trail(screen)
                player.draw_particles(screen)
                player.draw_wobbly(screen, t_global)
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
                        screen.blit(fade_surface, (0, 0))

            # Draw HUD
            draw_hud()

            if game_state == GAME_OVER:
                draw_game_over()

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