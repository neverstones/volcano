import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

class BackgroundManager:
    def __init__(self):
        # Percorsi immagini dei livelli principali
        self.level_images = [
            "assets/RoundedBlocks/lava.png",      
            "assets/RoundedBlocks/stoneWall.png", 
            "assets/RoundedBlocks/groundAndGrass.png"
        ]

        self.tiles_per_level = 3  # quante “finestre” per livello
        self.layers = []          # struttura: layers[level][tile_index]
        self.tile_offsets = []    # offset verticale di ciascun tile
        self.current_index = 0    # indice livello corrente

        # Carica e scala le immagini
        for img_path in self.level_images:
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.layers.append([img.copy() for _ in range(self.tiles_per_level)])
            self.tile_offsets.append([i * SCREEN_HEIGHT for i in range(self.tiles_per_level)])

        # Tile per i muri vulcanici nell’ultimo livello
        wall_img = pygame.image.load("assets/RoundedBlocks/stoneWall.png").convert_alpha()
        self.wall_tile = pygame.transform.scale(wall_img, (32, 32))

        # Parametri galleria vulcanica
        self.left_margin = 0
        self.right_margin = SCREEN_WIDTH
        self.volcano_shrink_rate = 0.4  # pixel per frame

    def update(self, dy):
        """Scroll verticale dei tile."""
        # Aggiorna offset dei tile del livello corrente
        self.tile_offsets[int(self.current_index)] = [
            offset + dy for offset in self.tile_offsets[int(self.current_index)]
        ]

        # Riporta i tile sopra se escono sotto
        for i, offset in enumerate(self.tile_offsets[int(self.current_index)]):
            if offset >= SCREEN_HEIGHT:
                self.tile_offsets[int(self.current_index)][i] -= self.tiles_per_level * SCREEN_HEIGHT

        # Galleria vulcanica: restringimento muri nell’ultimo livello
        if int(self.current_index) == len(self.layers) - 1:
            self.left_margin += self.volcano_shrink_rate
            self.right_margin -= self.volcano_shrink_rate
            max_margin = SCREEN_WIDTH // 2 - 40
            self.left_margin = min(self.left_margin, max_margin)
            self.right_margin = max(self.right_margin, SCREEN_WIDTH - max_margin)

    def draw(self, screen):
        """Disegna tutti i tile del livello corrente e i muri se necessario."""
        idx = int(self.current_index)
        # Tile principali
        for offset in self.tile_offsets[idx]:
            screen.blit(self.layers[idx][0], (0, offset))  # usa 0 o stesso tile ripetuto

        # Muri laterali solo nell’ultimo livello
        if idx == len(self.layers) - 1:
            tile_w, tile_h = self.wall_tile.get_size()
            for offset in self.tile_offsets[idx]:
                # Muro sinistro
                y = offset
                while y < offset + SCREEN_HEIGHT:
                    screen.blit(self.wall_tile, (0, y))
                    y += tile_h
                # Muro destro
                y = offset
                while y < offset + SCREEN_HEIGHT:
                    screen.blit(self.wall_tile, (self.right_margin, y))
                    y += tile_h

    def reset(self):
        """Torna al livello iniziale e azzera offset e margini."""
        self.current_index = 0
        self.left_margin = 0
        self.right_margin = SCREEN_WIDTH
        for i in range(len(self.tile_offsets)):
            self.tile_offsets[i] = [j * SCREEN_HEIGHT for j in range(self.tiles_per_level)]
