import pygame
from constants import *
from audio_manager import AudioManager
from save_system import load_scores, save_score
from level_volcano import generate_volcano_platforms, draw_volcano_level
#from eruption_effects import draw_eruption_effects

# Qui andra' il loop principale, gestione stati, input, rendering, import di tutti i moduli

def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Volcano Jump - Enhanced Edition")
    clock = pygame.time.Clock()
    # Inizializza font DOPO pygame.init()
    FONT = pygame.font.SysFont("Arial", 20)
    TITLE_FONT = pygame.font.SysFont("Arial", 36, bold=True)
    SMALL_FONT = pygame.font.SysFont("Arial", 16)
    running = True
    audio = AudioManager()
    # Esempio di uso delle funzioni modulari
    platforms, platform_types, powerups, collectibles, enemies = generate_volcano_platforms()
    world_offset = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # ...gestione input, update, collisioni, ecc...
        draw_volcano_level(screen, platforms, world_offset)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
