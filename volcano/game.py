import pygame
from . import constants
from .player import WobblyBall
from .levels import generate_platforms
from .game_states import run_game_loop

def run():
    """Avvia il gioco."""
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption("Volcano Jump")

    # Crea la finestra
    screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))

    # Avvia il game loop
    run_game_loop(screen)

    pygame.quit()
