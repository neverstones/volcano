"""
Constants used throughout the volcano game.
"""
import pygame


#Game time
GAME_TIME = 120

# Screen dimensions
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 800
FPS = 60
GRAVITY = 0.98

# Game States
MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3
SCORE_LIST = 4
ENTER_NAME = 5

#LIMITI AREA DI AZIONE (Xmin, Xmax, Ymax)
ACTIONS_AREA_LEFT = 50
ACTION_AREA_RIGHT = SCREEN_WIDTH - 50

LEVEL_HEIGHT = 2000

# Dimensioni piattaforme
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 15
PLAYER_RADIUS = 32


LEVELS = [
    {"name": "Mantle", "bg": "assets/roundedblocks/lava.png"},
    {"name": "Crust", "bg": "assets/roundedblocks/stoneWall.png"},
    {"name": "Volcano", "bg": "assets/roundedblocks/groundAndGrass.png"},
]

# Debug flags
ENABLE_VOLCANO_DEBUG = False
ENABLE_INPUT_DEBUG = False
ENABLE_COLLISION_DEBUG = False
SHOW_CRATER_DEBUG = False

# Physics constants
GRAVITY = 0.25
TERMINAL_VELOCITY = 6.0
JUMP_FORCE = -5.0
SIDE_SPEED = 2.5
FRICTION = 0.8
VOLCANO_THRESHOLD = 29.8
VOLCANO_EXIT_THRESHOLD = 29.3

# Game mechanics
SCROLL_THRESHOLD = 12.0
SCROLL_SPEED = 0.3
MAX_SCROLL_SPEED = 5.0

# Level definitions
LEVEL_MANTELLO = 0
LEVEL_CROSTA = 1  
LEVEL_VULCANO = 2

KM_PER_LEVEL = [15.0, 30.0, 40.0]

# Level colors
LEVEL_COLORS = {
    LEVEL_MANTELLO: (255, 140, 0),    # Orange
    LEVEL_CROSTA: (139, 69, 19),      # Brown
    LEVEL_VULCANO: (255, 0, 0)        # Red
}

# Platform configurations
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 20
PLATFORM_GAP_MIN = 80
PLATFORM_GAP_MAX = 150

# Tile system
TILE_SIZE = 32

# Conversion factors
PIXEL_PER_KM = 50

# Power-up configurations
POWERUP_LIFETIME = 10000  # milliseconds
POWERUP_SPAWN_CHANCE = 0.1

# Collectible configurations
COLLECTIBLE_SPAWN_CHANCE = 0.15
COLLECTIBLE_POINTS = 10

# Enemy configurations
ENEMY_SPAWN_CHANCE = 0.08
ENEMY_SPEED = 1.0

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Sky colors for different altitudes
SKY_COLORS = {
    0: (135, 206, 235),     # Sky blue at ground level
    10: (70, 130, 180),     # Steel blue
    20: (25, 25, 112),      # Midnight blue
    30: (0, 0, 0),          # Black space
    40: (0, 0, 0)           # Black space
}

# UI Constants
FONT_LARGE = 48
FONT_MEDIUM = 24
FONT_SMALL = 18

# Audio settings
AUDIO_FREQUENCY = 22050
AUDIO_BUFFER = 512

# Save file
SAVE_FILE = "volcano_scores.json"
