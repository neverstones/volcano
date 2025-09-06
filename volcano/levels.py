import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, LEVEL_HEIGHT

class LevelManager:
    def __init__(self, level_defs):
        self.level_defs = level_defs
        self.current_index = 0
        self.backgrounds = [
            pygame.transform.scale(
                pygame.image.load(level["bg"]).convert_alpha(),
                (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            for level in self.level_defs
        ]

    def update(self, player_y):
        # Più il player sale, più cambia livello
        level_index = abs(player_y) // LEVEL_HEIGHT
        if level_index < len(self.level_defs):
            self.current_index = level_index
        else:
            self.current_index = len(self.level_defs) - 1

    def get_background(self):
        return self.backgrounds[self.current_index]
