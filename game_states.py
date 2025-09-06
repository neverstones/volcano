"""
Game states management for the volcano game.
"""
from constants import *

# -------------------------------
# Game state globals
# -------------------------------
game_state = MENU
player_name = ""
high_scores = []

# Fountain/eruption globals
fountain_start_time = 0
fountain_particles = []
victory_achieved = False

# -------------------------------
# Utility: stati → nome
# -------------------------------
STATE_NAMES = {
    MENU: "MENU",
    PLAYING: "PLAYING",
    PAUSED: "PAUSED",
    GAME_OVER: "GAME_OVER",
    SCORE_LIST: "SCORE_LIST",
    ENTER_NAME: "ENTER_NAME"
}

def state_to_name(value: int) -> str:
    """Convert state value to name for debugging."""
    return STATE_NAMES.get(value, str(value))
