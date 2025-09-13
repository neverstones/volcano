import pygame
import math
import random
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from fountain import Fountain


class BackgroundManager:
    def __init__(self):
        # Percorsi immagini dei livelli principali
        self.level_images = [
            "assets/RoundedBlocks/lava.png",      
            "assets/RoundedBlocks/stoneWall.png", 
            "assets/RoundedBlocks/shardRock.png"  # Cambio da groundAndGrass a shardRock per vulcano
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
        
        # Immagine paesaggio esterno per il vulcano (scroll lento)
        self.landscape_bg = pygame.image.load("assets/vector_ambient.png").convert()
        self.landscape_bg = pygame.transform.scale(self.landscape_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.landscape_scroll = 0  # Scroll separato per il paesaggio
        
        # Fontana di lava per il cratere
        self.fountain_active = False
        self.crater_mode = False
        self.fountain = None

        # Parametri per il cono vulcanico (solo nel livello 2 - Vulcano)
        self.volcano_level_index = 2  # Livello vulcano
        self.cone_walls = []  # Lista delle pareti del cono per ogni tile
        
        # Tracking assoluto per il vulcano (non dipende dal riciclaggio tile)
        self.volcano_total_scroll = 0
        
        self.setup_volcano_cone()
        
    def setup_volcano_cone(self):
        """Configura la forma del cono vulcanico per i 3 tile del livello vulcano."""
        self.cone_walls = []
        
        # Parametri del cono - forma di vulcano che si restringe verso l'alto
        base_width = SCREEN_WIDTH  # Larghezza alla base (larga come schermo)
        crater_width = 120  # Larghezza del cratere in cima (stretto)
        tiles_count = self.tiles_per_level  # 3 tile
        total_height = tiles_count * SCREEN_HEIGHT  # Altezza totale del vulcano
        
        # Calcola il tasso di restringimento per pixel (1 pixel per pixel di altezza)
        width_reduction_per_pixel = (base_width - crater_width) / total_height
        
        # Calcola la larghezza delle pareti per ogni tile
        for tile_idx in range(tiles_count):
            # Altezza dall'inizio del vulcano a questo tile
            height_from_base = tile_idx * SCREEN_HEIGHT
            
            # Larghezza del passaggio a questa altezza (si restringe salendo)
            passage_width = base_width - (width_reduction_per_pixel * height_from_base)
            wall_thickness = (SCREEN_WIDTH - passage_width) / 2
            
            # Coordinate delle pareti
            left_wall_end = wall_thickness
            right_wall_start = SCREEN_WIDTH - wall_thickness
            
            self.cone_walls.append({
                'left_wall_end': left_wall_end,
                'right_wall_start': right_wall_start,
                'passage_width': passage_width,
                'wall_thickness': wall_thickness,
                'height_from_base': height_from_base
            })

    def update(self, dy, total_scroll_distance=0):
        """Scroll verticale dei tile e aggiornamento livello."""
        
        # Determina il livello corrente in base alla distanza percorsa
        # Ogni livello è lungo circa 2000 pixel (constants.LEVEL_HEIGHT)
        LEVEL_HEIGHT = 2000
        new_level_index = min(int(total_scroll_distance // LEVEL_HEIGHT), len(self.level_images) - 1)
        
        # Se cambiamo livello, stampa il debug
        if new_level_index != self.current_index:
            level_names = ["Mantello", "Crosta", "Vulcano"]
            old_name = level_names[self.current_index] if self.current_index < len(level_names) else "Sconosciuto"
            new_name = level_names[new_level_index] if new_level_index < len(level_names) else "Sconosciuto"
            print(f"🌍 Cambio livello: {old_name} → {new_name} (scroll: {total_scroll_distance})")
            self.current_index = new_level_index
        
        # Traccia lo scroll assoluto nel vulcano
        if self.current_index == self.volcano_level_index:
            self.volcano_total_scroll += dy
            # Scroll più lento per il paesaggio (1/3 della velocità)
            self.landscape_scroll += dy * 0.33
                
        # Aggiorna offset dei tile del livello corrente
        self.tile_offsets[int(self.current_index)] = [
            offset + dy for offset in self.tile_offsets[int(self.current_index)]
        ]

        # Riporta i tile sopra se escono sotto
        for i, offset in enumerate(self.tile_offsets[int(self.current_index)]):
            if offset >= SCREEN_HEIGHT:
                self.tile_offsets[int(self.current_index)][i] -= self.tiles_per_level * SCREEN_HEIGHT

    def is_crater_mode(self):
        """Restituisce True se siamo in modalità cratere (goccia sostituita dalla fontana)."""
        return self.crater_mode

    def check_crater_reached(self, player_y):
        """Controlla se il player ha raggiunto il cratere e attiva la fontana."""
        if self.current_index != self.volcano_level_index:
            return False
            
        if self.fountain_active:
            return True  # Già attiva
            
        # Calcola se il player è arrivato al cratere (zona dove le pareti finiscono)
        total_height = self.tiles_per_level * SCREEN_HEIGHT
        crater_height = total_height * 0.9  # 90% dell'altezza totale del vulcano
        
        # Il player è al cratere se ha scrollato abbastanza verso l'alto
        player_absolute_height = self.volcano_total_scroll + (SCREEN_HEIGHT - player_y)
        
        if player_absolute_height >= crater_height:
            self.fountain_active = True
            self.crater_mode = True  # Attiva modalità cratere
            print("🌋 CRATERE RAGGIUNTO! Fontana di lava attivata! Goccia sostituita dalla fontana.")
            return True
            
        return False

    def _particle_should_stay(self, particle):
        """Determina se una particella dovrebbe rimanere attiva o essere rimossa."""
        # Se esce dal fondo dello schermo, rimuovila
        if particle.y > SCREEN_HEIGHT + 100:
            return False

        # Se la particella ha un fade_factor troppo basso, rimuovila
        if hasattr(particle, 'fade_factor') and particle.fade_factor <= 0.01:
            return False

        # Se siamo nel vulcano, consenti alle particelle della fontana di atterrare ovunque (nessun limite laterale né centrale)
        if self.current_index == self.volcano_level_index:
            return True
        else:
            # Negli altri livelli, usa margini più ampi
            if particle.x < -200 or particle.x > SCREEN_WIDTH + 200:
                return False
        return True


    def draw(self, screen):
        """Disegna tutti i tile del livello corrente e le pareti del cono vulcanico se necessario."""
        idx = int(self.current_index)
        
        # Nel vulcano, usa un sistema di background composito
        if idx == self.volcano_level_index:
            self.draw_volcano_backgrounds(screen)
            # Fontana centralizzata: aggiorna e disegna se attiva
            if self.fountain_active:
                if self.fountain is None:
                    self.fountain = Fountain(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                self.fountain.emit()
                self.fountain.update()
                self.fountain.draw(screen)
        else:
            # Altri livelli: disegna normalmente
            for offset in self.tile_offsets[idx]:
                screen.blit(self.layers[idx][0], (0, offset))

        # Disegna le pareti del cono vulcanico solo nel livello vulcano
        if idx == self.volcano_level_index:
            self.draw_volcano_cone(screen)

    def draw_volcano_backgrounds(self, screen):
        """Disegna i background del vulcano: vector_ambient esterno e shardRock interno."""
        # Disegna vector_ambient con scroll lento (tile unico)
        landscape_y = int(self.landscape_scroll % SCREEN_HEIGHT)
        screen.blit(self.landscape_bg, (0, landscape_y))
        screen.blit(self.landscape_bg, (0, landscape_y - SCREEN_HEIGHT))  # Tile per continuità
        
        # Poi disegna shardRock solo nell'area interna definita dalle pareti
        # Parametri del cono
        base_width = SCREEN_WIDTH
        crater_width = 120
        total_height = self.tiles_per_level * SCREEN_HEIGHT
        tile_h = 32  # Altezza dei tile delle pareti
        
        if total_height <= 0:
            return
            
        width_reduction_per_pixel = (base_width - crater_width) / total_height
        
        for tile_idx, offset in enumerate(self.tile_offsets[self.volcano_level_index]):
            # Disegna shardRock a strisce per efficienza
            for y in range(offset, offset + SCREEN_HEIGHT, tile_h):
                if y >= -tile_h and y < SCREEN_HEIGHT + tile_h:  # Solo se visibile
                    # Calcola l'altezza assoluta dal fondo del vulcano
                    absolute_height = self.volcano_total_scroll + (SCREEN_HEIGHT - y)
                    absolute_height = max(0, min(absolute_height, total_height))
                    
                    # Calcola la larghezza del passaggio con convergenza al cratere
                    if absolute_height >= total_height * 0.9:  # Ultimi 10% = cratere
                        passage_width = crater_width  # Pareti dritte al cratere
                    else:
                        passage_width = base_width - (width_reduction_per_pixel * absolute_height)
                        passage_width = max(crater_width, min(passage_width, base_width))
                    
                    # Centro dello schermo per simmetria perfetta
                    center = SCREEN_WIDTH / 2
                    half_passage = passage_width / 2
                    
                    left_wall_end = int(center - half_passage)
                    right_wall_start = int(center + half_passage)
                    
                    # Assicura coordinate valide
                    left_wall_end = max(0, left_wall_end)
                    right_wall_start = min(SCREEN_WIDTH, right_wall_start)
                    
                    # Disegna una striscia di shardRock nell'area interna
                    if right_wall_start > left_wall_end:
                        inner_width = right_wall_start - left_wall_end
                        inner_rect = pygame.Rect(left_wall_end, y, inner_width, tile_h)
                        
                        # Crea una superficie temporanea per shardRock
                        if inner_width > 0 and tile_h > 0:
                            source_rect = pygame.Rect(left_wall_end % SCREEN_WIDTH, y % SCREEN_HEIGHT, 
                                                    min(inner_width, SCREEN_WIDTH), min(tile_h, SCREEN_HEIGHT))
                            if source_rect.width > 0 and source_rect.height > 0:
                                try:
                                    inner_surface = self.layers[self.volcano_level_index][0].subsurface(source_rect)
                                    screen.blit(inner_surface, (left_wall_end, y))
                                except:
                                    # Se fallisce subsurface, usa un colore solido
                                    pygame.draw.rect(screen, (100, 100, 100), inner_rect)

    def draw_fountain(self, screen):
        """Disegna la fontana di lava al cratere."""
        # Prima disegna fumo
        for p in self.smoke_particles:
            p.draw(screen)
        # Poi lava in primo piano
        for p in self.lava_particles:
            p.draw(screen)

    def draw_volcano_interior(self, screen):
        """Disegna l'interno del vulcano (shardRock) solo nell'area tra le pareti."""
        # Disegna prima tutto shardRock, poi le pareti copriranno l'esterno
        for offset in self.tile_offsets[self.volcano_level_index]:
            screen.blit(self.layers[self.volcano_level_index][0], (0, offset))

    def draw_volcano_cone(self, screen):
        """Disegna le pareti del cono vulcanico inclinate e simmetriche."""
        tile_w, tile_h = self.wall_tile.get_size()
        
        # Parametri del cono
        base_width = SCREEN_WIDTH  # Largo dove entra la goccia (in basso)
        crater_width = 120  # Stretto al cratere (in cima)
        total_height = self.tiles_per_level * SCREEN_HEIGHT
        crater_height = total_height * 0.9  # 90% dell'altezza = inizio cratere
        
        if total_height <= 0:
            return
            
        width_reduction_per_pixel = (base_width - crater_width) / total_height
        
        for tile_idx, offset in enumerate(self.tile_offsets[self.volcano_level_index]):
            # Disegna le pareti tile per tile per performance migliori
            for y in range(offset, offset + SCREEN_HEIGHT, tile_h):
                if y >= -tile_h and y < SCREEN_HEIGHT + tile_h:  # Solo se visibile
                    # Calcola l'altezza assoluta dal fondo del vulcano
                    # Più si sale (y diminuisce), più il cono si restringe
                    absolute_height = self.volcano_total_scroll + (SCREEN_HEIGHT - y)
                    absolute_height = max(0, min(absolute_height, total_height))
                    # Non disegnare pareti se siamo al cratere (zona dritta)
                    if absolute_height >= crater_height:
                        continue  # Salta questo tile, siamo nel cratere
                    passage_width = base_width - (width_reduction_per_pixel * absolute_height)
                    passage_width = max(crater_width, min(passage_width, base_width))
                    # Centro dello schermo per simmetria perfetta
                    center = SCREEN_WIDTH / 2
                    half_passage = passage_width / 2
                    left_wall_end = int(center - half_passage)
                    right_wall_start = int(center + half_passage)
                    # Disegna parete sinistra (solo 2 tile di spessore)
                    tiles_left = min(2, left_wall_end // tile_w)  # Massimo 2 tile
                    for i in range(tiles_left):
                        x = left_wall_end - (i + 1) * tile_w  # Parte dal bordo interno
                        if x >= 0:  # Solo se dentro lo schermo
                            screen.blit(self.wall_tile, (x, y))
                    # Disegna parete destra (solo 2 tile di spessore, speculare)
                    tiles_right = min(2, (SCREEN_WIDTH - right_wall_start) // tile_w)  # Massimo 2 tile
                    for i in range(tiles_right):
                        x = right_wall_start + i * tile_w  # Parte dal bordo interno
                        if x < SCREEN_WIDTH:  # Solo se dentro lo schermo
                            screen.blit(self.wall_tile, (x, y))
        # Fontana centralizzata: aggiorna e disegna se attiva
        if self.fountain_active:
            if self.fountain is None:
                self.fountain = Fountain(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.fountain.emit()
            self.fountain.update()
            self.fountain.draw(screen)

    def get_volcano_walls_at_y(self, y_position):
        """Restituisce le coordinate delle pareti del vulcano alla posizione Y specificata."""
        if self.current_index != self.volcano_level_index:
            return None
        
        # Parametri del cono (stessi del metodo draw)
        base_width = SCREEN_WIDTH
        crater_width = 120
        total_height = self.tiles_per_level * SCREEN_HEIGHT
        crater_height = total_height * 0.9  # 90% dell'altezza = inizio cratere
        
        if total_height <= 0:
            return None
            
        # Usa l'altezza assoluta dal fondo del vulcano
        absolute_height = self.volcano_total_scroll + (SCREEN_HEIGHT - y_position)
        absolute_height = max(0, min(absolute_height, total_height))
        
        # Se siamo al cratere, non ci sono più pareti
        if absolute_height >= crater_height:
            return None
            
        width_reduction_per_pixel = (base_width - crater_width) / total_height
        
        # Calcola larghezza del passaggio con convergenza al cratere
        passage_width = base_width - (width_reduction_per_pixel * absolute_height)
        passage_width = max(crater_width, min(passage_width, base_width))
        
        # Centro dello schermo per simmetria perfetta
        center = SCREEN_WIDTH / 2
        half_passage = passage_width / 2
        
        left_wall_end = center - half_passage
        right_wall_start = center + half_passage
        
        return {
            'left_wall_end': left_wall_end,
            'right_wall_start': right_wall_start,
            'passage_width': passage_width,
            'wall_thickness': (SCREEN_WIDTH - passage_width) / 2
        }

    def check_volcano_collision(self, player):
        """Controlla e gestisce le collisioni del player con i blocchetti di tile delle pareti del vulcano."""
        if self.current_index != self.volcano_level_index:
            return False
        
        # Usa il metodo get_volcano_walls_at_y per consistenza
        walls = self.get_volcano_walls_at_y(player.y)
        if walls is None:
            return False
        
        tile_w, tile_h = self.wall_tile.get_size()
        
        # Posizione del player
        player_left = player.x - player.radius
        player_right = player.x + player.radius
        
        collision = False
        
        left_wall_end = walls['left_wall_end']
        right_wall_start = walls['right_wall_start']
        
        # Controlla collisione con i tile della parete sinistra (solo 2 tile)
        if player_left < left_wall_end:
            # Trova il bordo esterno della parete sinistra (massimo 2 tile)
            tiles_left = min(2, int(left_wall_end // tile_w))
            wall_outer_edge = left_wall_end - tiles_left * tile_w
            player.x = left_wall_end + player.radius  # Rimbalza sul bordo interno
            player.vx = abs(player.vx) * 0.8  # Rimbalzo attenuato
            collision = True
        
        # Controlla collisione con i tile della parete destra (solo 2 tile, speculare)
        elif player_right > right_wall_start:
            # Trova il bordo esterno della parete destra (massimo 2 tile)
            tiles_right = min(2, int((SCREEN_WIDTH - right_wall_start) // tile_w))
            wall_outer_edge = right_wall_start + tiles_right * tile_w
            player.x = right_wall_start - player.radius  # Rimbalza sul bordo interno
            player.vx = -abs(player.vx) * 0.8  # Rimbalzo attenuato
            collision = True
        
        return collision

    def reset(self):
        """Torna al livello iniziale e azzera offset."""
        self.current_index = 0
        self.volcano_total_scroll = 0  # Reset tracking assoluto vulcano
        self.landscape_scroll = 0  # Reset scroll paesaggio
        self.fountain_active = False  # Reset fontana
        self.crater_mode = False  # Reset modalità cratere
    # Fountain centralizzata: nessuna lista particelle qui
        for i in range(len(self.tile_offsets)):
            self.tile_offsets[i] = [j * SCREEN_HEIGHT for j in range(self.tiles_per_level)]
