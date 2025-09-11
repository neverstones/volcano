"""
Game states and global variables for the volcano game.
"""
from constants import *

# Global game state variables
game_state = MENU
player_name = ""
high_scores = []

# Fountain effect variables
fountain_start_time = 0
fountain_particles = []
victory_achieved = False

def _state_to_name(value):
    """Convert state value to name for debugging."""
    return {
        0: "MENU",
        1: "PLAYING",
        2: "PAUSED",
        3: "GAME_OVER",
        4: "SCORE_LIST",
        5: "ENTER_NAME"
    }.get(value, str(value))
