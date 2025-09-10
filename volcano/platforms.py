import pygame, random
from constants import SCREEN_WIDTH, PLATFORM_WIDTH, PLATFORM_HEIGHT, SCREEN_HEIGHT

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w=PLATFORM_WIDTH, h=PLATFORM_HEIGHT, moving=False, breakable=False):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill((100,200,100))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.moving = moving
        self.breakable = breakable
        self.speed = random.choice([-2,2]) if moving else 0
        self.broken = False
        self.width = w  # Salva la larghezza originale

    def update(self):
        if self.moving:
            self.rect.x += self.speed
            if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.speed *= -1

    def draw(self, screen):
        if not self.broken:
            screen.blit(self.image,self.rect.topleft)

class PlatformManager:
    def __init__(self,num_platforms=10):
        self.platforms = []
        self.num_platforms = num_platforms
        # Gap ridotti per compensare il salto più basso
        self.min_gap = 40  # Ridotto da 45
        self.max_gap = 75  # Ridotto da 85
        self.background_manager = None  # Riferimento al background manager
        self.level_manager = None       # Riferimento al level manager
        
    def set_managers(self, background_manager, level_manager):
        """Imposta i riferimenti ai manager per controllare il livello vulcano."""
        self.background_manager = background_manager
        self.level_manager = level_manager
        
    def get_volcano_constraints(self, y_position):
        """Ottiene i vincoli delle pareti del vulcano per una data posizione Y."""
        if (self.background_manager is None or self.level_manager is None or
            self.level_manager.current_index != 2):  # 2 = livello vulcano
            return None
            
        walls = self.background_manager.get_volcano_walls_at_y(y_position)
        if walls is None:
            return None
            
        # Aggiunge un margine di sicurezza dalle pareti
        margin = 20
        return {
            'left_limit': walls['left_wall_end'] + margin,
            'right_limit': walls['right_wall_start'] - margin,
            'available_width': walls['passage_width'] - (margin * 2)
        }

    def generate_initial_platforms(self,player):
        self.platforms=[]
        
        # Controlla se siamo nel vulcano
        volcano_constraints = self.get_volcano_constraints(player.y)
        
        # Crea sempre una piattaforma di partenza sotto il giocatore
        start_platform_x = player.x - PLATFORM_WIDTH // 2
        
        if volcano_constraints:
            # Nel vulcano: usa piattaforme più strette e rispetta i limiti
            platform_width = max(60, min(PLATFORM_WIDTH * 0.7, volcano_constraints['available_width'] * 0.6))
            start_platform_x = max(volcano_constraints['left_limit'], 
                                 min(start_platform_x, volcano_constraints['right_limit'] - platform_width))
        else:
            # Fuori dal vulcano: logica normale
            platform_width = PLATFORM_WIDTH
            start_platform_x = max(50, min(start_platform_x, SCREEN_WIDTH - platform_width - 50))
            
        start_platform_y = player.y + player.radius + 20  # 20 pixel sotto il giocatore
        self.platforms.append(Platform(start_platform_x, start_platform_y, w=platform_width))
        
        # Genera le altre piattaforme con logica Doodle Jump (posizioni casuali)
        current_y = start_platform_y
        
        while current_y > -SCREEN_HEIGHT*3:
            # Calcola la posizione Y della prossima piattaforma
            gap = random.randint(self.min_gap, self.max_gap)
            y = current_y - gap
            
            # Controlla vincoli del vulcano per questa altezza
            volcano_constraints_y = self.get_volcano_constraints(y)
            
            if volcano_constraints_y:
                # Nel vulcano: piattaforme più strette e dentro le pareti
                platform_width = max(60, min(PLATFORM_WIDTH * 0.7, volcano_constraints_y['available_width'] * 0.6))
                x_min = volcano_constraints_y['left_limit']
                x_max = volcano_constraints_y['right_limit'] - platform_width
                
                if x_max > x_min:
                    x = random.randint(int(x_min), int(x_max))
                else:
                    x = int(x_min)  # Se non c'è spazio, usa il minimo
            else:
                # Fuori dal vulcano: logica normale
                platform_width = PLATFORM_WIDTH
                x = random.randint(50, SCREEN_WIDTH - platform_width - 50)
            
            self.platforms.append(Platform(x, y, w=platform_width))
            current_y = y

    def update(self,dy):
        # Rimuovi piattaforme che sono uscite dallo schermo
        initial_count = len(self.platforms)
        removed_platforms = 0
        for plat in list(self.platforms):
            plat.rect.y += dy
            plat.update()
            if plat.rect.top > SCREEN_HEIGHT:
                self.platforms.remove(plat)
                removed_platforms += 1
        
        # Genera nuove piattaforme se necessario
        added_platforms = 0
        while len(self.platforms) < self.num_platforms:
            if not self.platforms:
                # Se non ci sono piattaforme, crea una piattaforma centrale
                x = SCREEN_WIDTH // 2 - PLATFORM_WIDTH // 2
                y = -SCREEN_HEIGHT
                platform_width = PLATFORM_WIDTH
            else:
                highest_y = min(p.rect.y for p in self.platforms)
                gap = random.randint(self.min_gap, self.max_gap)
                y = highest_y - gap
                
                # Controlla vincoli del vulcano per questa altezza
                volcano_constraints_y = self.get_volcano_constraints(y)
                
                if volcano_constraints_y:
                    # Nel vulcano: piattaforme più strette e dentro le pareti
                    platform_width = max(60, min(PLATFORM_WIDTH * 0.7, volcano_constraints_y['available_width'] * 0.6))
                    x_min = volcano_constraints_y['left_limit']
                    x_max = volcano_constraints_y['right_limit'] - platform_width
                    
                    if x_max > x_min:
                        x = random.randint(int(x_min), int(x_max))
                    else:
                        x = int(x_min)  # Se non c'è spazio, usa il minimo
                else:
                    # Fuori dal vulcano: logica normale
                    platform_width = PLATFORM_WIDTH
                    
                    # Controllo sicurezza: se non ci sono piattaforme raggiungibili nelle ultime 3,
                    # genera una piattaforma raggiungibile
                    recent_platforms = [p for p in self.platforms if p.rect.y > highest_y + self.max_gap * 2]
                    needs_reachable_platform = len(recent_platforms) < 1
                    
                    if needs_reachable_platform and len(self.platforms) > 1:
                        # Trova una posizione raggiungibile dal centro dello schermo
                        center_x = SCREEN_WIDTH // 2
                        max_reach = 200  # Distanza massima raggiungibile
                        x_start = max(50, center_x - max_reach)
                        x_end = min(SCREEN_WIDTH - platform_width - 50, center_x + max_reach)
                        x = random.randint(x_start, x_end)
                    else:
                        # Posizione completamente casuale (stile Doodle Jump)
                        x = random.randint(50, SCREEN_WIDTH - platform_width - 50)
            
            # Aggiungi la nuova piattaforma
            new_platform = Platform(x, y, w=platform_width, moving=random.random()<0.2, breakable=random.random()<0.1)
            self.platforms.append(new_platform)
            added_platforms += 1        # Debug: stampa informazioni solo se ci sono stati cambiamenti significativi
        if removed_platforms > 2 or added_platforms > 2:
            highest_y = min(p.rect.y for p in self.platforms) if self.platforms else "N/A"
            print(f"Platforms: removed={removed_platforms}, added={added_platforms}, total={len(self.platforms)}, highest_y={highest_y}")

    def check_collision(self,player):
        player.on_ground = False  # Reset dello stato a terra
        
        for p in self.platforms:
            if not p.broken and player.get_rect().colliderect(p.rect):
                # Calcola la sovrapposizione
                player_bottom = player.y + player.radius
                player_top = player.y - player.radius
                player_left = player.x - player.radius
                player_right = player.x + player.radius
                
                platform_top = p.rect.top
                platform_bottom = p.rect.bottom
                platform_left = p.rect.left
                platform_right = p.rect.right
                
                # Controlla se il player sta atterrando sulla piattaforma dall'alto
                if (player.vy >= 0 and  # Player che cade o fermo
                    player_bottom >= platform_top and  # Player sopra la piattaforma
                    player_bottom <= platform_top + 15 and  # Margine di tolleranza
                    player_right > platform_left + 5 and  # Sovrapposizione orizzontale
                    player_left < platform_right - 5):
                    
                    if p.breakable:
                        p.broken = True
                        p.image.fill((150,50,50))
                        player.vy = -player.jump_strength * 0.8  # Salto ridotto su piattaforma rotta
                    else:
                        # Posiziona il player esattamente sulla piattaforma
                        player.y = platform_top - player.radius
                        player.vy = -player.jump_strength
                        player.on_ground = True
                    
                    break  # Esci dal loop una volta trovata una collisione

    def draw(self,screen):
        for p in self.platforms:
            p.draw(screen)
