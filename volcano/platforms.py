import pygame, random, math
from constants import SCREEN_WIDTH, PLATFORM_WIDTH, PLATFORM_HEIGHT, SCREEN_HEIGHT

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w=PLATFORM_WIDTH, h=PLATFORM_HEIGHT, moving=False):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill((100,200,100))
        self.rect = self.image.get_rect(topleft=(x,y))
        self.moving = moving
        self.speed = random.choice([-2,2]) if moving else 0

    def update(self):
        if self.moving:
            self.rect.x += self.speed
            if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.speed *= -1

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

class PlatformManager:
    def __init__(self,num_platforms=10):
        self.platforms = []
        self.num_platforms = num_platforms
        # Gap ridotti per compensare il salto più basso
        self.min_gap = 40  # Ridotto da 45
        self.max_gap = 75  # Ridotto da 85
        
        # Riferimento al background manager per ottenere i limiti del vulcano
        self.background_manager = None
        
    def set_background_manager(self, background_manager):
        """Imposta il riferimento al background manager per ottenere i limiti del vulcano."""
        self.background_manager = background_manager
    
    def get_volcano_platform_bounds(self, y_position):
        """Ottiene i limiti per le piattaforme nel vulcano in base alla posizione Y, usando le pareti del background."""
        if self.background_manager:
            wall_data = self.background_manager.get_volcano_walls_at_y(y_position)
            if wall_data:
                margin = 20
                return wall_data['left_wall_end'] + margin, wall_data['right_wall_start'] - margin
            else:
                # Se wall_data è None, siamo oltre il cratere: blocca la generazione
                return None, None
        # Fallback ai limiti standard se non c'è il background manager
        return 50, SCREEN_WIDTH - 50
    
    def generate_volcano_platform(self, x, y, level_name):
        """Genera una piattaforma specifica per il vulcano (più stretta) o normale per altri livelli."""
        if level_name == "Vulcano":
            # Ottieni i limiti delle pareti del vulcano
            left_bound, right_bound = self.get_volcano_platform_bounds(y)
            
            # Piattaforme più strette nel vulcano
            volcano_width = min(PLATFORM_WIDTH - 15, 50)
            
            # Assicurati che la piattaforma rientri nei limiti
            max_x = right_bound - volcano_width
            min_x = left_bound
            
            if max_x > min_x:
                x = max(min_x, min(x, max_x))
                return Platform(x, y, w=volcano_width, moving=random.random()<0.1)
            else:
                # Se lo spazio è troppo stretto, metti al centro
                center_x = (left_bound + right_bound) // 2 - volcano_width // 2
                return Platform(center_x, y, w=volcano_width, moving=False)
        else:
            # Piattaforme normali per altri livelli (Mantello, Crosta)
            return Platform(x, y, w=PLATFORM_WIDTH, moving=random.random()<0.2)

    def generate_initial_platforms(self, player, level_manager=None, depth_multiplier=6):
        self.platforms=[]
        current_level = level_manager.get_current_level()["name"] if level_manager else "Mantello"
        # Recupera il limite del cratere dal background manager se disponibile
        crater_height = None
        if self.background_manager and hasattr(self.background_manager, 'tiles_per_level'):
            total_height = self.background_manager.tiles_per_level * SCREEN_HEIGHT
            crater_height = total_height * 0.9
        # Crea sempre una piattaforma di partenza sotto il giocatore
        start_platform_x = player.x - PLATFORM_WIDTH // 2
        # Adatta i limiti in base al livello
        if current_level == "Vulcano":
            left_bound, right_bound = self.get_volcano_platform_bounds(player.y + player.radius + 20)
            if left_bound is None or right_bound is None:
                return  # Non generare piattaforme oltre il cratere
            passage_width = right_bound - left_bound
            platform_width = min(PLATFORM_WIDTH - 15, 50, passage_width - 10)
            if passage_width < 40 or platform_width < 30:
                return  # Non generare piattaforme se lo spazio è troppo stretto
            start_platform_x = max(left_bound, min(start_platform_x, right_bound - platform_width))
        else:
            start_platform_x = max(50, min(start_platform_x, SCREEN_WIDTH - PLATFORM_WIDTH - 50))
        start_platform_y = player.y + player.radius + 20  # 20 pixel sotto il giocatore
        start_platform = self.generate_volcano_platform(start_platform_x, start_platform_y, current_level)
        self.platforms.append(start_platform)
        # Genera le altre piattaforme con logica Doodle Jump (posizioni casuali)
        current_y = start_platform_y
        # Profondità aumentata per generare più piattaforme in anticipo
        max_depth = -SCREEN_HEIGHT * depth_multiplier
        while current_y > max_depth:
            gap = random.randint(self.min_gap, self.max_gap)
            y = current_y - gap
            # Blocca la generazione oltre il cratere
            if crater_height is not None:
                absolute_height = self.background_manager.volcano_total_scroll + (SCREEN_HEIGHT - y)
                if absolute_height >= crater_height:
                    break
            if current_level == "Vulcano":
                left_bound, right_bound = self.get_volcano_platform_bounds(y)
                if left_bound is None or right_bound is None:
                    break  # Non generare piattaforme oltre il cratere
                passage_width = right_bound - left_bound
                platform_width = min(PLATFORM_WIDTH - 15, 50, passage_width - 10)
                if passage_width < 40 or platform_width < 30:
                    break  # Non generare piattaforme se lo spazio è troppo stretto
                if passage_width > platform_width + 20:
                    x = random.randint(int(left_bound + 10), int(right_bound - platform_width - 10))
                else:
                    x = int((left_bound + right_bound) // 2 - platform_width // 2)
            else:
                x = random.randint(50, SCREEN_WIDTH - PLATFORM_WIDTH - 50)
            platform = self.generate_volcano_platform(x, y, current_level)
            self.platforms.append(platform)
            current_y = y

    def update(self, dy, level_manager=None):
        current_level = level_manager.get_current_level()["name"] if level_manager else "Mantello"
        
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
            else:
                highest_y = min(p.rect.y for p in self.platforms)
                gap = random.randint(self.min_gap, self.max_gap)
                # Controllo sicurezza: se non ci sono piattaforme raggiungibili nelle ultime 3,
                # genera una piattaforma raggiungibile
                recent_platforms = [p for p in self.platforms if p.rect.y > highest_y + self.max_gap * 2]
                needs_reachable_platform = len(recent_platforms) < 1
                y = highest_y - gap
                # Blocca la generazione oltre il cratere anche in update
                crater_height = None
                if self.background_manager and hasattr(self.background_manager, 'tiles_per_level'):
                    total_height = self.background_manager.tiles_per_level * SCREEN_HEIGHT
                    crater_height = total_height * 0.9
                if current_level == "Vulcano" and crater_height is not None:
                    absolute_height = self.background_manager.volcano_total_scroll + (SCREEN_HEIGHT - y)
                    if absolute_height >= crater_height:
                        break
                if current_level == "Vulcano":
                    left_bound, right_bound = self.get_volcano_platform_bounds(y)
                    if left_bound is None or right_bound is None:
                        break
                    passage_width = right_bound - left_bound
                    platform_width = min(PLATFORM_WIDTH - 15, 50, passage_width - 10)
                    if passage_width < 40 or platform_width < 30:
                        break
                    # Cast a int per tutti i parametri
                    left_bound = int(left_bound)
                    right_bound = int(right_bound)
                    platform_width = int(platform_width)
                    if needs_reachable_platform and len(self.platforms) > 1:
                        center_x = int((left_bound + right_bound) // 2)
                        max_reach = int(min(150, (right_bound - left_bound) // 3))
                        x_start = max(int(left_bound + 10), center_x - max_reach)
                        x_end = min(int(right_bound - platform_width - 10), center_x + max_reach)
                        if x_end > x_start:
                            x = random.randint(x_start, x_end)
                        else:
                            x = center_x - platform_width // 2
                    else:
                        if right_bound - left_bound > platform_width + 20:
                            x = random.randint(int(left_bound + 10), int(right_bound - platform_width - 10))
                        else:
                            x = int((left_bound + right_bound) // 2 - platform_width // 2)
                else:
                    if needs_reachable_platform and len(self.platforms) > 1:
                        center_x = SCREEN_WIDTH // 2
                        max_reach = 200
                        x_start = max(50, center_x - max_reach)
                        x_end = min(SCREEN_WIDTH - PLATFORM_WIDTH - 50, center_x + max_reach)
                        x = random.randint(int(x_start), int(x_end))
                    else:
                        x = random.randint(50, SCREEN_WIDTH - PLATFORM_WIDTH - 50)
            new_platform = self.generate_volcano_platform(x, y, current_level)
            self.platforms.append(new_platform)
            added_platforms += 1
            
        # Debug: stampa informazioni solo se ci sono stati cambiamenti significativi
        if removed_platforms > 2 or added_platforms > 2:
            highest_y = min(p.rect.y for p in self.platforms) if self.platforms else "N/A"
            print(f"Platforms: removed={removed_platforms}, added={added_platforms}, total={len(self.platforms)}, highest_y={highest_y}")

    def check_collision(self,player):
        player.on_ground = False  # Reset dello stato a terra
        
        for p in self.platforms:
            if player.get_rect().colliderect(p.rect):
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
                    
                    # Posiziona il player esattamente sulla piattaforma e fallo saltare
                    player.y = platform_top - player.radius
                    player.vy = -player.jump_strength
                    player.on_ground = True
                    
                    break  # Esci dal loop una volta trovata una collisione

    def draw(self,screen):
        for p in self.platforms:
            p.draw(screen)
