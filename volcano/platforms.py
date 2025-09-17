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
        self.crumbling = False
        self.crumble_timer = None  # None finché non inizia a crollare

    def update(self, volcano_bounds=None):
        if self.moving:
            self.rect.x += self.speed
            # Se sono forniti i limiti del vulcano, usali per il rimbalzo
            if volcano_bounds is not None:
                left, right = volcano_bounds
                if self.rect.left < left:
                    self.rect.left = left
                    self.speed *= -1
                elif self.rect.right > right:
                    self.rect.right = right
                    self.speed *= -1
            else:
                if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                    self.speed *= -1
        # Gestione timer crollo
        if self.crumbling and self.crumble_timer is not None:
            self.crumble_timer -= 1

    def draw(self, screen):
        # Se crollante, cambia colore
        if self.crumbling:
            color = (200, 100, 100) if self.crumble_timer is None else (255, 50, 50)
            self.image.fill(color)
        else:
            self.image.fill((100,200,100))
        screen.blit(self.image, self.rect.topleft)

class PlatformManager:
    def __init__(self,num_platforms=10):
        self.platforms = []
        # Riduci il numero massimo di piattaforme per aumentare la difficoltà
        self.num_platforms = 10
        # Gap ridotti per aumentare la difficoltà
        self.min_gap = 25  # Distanza minima più bassa (più difficile)
        self.max_gap = 55  # Distanza massima più bassa (più difficile)
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
    
    def generate_volcano_platform(self, x, y, level_name, transition_mix=0.0):
        """Genera una piattaforma specifica per il vulcano (più stretta) o normale per altri livelli. transition_mix: 0=vecchio livello, 1=nuovo livello"""
        # Se siamo nella fascia di transizione, genera piattaforme miste
        if 0 < transition_mix < 1:
            if random.random() < transition_mix:
                # Nuovo livello (stile vulcano)
                left_bound, right_bound = self.get_volcano_platform_bounds(y)
                if left_bound is None or right_bound is None:
                    left_bound = 50
                    right_bound = SCREEN_WIDTH - 50
                volcano_width = min(PLATFORM_WIDTH - 15, 50)
                max_x = right_bound - volcano_width
                min_x = left_bound
                if max_x > min_x:
                    x = max(min_x, min(x, max_x))
                    return Platform(x, y, w=volcano_width, moving=random.random()<0.1)
                else:
                    center_x = (left_bound + right_bound) // 2 - volcano_width // 2
                    return Platform(center_x, y, w=volcano_width, moving=False)
            else:
                # Vecchio livello (stile crosta)
                return Platform(x, y, w=PLATFORM_WIDTH, moving=random.random()<0.2)
        elif level_name == "Vulcano":
            left_bound, right_bound = self.get_volcano_platform_bounds(y)
            if left_bound is None or right_bound is None:
                left_bound = 50
                right_bound = SCREEN_WIDTH - 50
            volcano_width = min(PLATFORM_WIDTH - 15, 50)
            max_x = right_bound - volcano_width
            min_x = left_bound
            if max_x > min_x:
                x = max(min_x, min(x, max_x))
                return Platform(x, y, w=volcano_width, moving=random.random()<0.1)
            else:
                center_x = (left_bound + right_bound) // 2 - volcano_width // 2
                return Platform(center_x, y, w=volcano_width, moving=False)
        else:
            return Platform(x, y, w=PLATFORM_WIDTH, moving=random.random()<0.2)

    def generate_initial_platforms(self, player, level_manager=None, depth_multiplier=6):
        # Mantieni le piattaforme della Crosta per una fascia di transizione
        prev_platforms = [p for p in self.platforms if hasattr(p, 'level') and p.level == 'Crosta'] if hasattr(self, 'platforms') else []
        self.platforms = []
        current_level = level_manager.get_current_level()["name"] if level_manager else "Mantello"
        crater_height = None
        if self.background_manager and hasattr(self.background_manager, 'tiles_per_level'):
            total_height = self.background_manager.tiles_per_level * SCREEN_HEIGHT
            crater_height = total_height * 0.9
        start_platform_y = player.y + player.radius + 20
        if current_level == "Vulcano":
            volcano_min_gap = 30
            volcano_max_gap = 55
            left_bound, right_bound = self.get_volcano_platform_bounds(start_platform_y)
            if left_bound is None or right_bound is None:
                start_platform_x = max(50, min(player.x - 20, SCREEN_WIDTH - 40 - 50))
                platform_width = 40
            else:
                passage_width = right_bound - left_bound
                platform_width = min(40, passage_width - 10)
                if passage_width < 40 or platform_width < 25:
                    start_platform_x = int((left_bound + right_bound) // 2 - 20)
                    platform_width = 40
                else:
                    start_platform_x = max(left_bound, min(player.x - platform_width // 2, right_bound - platform_width))
            start_platform = Platform(start_platform_x, start_platform_y, w=platform_width, moving=random.random()<0.1)
            start_platform.crumbling = random.random() < 0.18
            start_platform.level = "Vulcano"
            self.platforms.append(start_platform)
            current_y = start_platform_y
            max_depth = -SCREEN_HEIGHT * 8
            # Mantieni le piattaforme della Crosta per una fascia di 200px sopra il confine
            for p in prev_platforms:
                if p.rect.y > current_y - 200:
                    self.platforms.append(p)
            while current_y > max_depth:
                gap = random.randint(volcano_min_gap, volcano_max_gap)
                y = current_y - gap
                left_bound, right_bound = self.get_volcano_platform_bounds(y)
                if left_bound is None or right_bound is None:
                    break
                passage_width = right_bound - left_bound
                platform_width = min(40, passage_width - 10)
                # Sfasamento orizzontale casuale
                offset = random.randint(-30, 30)
                if passage_width < 40 or platform_width < 25:
                    x = int((left_bound + right_bound) // 2 - 20 + offset)
                    platform_width = 40
                elif passage_width > platform_width + 20:
                    x = random.randint(int(left_bound + 10), int(right_bound - platform_width - 10)) + offset
                else:
                    x = int((left_bound + right_bound) // 2 - platform_width // 2 + offset)
                platform = Platform(x, y, w=platform_width, moving=random.random()<0.1)
                platform.crumbling = random.random() < 0.18
                platform.level = "Vulcano"
                self.platforms.append(platform)
                current_y = y
        else:
            start_platform_x = max(50, min(player.x - PLATFORM_WIDTH // 2, SCREEN_WIDTH - PLATFORM_WIDTH - 50))
            current_level_for_platform = current_level
            start_platform = self.generate_volcano_platform(start_platform_x, start_platform_y, current_level_for_platform)
            self.platforms.append(start_platform)
            current_y = start_platform_y
            max_depth = -SCREEN_HEIGHT * depth_multiplier
            while current_y > max_depth:
                gap = random.randint(self.min_gap, self.max_gap)
                y = current_y - gap
                platform = self.generate_volcano_platform(random.randint(50, SCREEN_WIDTH - PLATFORM_WIDTH - 50), y, current_level)
                self.platforms.append(platform)
                current_y = y

    def update(self, dy, level_manager=None):
        current_level = level_manager.get_current_level()["name"] if level_manager else "Mantello"
        
        # Rimuovi piattaforme che sono uscite dallo schermo
        initial_count = len(self.platforms)
        removed_platforms = 0
        for plat in list(self.platforms):
            plat.rect.y += dy
            # Se siamo nel vulcano e la piattaforma è mobile, passa i limiti delle pareti
            if level_manager and level_manager.get_current_level()["name"] == "Vulcano" and plat.moving:
                left_bound, right_bound = self.get_volcano_platform_bounds(plat.rect.y)
                if left_bound is not None and right_bound is not None:
                    plat.update(volcano_bounds=(int(left_bound), int(right_bound)))
                else:
                    plat.update()
            else:
                plat.update()
            if plat.rect.top > SCREEN_HEIGHT:
                self.platforms.remove(plat)
                removed_platforms += 1
        
        # Genera nuove piattaforme se necessario (on demand, tutti i livelli)
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
                    # Genera piattaforme fino al cratere, ignorando i limiti delle pareti
                    if absolute_height >= crater_height:
                        break
                if current_level == "Vulcano":
                    # Genera piattaforme in stile doodle jump tra le pareti del vulcano
                    left_bound, right_bound = self.get_volcano_platform_bounds(y)
                    if left_bound is None or right_bound is None or right_bound - left_bound < 40:
                        x = SCREEN_WIDTH // 2 - PLATFORM_WIDTH // 2
                    else:
                        x = random.randint(int(left_bound + 5), int(right_bound - PLATFORM_WIDTH - 5))
                    # Probabilità piattaforma crollante
                    is_crumbling = random.random() < 0.18  # 18% di probabilità
                    platform = self.generate_volcano_platform(x, y, current_level)
                    platform.crumbling = is_crumbling
                    self.platforms.append(platform)
                    added_platforms += 1
                    continue
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
                    # Se la piattaforma è crollante, avvia timer crollo
                    if hasattr(p, 'crumbling') and p.crumbling and p.crumble_timer is None:
                        p.crumble_timer = 30  # frame di attesa prima del crollo (~0.5s a 60fps)
                    break  # Esci dal loop una volta trovata una collisione
        # Rimuovi piattaforme crollate
        self.platforms = [plat for plat in self.platforms if not (hasattr(plat, 'crumbling') and plat.crumbling and plat.crumble_timer is not None and plat.crumble_timer <= 0)]

    def draw(self,screen):
        for p in self.platforms:
            p.draw(screen)
