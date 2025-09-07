import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, LEVEL_HEIGHT

# --- Definizione dei livelli ---
# Ogni livello ha un nome e l'immagine di sfondo associata
LEVEL_DEFS = [
    {"name": "Mantello", "bg": "assets/RoundedBlocks/lava.png"},
    {"name": "Crosta", "bg": "assets/RoundedBlocks/stoneWall.png"},
    {"name": "Vulcano", "bg": "assets/RoundedBlocks/groundAndGrass.png"},
]

class LevelManager:
    def __init__(self, level_defs):
        self.level_defs = level_defs
        self.current_index = 0

        # Carica tutte le immagini dei livelli
        self.backgrounds = []
        for level in self.level_defs:
            img = pygame.image.load(level["bg"]).convert_alpha()
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.backgrounds.append(img)

    def update(self, player_y):
        """Aggiorna il livello in base all'altezza del player."""
        level_index = int(abs(player_y) // LEVEL_HEIGHT)
        if level_index < len(self.level_defs):
            self.current_index = level_index
        else:
            self.current_index = len(self.level_defs) - 1

    def get_current_level(self):
        """Ritorna il dizionario del livello attuale."""
        return self.level_defs[self.current_index]

    def get_background(self):
        """Ritorna l'immagine di sfondo del livello attuale."""
        return self.backgrounds[self.current_index]

    def reset(self):
        """Torna al primo livello (Mantello)."""
        self.current_index = 0
