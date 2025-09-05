# ----------------- Volcano Level Generation (Deterministico) -----------------
import pygame, random, math, sys, json, os
import logging
from datetime import datetime
WIDTH, HEIGHT = 600, 800

# ----------------- Window -----------------
WIDTH, HEIGHT = 600, 800
screen = None
clock = None
FONT = None
TITLE_FONT = None
SMALL_FONT = None

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