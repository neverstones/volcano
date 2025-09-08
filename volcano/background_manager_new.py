import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

class BackgroundManager:
    def __init__(self):
        # Percorsi immagini dei livelli principali
        self.level_images = [
            "assets/RoundedBlocks/lava.png",      
            "assets/RoundedBlocks/stoneWall.png", 
            "assets/RoundedBlocks/groundAndGrass.png"  # Sincronizzato con levels.py
        ]

        self.tiles_per_level = 3  # quante "finestre" per livello
        self.layers = []          # struttura: layers[level][tile_index]
        self.tile_offsets = []    # offset verticale di ciascun tile
        self.current_index = 0    # indice livello corrente

        # Carica e scala le immagini
        for img_path in self.level_images:
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.layers.append([img.copy() for _ in range(self.tiles_per_level)])
            self.tile_offsets.append([i * SCREEN_HEIGHT for i in range(self.tiles_per_level)])

        # Tile per i muri vulcanici
        wall_img = pygame.image.load("assets/RoundedBlocks/stoneWall.png").convert_alpha()
        self.wall_tile = pygame.transform.scale(wall_img, (32, 32))

        # Parametri per il cono vulcanico (solo nel livello 2 - Vulcano)
        self.volcano_level_index = 2  # Livello vulcano
        self.cone_walls = []  # Lista delle pareti del cono per ogni tile
        self.setup_volcano_cone()
        
    def setup_volcano_cone(self):
        """Configura la forma del cono vulcanico per i 3 tile del livello vulcano."""
        self.cone_walls = []
        
        # Parametri del cono - forma a imbuto che si restringe verso l'alto
        base_width = SCREEN_WIDTH  # Larghezza alla base (nessuna parete)
        crater_width = 120  # Larghezza del cratere in cima
        tiles_count = self.tiles_per_level  # 3 tile
        
        # Calcola la larghezza delle pareti per ogni tile
        for tile_idx in range(tiles_count):
            # Progressione dal fondo (tile 0) alla cima (tile 2)
            progress = tile_idx / (tiles_count - 1) if tiles_count > 1 else 0
            
            # Larghezza del passaggio a questo livello del cono
            passage_width = base_width - (base_width - crater_width) * progress
            wall_thickness = (SCREEN_WIDTH - passage_width) / 2
            
            # Coordinate delle pareti
            left_wall_end = wall_thickness
            right_wall_start = SCREEN_WIDTH - wall_thickness
            
            self.cone_walls.append({
                'left_wall_end': left_wall_end,
                'right_wall_start': right_wall_start,
                'passage_width': passage_width,
                'wall_thickness': wall_thickness
            })

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

    def draw(self, screen):
        """Disegna tutti i tile del livello corrente e le pareti del cono vulcanico se necessario."""
        idx = int(self.current_index)
        
        # Tile principali di background
        for offset in self.tile_offsets[idx]:
            screen.blit(self.layers[idx][0], (0, offset))

        # Disegna le pareti del cono vulcanico solo nel livello vulcano
        if idx == self.volcano_level_index:
            self.draw_volcano_cone(screen)

    def draw_volcano_cone(self, screen):
        """Disegna le pareti del cono vulcanico con forma che si restringe."""
        tile_w, tile_h = self.wall_tile.get_size()
        
        for tile_idx, offset in enumerate(self.tile_offsets[self.volcano_level_index]):
            if tile_idx < len(self.cone_walls):
                cone_data = self.cone_walls[tile_idx]
                left_wall_end = cone_data['left_wall_end']
                right_wall_start = cone_data['right_wall_start']
                
                # Disegna parete sinistra
                for y in range(offset, offset + SCREEN_HEIGHT, tile_h):
                    if y >= -tile_h and y < SCREEN_HEIGHT + tile_h:  # Solo se visibile
                        for x in range(0, int(left_wall_end), tile_w):
                            screen.blit(self.wall_tile, (x, y))
                
                # Disegna parete destra
                for y in range(offset, offset + SCREEN_HEIGHT, tile_h):
                    if y >= -tile_h and y < SCREEN_HEIGHT + tile_h:  # Solo se visibile
                        for x in range(int(right_wall_start), SCREEN_WIDTH, tile_w):
                            screen.blit(self.wall_tile, (x, y))

    def get_volcano_walls_at_y(self, y_position):
        """Restituisce le coordinate delle pareti del vulcano alla posizione Y specificata."""
        if self.current_index != self.volcano_level_index:
            return None
        
        # Calcola quale tile stiamo guardando basandosi sulla posizione Y
        for tile_idx, offset in enumerate(self.tile_offsets[self.volcano_level_index]):
            if offset <= y_position < offset + SCREEN_HEIGHT:
                if tile_idx < len(self.cone_walls):
                    return self.cone_walls[tile_idx]
        return None

    def check_volcano_collision(self, player):
        """Controlla e gestisce le collisioni del player con le pareti del vulcano."""
        if self.current_index != self.volcano_level_index:
            return False
        
        walls = self.get_volcano_walls_at_y(player.y)
        if walls is None:
            return False
        
        player_left = player.x - player.radius
        player_right = player.x + player.radius
        
        collision = False
        
        # Collisione con parete sinistra
        if player_left < walls['left_wall_end']:
            player.x = walls['left_wall_end'] + player.radius
            player.vx = abs(player.vx) * 0.8  # Rimbalzo attenuato
            collision = True
        
        # Collisione con parete destra
        elif player_right > walls['right_wall_start']:
            player.x = walls['right_wall_start'] - player.radius
            player.vx = -abs(player.vx) * 0.8  # Rimbalzo attenuato
            collision = True
        
        return collision

    def reset(self):
        """Torna al livello iniziale e azzera offset."""
        self.current_index = 0
        for i in range(len(self.tile_offsets)):
            self.tile_offsets[i] = [j * SCREEN_HEIGHT for j in range(self.tiles_per_level)]
