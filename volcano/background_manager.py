import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

class BackgroundManager:
    def __init__(self):
        # Carica le immagini dei vari strati
        self.layers = [
            pygame.image.load("assets/RoundedBlocks/lava.png").convert_alpha(),
            pygame.image.load("assets/RoundedBlocks/stone.png").convert_alpha(),
            pygame.image.load("assets/RoundedBlocks/ground.png").convert_alpha()
        ]

        # Ridimensiona ogni layer a grandezza finestra
        self.layers = [pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in self.layers]

        # Indice corrente dello strato
        self.current_index = 0
        self.offset_y = 0  # per lo scroll verticale

    def update(self, dy):
        """Muove il background verso il basso di dy (come le piattaforme)."""
        self.offset_y += dy

        # Se superiamo l’altezza dello schermo, passa allo strato successivo
        if self.offset_y >= SCREEN_HEIGHT:
            self.offset_y = 0
            self.current_index = min(self.current_index + 1, len(self.layers) - 1)

    def draw(self, screen):
        """Disegna lo sfondo attuale (e il successivo per continuità)."""
        current = self.layers[self.current_index]
        screen.blit(current, (0, self.offset_y))

        # Disegna anche lo strato successivo sopra, per continuità nello scroll
        if self.current_index < len(self.layers) - 1:
            next_layer = self.layers[self.current_index + 1]
            screen.blit(next_layer, (0, self.offset_y - SCREEN_HEIGHT))
