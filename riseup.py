import pygame, random, math, sys, json, os
import logging
from datetime import datetime

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    print("Audio not available, running without sound")
    pygame.mixer = None

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

# ----------------- Volcano Top + Sky -----------------
CRATER_Y = 100  # altezza del cratere
eruption = False
particles = []

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
            surface.blit(sparkle_surface, (x-size, y-size))

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

        # livello in base all'altezza
        height_km = abs(start_y - current_y) / PIXEL_PER_KM
        if height_km <= KM_PER_LEVEL[LEVEL_MANTELLO]:
            level = LEVEL_MANTELLO
        elif height_km <= KM_PER_LEVEL[LEVEL_CROSTA]:
            level = LEVEL_CROSTA
        else:
            level = LEVEL_VULCANO

        add_platform(x, current_y, level)

    log_debug(f"Generate {len(platforms)} piattaforme, {len(powerups)} power-ups, {len(collectibles)} collectibles, {len(enemies)} nemici")
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
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    screen.blit(overlay, (0, 0))

    game_over_text = TITLE_FONT.render("GAME OVER", True, (255, 0, 0))
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))

    final_score_text = FONT.render(f"Punteggio Finale: {score}", True, (255, 255, 255))
    screen.blit(final_score_text, (WIDTH//2 - final_score_text.get_width()//2, HEIGHT//2 - 50))

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
                    log_debug(f"Collisione con piattaforma {i} - Tipo: {platform_types[i]} - plat_top(screen)={plat_rect.top:.1f}")
                    return True, i

    return False, None

def reset_game():
    global player, world_offset, score, GAME_OVER, tiles_revealed, platforms, platform_types, current_level
    global powerups, collectibles, enemies

    platforms, platform_types, powerups, collectibles, enemies = create_static_platforms()

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

    world_offset = 0
    score = 0
    GAME_OVER = False
    tiles_revealed = 1
    current_level = LEVEL_MANTELLO

    log_debug(f"Gioco resettato - Player posizionato a x={player.x}, y={player.y}")

# ----------------- Main Game Loop -----------------
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
    global game_state, player_name, high_scores

    menu_selected = 0
    running = True

    while running:
        dt = clock.tick(60)/1000.0
        t_global += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if ev.key == pygame.K_UP:
                        menu_selected = (menu_selected - 1) % 3
                    elif ev.key == pygame.K_DOWN:
                        menu_selected = (menu_selected + 1) % 3
                    elif ev.key == pygame.K_RETURN:
                        if menu_selected == 0:  # GIOCA
                            game_state = PLAYING
                            reset_game()
                        elif menu_selected == 1:  # CLASSIFICA
                            game_state = LEADERBOARD
                        elif menu_selected == 2:  # ESCI
                            running = False

                elif game_state == PLAYING:
                    if ev.key == pygame.K_SPACE:
                        grounded, idx = check_platform_collision(player, platforms, world_offset)
                        if grounded:
                            player.jump()
                        else:
                            player.vy = -10

                elif game_state == GAME_OVER:
                    if ev.key == pygame.K_r:
                        game_state = PLAYING
                        reset_game()
                    elif ev.key == pygame.K_ESCAPE:
                        game_state = MENU

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

        # Store menu selection for drawing
        draw_menu.selected = menu_selected

        if game_state == PLAYING:
            keys = pygame.key.get_pressed()
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
                            GAME_OVER = True

            # SCROLL
            SCROLL_THRESH = HEIGHT * 0.4
            SCROLL_SPEED = 0.3

            if player.y < SCROLL_THRESH:
                target_dy = SCROLL_THRESH - player.y
                actual_dy = target_dy * SCROLL_SPEED
                max_scroll = 15
                actual_dy = min(max_scroll, actual_dy)

                world_offset += actual_dy
                player.y += actual_dy
                score += int(actual_dy * 0.2)

                km_height = world_offset / PIXEL_PER_KM
                log_debug(f"Scroll - km: {km_height:.2f}, world_offset: {world_offset:.1f}")

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

                if km_height >= KM_PER_LEVEL[LEVEL_VULCANO]:
                    GAME_OVER = True
                    score += 10000
                    audio.play('eruption')

            # Collision with platforms
            grounded, idx = check_platform_collision(player, platforms, world_offset)
            if grounded and player.vy >= 0:
                plat = platforms[idx]
                player.y = plat.top + world_offset - player.radius
                player.jump()

                # Particle effect
                player.particles.extend([
                    [player.x + random.uniform(-20,20),
                     player.y + player.radius,
                     random.uniform(1,3),
                     random.randint(20,30)]
                    for _ in range(5)
                ])

            # Game over condition
            if player.y - player.radius > HEIGHT + 200:
                GAME_OVER = True

            # Check for high score
            if GAME_OVER and score > 0:
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

            # Draw platforms
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

            # Draw power-ups
            for powerup in powerups:
                powerup.draw(screen, world_offset)

            # Draw collectibles
            for collectible in collectibles:
                collectible.draw(screen, world_offset)

            # Draw enemies
            for enemy in enemies:
                enemy.draw(screen, world_offset)

            # Draw player
            player.draw_trail(screen)
            player.draw_particles(screen)
            player.draw_wobbly(screen, t_global)

            # Draw HUD
            draw_hud()

            if game_state == GAME_OVER:
                draw_game_over()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()