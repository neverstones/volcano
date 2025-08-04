import pygame
import sys
import random
import math
import json
import os
from datetime import datetime

# Inizializza Pygame
pygame.init()

# Dimensioni schermo
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Magma Riser")

# Clock
clock = pygame.time.Clock()

# Costanti
GRAVITY = -0.01  # Gravità "inversa" molto leggera
FORCE = 0.08     # Forza spinta verso l'alto aumentata
CAMERA_SPEED = 2

# Colori
BLACK = (0, 0, 0)
RED = (255, 80, 0)
DARK_RED = (100, 20, 0)
WHITE = (255, 255, 255)
GREY = (50, 50, 50)

# Stato del gioco
MENU = 0
GIOCO = 1
PAUSA = 2
GAME_OVER = 3
CLASSIFICA = 4
INPUT_NAME = 5  # Nuovo stato per inserimento nome
stato = MENU

# Font
font = pygame.font.SysFont("Arial", 40)
small_font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 60, bold=True)

# Sistema di punteggio e competizione
game_score = 0
game_time = 0
game_start_time = 0
leaderboard = []  # Lista dei record con nome, punteggio, data
player_name = ""
input_active = False
difficulty_level = 1
max_time = 120  # 2 minuti per livello
leaderboard_file = "vulcano_scores.json"

# Variabili menu
menu_options = ["GIOCA", "CLASSIFICA", "ESCI"]
selected_option = 0

# Variabili per modalità competitiva
current_objective = "Raggiungi 5000m"
objectives = [
    (5000, "Raggiungi 5000m", 1000),
    (5500, "Raggiungi 5500m", 1500), 
    (6000, "Eruzione controllata", 2000)
]
objective_index = 0

# Variabili globali per l'eruzione
eruption_active = False
eruption_particles = []
eruption_start_time = 0

# Classe per bolle di gas boost
class GasBubble:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(15, 25)
        self.pulse = random.uniform(0, 2 * math.pi)
        self.boost_power = random.uniform(0.3, 0.6)
        self.collected = False
        self.life = 300  # 5 secondi a 60 FPS
        
    def update(self):
        self.pulse += 0.1
        self.life -= 1
        return self.life > 0
    
    def draw(self, surface, camera_y):
        screen_y = SCREEN_HEIGHT - (self.y - camera_y)
        if 0 <= screen_y <= SCREEN_HEIGHT and 0 <= self.x <= SCREEN_WIDTH:
            # Effetto pulsante
            pulse_factor = abs(math.sin(self.pulse))
            current_size = int(self.size * (0.8 + 0.4 * pulse_factor))
            
            # Alone luminoso
            glow_surface = pygame.Surface((current_size*4, current_size*4), pygame.SRCALPHA)
            glow_color = (100, 200, 255, int(100 * pulse_factor))
            pygame.draw.circle(glow_surface, glow_color, (current_size*2, current_size*2), current_size*2)
            surface.blit(glow_surface, (self.x - current_size*2, screen_y - current_size*2), special_flags=pygame.BLEND_ADD)
            
            # Bolla principale
            bubble_color = (150 + int(50 * pulse_factor), 220 + int(35 * pulse_factor), 255)
            pygame.draw.circle(surface, bubble_color, (int(self.x), int(screen_y)), current_size)
            
            # Riflesso interno
            highlight_size = max(2, current_size // 3)
            pygame.draw.circle(surface, (255, 255, 255), 
                             (int(self.x - current_size//3), int(screen_y - current_size//3)), highlight_size)
    
    def check_collision(self, particle):
        distance = math.hypot(self.x - particle.x, self.y - particle.y)
        return distance < self.size + particle.radius

# Classe per particelle dell'eruzione (lapilli)
class EruptionParticle:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy  # Ora positivo = verso l'alto
        self.life = random.randint(60, 180)
        self.max_life = self.life
        self.size = random.randint(3, 8)  # Lapilli più grandi
        self.color = (255, random.randint(80, 200), random.randint(0, 50))
        self.rotation = random.uniform(0, 2 * math.pi)
        self.angular_velocity = random.uniform(-0.2, 0.2)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy  # movimento verso l'alto (positivo)
        self.vy -= 0.15  # gravità che rallenta e poi inverte
        self.vx *= 0.995  # attrito dell'aria
        self.life -= 1
        self.rotation += self.angular_velocity
        
        # Fade out
        alpha = self.life / self.max_life
        self.color = (
            int(self.color[0] * alpha),
            int(self.color[1] * alpha),
            int(self.color[2] * alpha)
        )
        
        return self.life > 0
    
    def draw(self, surface, camera_y):
        screen_y = SCREEN_HEIGHT - int(self.y - camera_y)
        if 0 <= screen_y <= SCREEN_HEIGHT and 0 <= self.x <= SCREEN_WIDTH:
            # Disegna lapillo rotante
            points = []
            for i in range(6):  # Forma irregolare del lapillo
                angle = self.rotation + i * math.pi / 3
                radius = self.size * (0.7 + 0.3 * math.sin(i))
                px = int(self.x + math.cos(angle) * radius)
                py = int(screen_y + math.sin(angle) * radius)
                points.append((px, py))
            
            if len(points) >= 3:
                pygame.draw.polygon(surface, self.color, points)
                
                # Alone luminoso per lapilli caldi
                if self.life > self.max_life * 0.5:
                    glow_surface = pygame.Surface((self.size*6, self.size*6), pygame.SRCALPHA)
                    glow_color = tuple(list(self.color) + [60])
                    pygame.draw.circle(glow_surface, glow_color, (self.size*3, self.size*3), self.size*2)
                    surface.blit(glow_surface, (self.x - self.size*3, screen_y - self.size*3), special_flags=pygame.BLEND_ADD)

def check_eruption(magma_y):
    """Controlla se il magma ha raggiunto la superficie e inizia l'eruzione"""
    global eruption_active, eruption_start_time, game_score, stato
    
    if magma_y >= 5800 and not eruption_active:  # Superficie raggiunta
        eruption_active = True
        eruption_start_time = pygame.time.get_ticks()
        
        # Punteggio bonus per eruzione
        game_score += 2000
        
        # Crea lapilli iniziali dell'eruzione VERSO L'ALTO
        center_x = SCREEN_WIDTH // 2
        for _ in range(25):
            # Angoli verso l'alto (da -π/6 a -5π/6)
            angle = random.uniform(-math.pi/6, -5*math.pi/6)
            speed = random.uniform(8, 18)
            vx = math.cos(angle) * speed
            vy = abs(math.sin(angle)) * speed  # Assicura movimento verso l'alto
            eruption_particles.append(EruptionParticle(center_x + random.randint(-20, 20), 5800, vx, vy))

def update_eruption():
    """Aggiorna l'eruzione"""
    global eruption_particles, stato
    
    if not eruption_active:
        return
    
    # Aggiorna particelle esistenti
    eruption_particles = [p for p in eruption_particles if p.update()]
    
    # Verifica se l'eruzione è finita per passare alla vittoria
    time_since_start = pygame.time.get_ticks() - eruption_start_time
    
    # Aggiungi nuovi lapilli durante l'eruzione
    if time_since_start < 4000:  # 4 secondi di eruzione attiva
        center_x = SCREEN_WIDTH // 2
        
        # Intensità variabile dell'eruzione
        if time_since_start < 1500:  # Prima fase: eruzione intensa
            for _ in range(3):
                angle = random.uniform(-math.pi/8, -7*math.pi/8)
                speed = random.uniform(12, 22)
                vx = math.cos(angle) * speed
                vy = abs(math.sin(angle)) * speed  # Verso l'alto
                eruption_particles.append(EruptionParticle(
                    center_x + random.randint(-15, 15), 5800, vx, vy))
        
        elif time_since_start < 3000:  # Seconda fase: eruzione media
            for _ in range(2):
                angle = random.uniform(-math.pi/4, -3*math.pi/4)
                speed = random.uniform(8, 16)
                vx = math.cos(angle) * speed
                vy = abs(math.sin(angle)) * speed
                eruption_particles.append(EruptionParticle(
                    center_x + random.randint(-25, 25), 5800, vx, vy))
        
        else:  # Fase finale: eruzione che si attenua
            if random.randint(1, 3) == 1:
                angle = random.uniform(-math.pi/3, -2*math.pi/3)
                speed = random.uniform(5, 12)
                vx = math.cos(angle) * speed
                vy = abs(math.sin(angle)) * speed
                eruption_particles.append(EruptionParticle(
                    center_x + random.randint(-10, 10), 5800, vx, vy))
    
    # Transizione alla vittoria dopo 5 secondi
    elif time_since_start > 5000:
        stato = INPUT_NAME  # Passa all'inserimento nome

def draw_eruption(surface, camera_y):
    """Disegna l'eruzione con effetti spettacolari"""
    if not eruption_active:
        return
    
    center_x = SCREEN_WIDTH // 2
    crater_screen_y = SCREEN_HEIGHT - (5800 - camera_y)
    
    if crater_screen_y > 0:
        # Colonna centrale di lava con effetti multipli
        column_height = min(300, crater_screen_y)
        
        # Alone luminoso della colonna
        glow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(0, column_height, 3):
            width = 40 - int(i * 0.08)
            if width > 0:
                color_intensity = 1 - (i / column_height)
                glow_color = (
                    int(255 * color_intensity),
                    int(100 * color_intensity),
                    int(30 * color_intensity),
                    int(80 * color_intensity)
                )
                pygame.draw.ellipse(glow_surface, glow_color, 
                                  (center_x - width, crater_screen_y - i, width*2, 15))
        
        surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # Colonna principale con gradiente
        for i in range(0, column_height, 2):
            width = 25 - int(i * 0.06)
            if width > 0:
                color_intensity = 1 - (i / column_height)
                
                # Nucleo bianco caldo
                core_width = max(2, width // 3)
                core_color = (255, 255, int(200 + 55 * color_intensity))
                pygame.draw.ellipse(surface, core_color, 
                                  (center_x - core_width//2, crater_screen_y - i, core_width, 8))
                
                # Strato intermedio arancione
                mid_color = (255, int(150 + 105 * color_intensity), int(50 * color_intensity))
                pygame.draw.ellipse(surface, mid_color, 
                                  (center_x - width//2, crater_screen_y - i, width, 12))
        
        # Particelle di scintille attorno alla colonna
        for _ in range(15):
            spark_angle = random.uniform(0, 2 * math.pi)
            spark_dist = random.uniform(30, 80)
            spark_x = center_x + math.cos(spark_angle) * spark_dist
            spark_y = crater_screen_y - random.uniform(0, column_height * 0.7)
            
            spark_color = (255, random.randint(150, 255), random.randint(0, 100))
            spark_size = random.randint(1, 4)
            pygame.draw.circle(surface, spark_color, (int(spark_x), int(spark_y)), spark_size)
    
    # Disegna particelle con effetti migliorati
    for particle in eruption_particles:
        screen_y = SCREEN_HEIGHT - int(particle.y - camera_y)
        if 0 <= screen_y <= SCREEN_HEIGHT and 0 <= particle.x <= SCREEN_WIDTH:
            # Alone luminoso per ogni particella
            glow_size = particle.size * 3
            glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
            
            alpha = int(particle.life / particle.max_life * 100)
            glow_color = tuple(list(particle.color) + [alpha])
            pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
            
            surface.blit(glow_surface, (particle.x - glow_size, screen_y - glow_size), special_flags=pygame.BLEND_ADD)
            
            # Particella principale
            pygame.draw.circle(surface, particle.color, (int(particle.x), screen_y), particle.size)
            
            # Nucleo luminoso
            core_color = tuple([min(255, c + 100) for c in particle.color])
            pygame.draw.circle(surface, core_color, (int(particle.x), screen_y), max(1, particle.size//2))

# Sezioni geologiche e altezze cumulative (in unità arbitrarie)
section_heights = {
    "Mantello": 0,
    "Crosta": 2000,
    "Vulcano": 4000
}



class Faglia:
    def __init__(self, path):
        self.path = path  # lista di tuple (x, y)
        self.width = 40   # larghezza della faglia

    def draw(self, surface, camera_y):
        for i in range(len(self.path) - 1):
            p1 = self.path[i]
            p2 = self.path[i + 1]
            
            screen_p1 = (p1[0], SCREEN_HEIGHT - (p1[1] - camera_y))
            screen_p2 = (p2[0], SCREEN_HEIGHT - (p2[1] - camera_y))
            
            # Effetto glow esterno della faglia
            glow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # Alone luminoso più ampio
            for glow_width in range(self.width + 30, self.width - 5, -3):
                alpha = max(10, 40 - (glow_width - self.width))
                glow_color = (120, 80, 255, alpha)
                pygame.draw.line(glow_surface, glow_color, screen_p1, screen_p2, glow_width)
            
            surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
            
            # Faglia principale con gradiente
            pygame.draw.line(surface, (100, 60, 200), screen_p1, screen_p2, self.width)
            pygame.draw.line(surface, (150, 100, 255), screen_p1, screen_p2, self.width - 10)
            pygame.draw.line(surface, (200, 150, 255), screen_p1, screen_p2, self.width - 20)
            
            # Bordi luminosi
            pygame.draw.line(surface, (255, 200, 255), screen_p1, screen_p2, 4)
            
            # Effetti di energia che scorrono lungo la faglia
            segment_length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if segment_length > 0:
                num_energy_points = int(segment_length // 20)
                for j in range(num_energy_points):
                    progress = (j / max(1, num_energy_points - 1))
                    energy_x = p1[0] + (p2[0] - p1[0]) * progress
                    energy_y = SCREEN_HEIGHT - (p1[1] + (p2[1] - p1[1]) * progress - camera_y)
                    
                    # Effetto energia pulsante
                    pulse = abs(math.sin(pygame.time.get_ticks() * 0.01 + j * 0.5))
                    energy_size = int(3 + pulse * 4)
                    energy_color = (255, int(200 + pulse * 55), int(100 + pulse * 155))
                    
                    pygame.draw.circle(surface, energy_color, (int(energy_x), int(energy_y)), energy_size)
            
            # Scintille casuali più spettacolari
            if random.randint(1, 5) == 1:
                sparkle_x = p1[0] + random.randint(-self.width//2, self.width//2)
                sparkle_y = SCREEN_HEIGHT - (p1[1] - camera_y) + random.randint(-15, 15)
                sparkle_size = random.randint(2, 5)
                sparkle_color = (255, 255, random.randint(150, 255))
                
                # Sparkle con alone
                sparkle_surface = pygame.Surface((sparkle_size*6, sparkle_size*6), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surface, sparkle_color + (100,), (sparkle_size*3, sparkle_size*3), sparkle_size*3)
                pygame.draw.circle(sparkle_surface, sparkle_color, (sparkle_size*3, sparkle_size*3), sparkle_size)
                surface.blit(sparkle_surface, (sparkle_x - sparkle_size*3, sparkle_y - sparkle_size*3), special_flags=pygame.BLEND_ADD)

    def contiene(self, particle):
        # Controlla se la particella è vicina a uno dei segmenti
        for i in range(len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i+1]
            px, py = particle.x, particle.y

            # Distanza punto-segmento
            dx, dy = x2 - x1, y2 - y1
            length_squared = dx*dx + dy*dy
            if length_squared == 0:
                continue
            t = max(0, min(1, ((px - x1)*dx + (py - y1)*dy) / length_squared))
            proj_x = x1 + t * dx
            proj_y = y1 + t * dy
            dist = math.hypot(px - proj_x, py - proj_y)
            if dist < self.width / 2:
                return (proj_x, proj_y)
        return None
# Classe singola particella magma
class MagmaParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 10
        self.viscosity = 0.1  # da basso a alto, cambia man mano
        self.color = (255, 100, 0)
        self.boost_time = 0  # Tempo rimanente di boost
        self.boosted = False  # Flag se è sotto effetto boost

    def update_viscosity_and_color(self):
        # Cambia viscosità in base alla posizione y (più in alto = più viscoso) - RIVISTO
        if self.y < section_heights["Crosta"]:
            self.viscosity = 0.05  # molto fluido nel mantello
            self.color = (255, 140, 50)  # arancione chiaro
        elif self.y < section_heights["Vulcano"]:
            self.viscosity = 0.10  # leggermente più viscoso nella crosta
            self.color = (230, 90, 20)
        else:
            # PROBLEMA RISOLTO: viscosità troppo bassa nel vulcano
            self.viscosity = 0.15  # Ridotto da 0.3 a 0.15 per evitare rallentamento eccessivo
            self.color = (180, 50, 10)

    def update(self, neighbors):
        # Decrementa il tempo di boost
        if self.boost_time > 0:
            self.boost_time -= 1
            self.boosted = True
        else:
            self.boosted = False
        
        # Movimento semplice: attrazione verso centro, viscosità rallenta movimento
        center_x = SCREEN_WIDTH // 2
        dx = center_x - self.x
        self.vx += dx * 0.001  # forza centripeta

        # Gravità verso il basso (ridotta)
        self.vy += GRAVITY  # GRAVITY è già negativo (-0.02)
        
        # BOOST CONTINUO: se boosted, spinta extra verso l'alto
        if self.boosted:
            self.vy += FORCE * 0.8  # Spinta continua mentre boosted
            self.color = (255, 255, 150)  # Colore dorato
            # Riduce drasticamente la viscosità durante boost
            effective_viscosity = self.viscosity * 0.3
        else:
            effective_viscosity = self.viscosity

        # Attrito viscoso (con viscosità effettiva ridotta durante boost)
        self.vx *= (1 - effective_viscosity)
        self.vy *= (1 - effective_viscosity)

        # Aggiorna posizione
        self.x += self.vx
        self.y += self.vy

        # Limiti orizzontali per restare all'interno di +-50 px dal centro
        if self.x < center_x - 50:
            self.x = center_x - 50
            self.vx *= -0.5
        elif self.x > center_x + 50:
            self.x = center_x + 50
            self.vx *= -0.5

# Classe magma come fluido di particelle
class MagmaFluid:
    def __init__(self, num_particles=60):  # Ridotto da 120 a 60 particelle
        self.particles = []
        start_y = 0
        center_x = SCREEN_WIDTH // 2
        for _ in range(num_particles):
            px = center_x + random.uniform(-20, 20)  # Ridotto la dispersione
            py = start_y + random.uniform(0, 30)     # Ridotto la dispersione
            self.particles.append(MagmaParticle(px, py))
        self.trail = []
        self.collected_bubbles = 0  # Contatore bolle raccolte

    def update(self, force, move_left=False, move_right=False, gas_bubbles=[]):
        global gas_released, game_score
        
        # Aggiorna viscosità e colore particelle
        for p in self.particles:
            p.update_viscosity_and_color()

        # Aggiorna posizione particelle
        for p in self.particles:
            p.update(self.particles)
        
        # MOVIMENTO ORIZZONTALE CON FRECCE
        if move_left:
            for p in self.particles:
                p.vx -= 0.03  # Ridotto la forza
        if move_right:
            for p in self.particles:
                p.vx += 0.03  # Ridotto la forza
        
        # INTERAZIONE CON BOLLE DI GAS BOOST - MIGLIORATA
        for bubble in gas_bubbles[:]:  # Copia la lista per modificarla
            for p in self.particles:
                if not bubble.collected and bubble.check_collision(p):
                    # BOOST POTENTE E DURATURO dalla bolla di gas!
                    p.vy += FORCE * bubble.boost_power * 5.0  # Boost iniziale più potente
                    p.boost_time = 180  # 3 secondi di boost a 60 FPS
                    p.boosted = True
                    bubble.collected = True
                    self.collected_bubbles += 1
                    game_score += 100  # Bonus punteggio per bolla raccolta
                    
                    # Rimuovi la bolla raccolta
                    if bubble in gas_bubbles:
                        gas_bubbles.remove(bubble)
                    break
        
        # ESSOLUZIONE DEI GAS - Soglia critica MIGLIORATA
        avg_y = sum(p.y for p in self.particles) / len(self.particles)
        if avg_y >= gas_threshold and not gas_released:
            gas_released = True
            game_score += 500  # Bonus per raggiungere soglia gas
            for p in self.particles:
                p.vy += FORCE * 3.0  # Aumentato da 2.0 a 3.0 - spinta più potente
                p.viscosity *= 0.3   # Riduzione viscosità più drastica (era 0.5)
                p.boost_time = 300   # 5 secondi di boost continuo
                p.boosted = True
                p.color = (255, 200, 100)  # Colore meno intenso
        
        # Spinta continua dei gas una volta liberati - POTENZIATA
        if gas_released:
            for p in self.particles:
                if p.y >= gas_threshold:
                    p.vy += FORCE * 2.5  # Aumentato da 1.5 a 2.5
                    p.color = (255, 180, 80)  # Colore più sobrio
        
        # Interazione con faglie - meno caotica
        for p in self.particles:
            for f in faglie:
                fault_point = f.contiene(p)
                if fault_point:
                    p.vy += FORCE * 1.2  # Ridotto da 1.5 a 1.2
                    p.viscosity *= 0.8   # Meno drastico
                    ax, ay = fault_point
                    p.vx += (ax - p.x) * 0.005  # Ridotto da 0.01 a 0.005
                    p.color = (255, 150, 50)  # Colore meno intenso

        # Spinta manuale verso l'alto (spacebar) - MIGLIORATA
        if force:
            for p in self.particles:
                # Spinta più potente e adattata alla viscosità
                base_force = FORCE * (2.5 - p.viscosity)  # Aumentato da 1.5 a 2.5
                
                # Spinta extra se nella sezione vulcano (dove c'è più resistenza)
                if p.y >= section_heights["Vulcano"]:
                    base_force *= 1.5  # 50% di spinta extra nel vulcano
                
                p.vy += base_force

        # Aggiorna scia (meno lunga)
        avg_y = sum(p.y for p in self.particles) / len(self.particles)
        avg_x = sum(p.x for p in self.particles) / len(self.particles)
        avg_r = sum(p.radius for p in self.particles) / len(self.particles)

        if len(self.trail) == 0 or abs(self.trail[-1][1] - avg_y) > 15:  # Scia meno densa
            self.trail.append((avg_x, avg_y, avg_r))
            if len(self.trail) > 60:  # Ridotto da 120 a 60
                self.trail.pop(0)

    def draw(self, surface, camera_y):
        # Disegna scia con trasparenze variabili e effetti glow
        for i, (tx, ty, tr) in enumerate(self.trail):
            fade = int(150 * (i / len(self.trail)))
            
            # Alone luminoso per la scia
            glow_surface = pygame.Surface((tr*6, tr*6), pygame.SRCALPHA)
            glow_color = (100 + fade, 30, 0, 80)
            pygame.draw.circle(glow_surface, glow_color, (tr*3, tr*3), int(tr*2.5))
            surface.blit(glow_surface, (int(tx - tr*3), SCREEN_HEIGHT - int(ty - camera_y) - tr*3), special_flags=pygame.BLEND_ADD)
            
            # Scia principale
            color = (100 + fade, 30, 0)
            pygame.draw.circle(surface, color, (int(tx), SCREEN_HEIGHT - int(ty - camera_y)), int(tr * 0.8))

        # Disegna particelle con effetti avanzati
        for p in self.particles:
            screen_y = SCREEN_HEIGHT - (p.y - camera_y)
            
            # Controlla se la particella è in una faglia per effetti speciali
            in_fault = False
            for f in faglie:
                if f.contiene(p):
                    in_fault = True
                    break
            
            if in_fault:
                # Effetto speciale per magma nelle faglie (autostrade)
                # Alone luminoso molto più grande e spettacolare
                glow_size = p.radius * 8
                glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                
                # Multistrato glow effect
                pygame.draw.circle(glow_surface, (255, 255, 100, 60), (glow_size, glow_size), glow_size)
                pygame.draw.circle(glow_surface, (255, 200, 50, 100), (glow_size, glow_size), int(glow_size*0.7))
                pygame.draw.circle(glow_surface, p.color + (150,), (glow_size, glow_size), int(glow_size*0.4))
                
                surface.blit(glow_surface, (p.x - glow_size, screen_y - glow_size), special_flags=pygame.BLEND_ADD)
                
                # Particelle scintillanti dinamiche
                for _ in range(5):
                    spark_x = p.x + random.randint(-25, 25)
                    spark_y = screen_y + random.randint(-25, 25)
                    spark_size = random.randint(1, 3)
                    spark_color = (255, 255, random.randint(100, 255))
                    pygame.draw.circle(surface, spark_color, (int(spark_x), int(spark_y)), spark_size)
                
                # Nucleo della particella
                core_surface = pygame.Surface((p.radius*4, p.radius*4), pygame.SRCALPHA)
                pygame.draw.circle(core_surface, (255, 255, 255, 200), (p.radius*2, p.radius*2), p.radius)
                surface.blit(core_surface, (p.x - p.radius*2, screen_y - p.radius*2), special_flags=pygame.BLEND_ADD)
            else:
                # Rendering normale migliorato con glow
                glow_size = p.radius * 3
                glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                
                # Glow esterno
                glow_color = tuple(list(p.color) + [60])
                pygame.draw.circle(glow_surface, glow_color, (glow_size, glow_size), glow_size)
                
                # Glow interno
                inner_glow = tuple([min(255, c + 50) for c in p.color] + [120])
                pygame.draw.circle(glow_surface, inner_glow, (glow_size, glow_size), int(glow_size*0.6))
                
                surface.blit(glow_surface, (p.x - glow_size, screen_y - glow_size), special_flags=pygame.BLEND_ADD)
                
                # Nucleo solido
                pygame.draw.circle(surface, p.color, (int(p.x), int(screen_y)), p.radius)
                
                # Highlight centrale
                highlight_color = tuple([min(255, c + 100) for c in p.color])
                pygame.draw.circle(surface, highlight_color, (int(p.x), int(screen_y)), max(1, p.radius//3))



# Minimappa
class MiniMap:
    def __init__(self):
        self.width = 150
        self.height = 400
        self.x = SCREEN_WIDTH - self.width - 10
        self.y = 10

    def draw(self, surface, magma_y):
        pygame.draw.rect(surface, GREY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height), 2)

        total_height = section_heights["Vulcano"] + 1000
        scaled_y = int(self.height - (magma_y / total_height) * self.height)
        pygame.draw.circle(surface, RED, (self.x + self.width // 2, self.y + scaled_y), 6)

        # Sezioni
        for sec, top in section_heights.items():
            h = int(self.height - (top / total_height) * self.height)
            label = small_font.render(sec, True, WHITE)
            surface.blit(label, (self.x + 5, self.y + h - 10))

# Proprietà magma (differenziazione)
class MagmaProperties:
    def __init__(self):
        self.stage = "Ultramafica"
        self.stages = [
            (0, "Ultramafica"),
            (1000, "Mafica"),
            (2000, "Intermedia"),
            (3000, "Felsica")
        ]

    def update(self, y):
        for level, name in reversed(self.stages):
            if y >= level:
                self.stage = name
                break

    def draw(self, surface):
        label = small_font.render(f"Composizione: {self.stage}", True, WHITE)
        surface.blit(label, (10, 10))

# Funzioni per sistema competitivo e classifica persistente
def load_leaderboard():
    """Carica la classifica dal file JSON"""
    global leaderboard
    try:
        if os.path.exists(leaderboard_file):
            with open(leaderboard_file, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
        else:
            leaderboard = []
    except (json.JSONDecodeError, FileNotFoundError):
        leaderboard = []
    
    # Ordina per punteggio decrescente
    leaderboard.sort(key=lambda x: x['score'], reverse=True)

def save_leaderboard():
    """Salva la classifica nel file JSON"""
    try:
        with open(leaderboard_file, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Errore nel salvare la classifica: {e}")

def add_score_to_leaderboard(name, score):
    """Aggiunge un nuovo punteggio alla classifica"""
    global leaderboard
    
    # Crea nuovo record
    new_record = {
        'name': name.strip() if name.strip() else "Anonimo",
        'score': score,
        'date': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Aggiungi alla classifica
    leaderboard.append(new_record)
    
    # Ordina per punteggio decrescente
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Mantieni solo i migliori 20 record
    leaderboard = leaderboard[:20]
    
    # Salva su file
    save_leaderboard()
    
    return get_player_position(score)

def get_player_position(score):
    """Restituisce la posizione del giocatore nella classifica"""
    for i, record in enumerate(leaderboard):
        if record['score'] == score:
            return i + 1
    return len(leaderboard) + 1

def update_score(magma_y):
    """Aggiorna il punteggio basato sull'altitudine"""
    global game_score
    # Punteggio basato sull'altitudine raggiunta
    altitude_bonus = max(0, int(magma_y / 10))
    game_score = max(game_score, altitude_bonus)

def check_objectives(magma_y):
    """Controlla se gli obiettivi sono stati raggiunti"""
    global objective_index, game_score, current_objective
    
    if objective_index < len(objectives):
        target_altitude, description, bonus = objectives[objective_index]
        if magma_y >= target_altitude:
            game_score += bonus
            objective_index += 1
            if objective_index < len(objectives):
                current_objective = objectives[objective_index][1]
            else:
                current_objective = "MISSIONE COMPLETATA!"

def check_game_over():
    """Controlla condizioni di game over"""
    global stato, game_time
    
    current_time = (pygame.time.get_ticks() - game_start_time) / 1000
    
    # Game over se il tempo è scaduto
    if current_time >= max_time:
        stato = INPUT_NAME  # Vai all'inserimento nome invece di GAME_OVER
    """Aggiorna il punteggio basato sull'altitudine"""
    global game_score
    # Punteggio basato sull'altitudine raggiunta
    altitude_bonus = max(0, int(magma_y / 10))
    game_score = max(game_score, altitude_bonus)

def check_objectives(magma_y):
    """Controlla se gli obiettivi sono stati raggiunti"""
    global objective_index, game_score, current_objective
    
    if objective_index < len(objectives):
        target_altitude, description, bonus = objectives[objective_index]
        if magma_y >= target_altitude:
            game_score += bonus
            objective_index += 1
            if objective_index < len(objectives):
                current_objective = objectives[objective_index][1]
            else:
                current_objective = "MISSIONE COMPLETATA!"

def check_game_over():
    """Controlla condizioni di game over"""
    global stato, game_time
    
    current_time = (pygame.time.get_ticks() - game_start_time) / 1000
    
    # Game over se il tempo è scaduto
    if current_time >= max_time:
        stato = GAME_OVER
        update_best_scores()

def update_best_scores():
    """Aggiorna la classifica dei migliori punteggi"""
    global best_scores, game_score
    
    best_scores.append(game_score)
    best_scores.sort(reverse=True)
    best_scores = best_scores[:5]  # Mantieni solo i top 5

def draw_name_input(surface):
    """Schermata per inserimento nome giocatore"""
    global player_name, input_active
    
    # Overlay scuro
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))
    
    # Pannello centrale
    panel_width, panel_height = 600, 350
    panel_x = (SCREEN_WIDTH - panel_width) // 2
    panel_y = (SCREEN_HEIGHT - panel_height) // 2
    
    # Colore del pannello basato sul tipo di fine gioco
    if eruption_active:
        # Vittoria - pannello dorato
        pygame.draw.rect(surface, (40, 30, 10), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (255, 215, 0), (panel_x, panel_y, panel_width, panel_height), 4)
        title_text = big_font.render("🏆 NUOVO RECORD! 🏆", True, (255, 215, 0))
    else:
        # Game over normale
        pygame.draw.rect(surface, (20, 20, 20), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (100, 150, 255), (panel_x, panel_y, panel_width, panel_height), 4)
        title_text = big_font.render("PARTITA TERMINATA", True, (255, 100, 100))
    
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 60))
    surface.blit(title_text, title_rect)
    
    # Punteggio finale
    score_text = font.render(f"Punteggio: {game_score}", True, (255, 255, 100))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 120))
    surface.blit(score_text, score_rect)
    
    # Istruzione per inserimento nome
    instruction_text = small_font.render("Inserisci il tuo nome per la classifica:", True, (255, 255, 255))
    instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 170))
    surface.blit(instruction_text, instruction_rect)
    
    # Campo di input del nome
    input_width = 400
    input_height = 50
    input_x = (SCREEN_WIDTH - input_width) // 2
    input_y = panel_y + 200
    
    # Sfondo del campo input
    input_color = (100, 100, 100) if input_active else (60, 60, 60)
    pygame.draw.rect(surface, input_color, (input_x, input_y, input_width, input_height))
    pygame.draw.rect(surface, (255, 255, 255), (input_x, input_y, input_width, input_height), 2)
    
    # Testo inserito
    display_name = player_name
    if input_active and pygame.time.get_ticks() % 1000 < 500:  # Cursore lampeggiante
        display_name += "|"
    
    name_text = font.render(display_name, True, (255, 255, 255))
    name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, input_y + input_height//2))
    
    # Limita il testo alla larghezza del campo
    if name_rect.width > input_width - 20:
        # Tronca il testo se troppo lungo
        truncated_name = player_name[-(len(player_name)//2):]
        if input_active and pygame.time.get_ticks() % 1000 < 500:
            truncated_name += "|"
        name_text = font.render(truncated_name, True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, input_y + input_height//2))
    
    surface.blit(name_text, name_rect)
    
    # Istruzioni
    enter_text = small_font.render("Premi INVIO per confermare", True, (200, 255, 200))
    enter_rect = enter_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 280))
    surface.blit(enter_text, enter_rect)
    
def draw_hud(surface, magma_y):
    """Disegna HUD pulito e competitivo"""
    global game_time
    
    # Tempo rimanente
    current_time = (pygame.time.get_ticks() - game_start_time) / 1000
    time_left = max(0, max_time - current_time)
    
    # Pannello HUD principale
    hud_surface = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
    hud_surface.fill((0, 0, 0, 150))
    surface.blit(hud_surface, (0, 0))
    
    # Linea separatrice
    pygame.draw.line(surface, (100, 200, 255), (0, 120), (SCREEN_WIDTH, 120), 2)
    
    # Timer (rosso se < 30 secondi)
    timer_color = (255, 100, 100) if time_left < 30 else (255, 255, 255)
    timer_text = font.render(f"TEMPO: {int(time_left)}s", True, timer_color)
    surface.blit(timer_text, (20, 20))
    
    # Punteggio
    score_text = font.render(f"PUNTEGGIO: {game_score}", True, (255, 255, 100))
    surface.blit(score_text, (20, 60))
    
    # Altitudine attuale
    altitude_text = small_font.render(f"Altitudine: {int(magma_y)}m", True, (200, 255, 200))
    surface.blit(altitude_text, (300, 25))
    
    # Obiettivo corrente
    objective_text = small_font.render(f"Obiettivo: {current_objective}", True, (255, 200, 100))
    surface.blit(objective_text, (300, 50))
    
    # Bolle raccolte
    if hasattr(magma, 'collected_bubbles'):
        bubbles_text = small_font.render(f"💨 Bolle: {magma.collected_bubbles}", True, (150, 220, 255))
        surface.blit(bubbles_text, (300, 75))
    
    # Barra di progresso obiettivo
    if objective_index < len(objectives):
        target_altitude = objectives[objective_index][0]
        progress = min(1.0, magma_y / target_altitude)
        
        bar_width = 200
        bar_height = 8
        bar_x = SCREEN_WIDTH - 220
        bar_y = 30
        
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        progress_text = small_font.render(f"{int(progress * 100)}%", True, (255, 255, 255))
        surface.blit(progress_text, (bar_x + bar_width + 10, bar_y - 5))
    """Disegna HUD pulito e competitivo"""
    global game_time
    
    # Tempo rimanente
    current_time = (pygame.time.get_ticks() - game_start_time) / 1000
    time_left = max(0, max_time - current_time)
    
    # Pannello HUD principale
    hud_surface = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
    hud_surface.fill((0, 0, 0, 150))
    surface.blit(hud_surface, (0, 0))
    
    # Linea separatrice
    pygame.draw.line(surface, (100, 200, 255), (0, 120), (SCREEN_WIDTH, 120), 2)
    
    # Timer (rosso se < 30 secondi)
    timer_color = (255, 100, 100) if time_left < 30 else (255, 255, 255)
    timer_text = font.render(f"TEMPO: {int(time_left)}s", True, timer_color)
    surface.blit(timer_text, (20, 20))
    
    # Punteggio
    score_text = font.render(f"PUNTEGGIO: {game_score}", True, (255, 255, 100))
    surface.blit(score_text, (20, 60))
    
    # Altitudine attuale
    altitude_text = small_font.render(f"Altitudine: {int(magma_y)}m", True, (200, 255, 200))
    surface.blit(altitude_text, (300, 25))
    
    # Obiettivo corrente
    objective_text = small_font.render(f"Obiettivo: {current_objective}", True, (255, 200, 100))
    surface.blit(objective_text, (300, 50))
    
    # Bolle raccolte
    if hasattr(magma, 'collected_bubbles'):
        bubbles_text = small_font.render(f"💨 Bolle: {magma.collected_bubbles}", True, (150, 220, 255))
        surface.blit(bubbles_text, (300, 75))
    
    # Barra di progresso obiettivo
    if objective_index < len(objectives):
        target_altitude = objectives[objective_index][0]
        progress = min(1.0, magma_y / target_altitude)
        
        bar_width = 200
        bar_height = 8
        bar_x = SCREEN_WIDTH - 220
        bar_y = 30
        
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, int(bar_width * progress), bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        progress_text = small_font.render(f"{int(progress * 100)}%", True, (255, 255, 255))
        surface.blit(progress_text, (bar_x + bar_width + 10, bar_y - 5))

def draw_game_over(surface):
    """Schermata game over/vittoria con posizione in classifica"""
    global player_position
    
    # Overlay scuro
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    # Pannello centrale più grande per vittoria
    panel_width, panel_height = 500, 400
    panel_x = (SCREEN_WIDTH - panel_width) // 2
    panel_y = (SCREEN_HEIGHT - panel_height) // 2
    
    # Colore del pannello basato sul tipo di fine gioco
    if eruption_active:
        # Vittoria - pannello dorato
        pygame.draw.rect(surface, (40, 30, 10), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (255, 215, 0), (panel_x, panel_y, panel_width, panel_height), 4)
        
        # Testo vittoria
        victory_text = big_font.render("🌋 VITTORIA! 🌋", True, (255, 215, 0))
        text_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 80))
        surface.blit(victory_text, text_rect)
        
        success_text = font.render("Eruzione completata!", True, (255, 255, 100))
        success_rect = success_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 140))
        surface.blit(success_text, success_rect)
    else:
        # Game over normale
        pygame.draw.rect(surface, (20, 20, 20), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (100, 150, 255), (panel_x, panel_y, panel_width, panel_height), 3)
        
        game_over_text = big_font.render("TEMPO SCADUTO", True, (255, 100, 100))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 80))
        surface.blit(game_over_text, text_rect)
    
    # Punteggio finale
    final_score_text = font.render(f"Punteggio Finale: {game_score}", True, (255, 255, 100))
    score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 180))
    surface.blit(final_score_text, score_rect)
    
    # Statistiche aggiuntive
    if hasattr(magma, 'collected_bubbles'):
        bubbles_text = small_font.render(f"Bolle raccolte: {magma.collected_bubbles}", True, (150, 220, 255))
        bubbles_rect = bubbles_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 220))
        surface.blit(bubbles_text, bubbles_rect)
    
    # Posizione in classifica (se già inserita)
    if 'player_position' in globals() and player_position:
        position_text = small_font.render(f"🏆 Posizione #{player_position} nella classifica!", True, (100, 255, 100))
        pos_rect = position_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 250))
        surface.blit(position_text, pos_rect)
    
    # Istruzioni
    restart_text = small_font.render("Premi SPAZIO per giocare ancora", True, (200, 200, 200))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 300))
    surface.blit(restart_text, restart_rect)
    
    menu_text = small_font.render("Premi ESC per il menu", True, (200, 200, 200))
    menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH//2, panel_y + 330))
    surface.blit(menu_text, menu_rect)

def draw_leaderboard(surface):
    """Disegna la classifica persistente"""
    surface.fill((20, 30, 40))
    
    # Titolo
    title_text = big_font.render("🏆 CLASSIFICA 🏆", True, (255, 255, 100))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 60))
    surface.blit(title_text, title_rect)
    
    # Sottotitolo con numero di giocatori
    subtitle_text = small_font.render(f"Record di {len(leaderboard)} giocatori", True, (200, 200, 200))
    subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, 100))
    surface.blit(subtitle_text, subtitle_rect)
    
    # Header della tabella
    header_y = 140
    name_x = 50
    score_x = 350
    date_x = 550
    
    header_font = pygame.font.SysFont("Arial", 24, bold=True)
    pos_header = header_font.render("#", True, (255, 255, 255))
    name_header = header_font.render("NOME", True, (255, 255, 255))
    score_header = header_font.render("PUNTEGGIO", True, (255, 255, 255))
    date_header = header_font.render("DATA", True, (255, 255, 255))
    
    surface.blit(pos_header, (20, header_y))
    surface.blit(name_header, (name_x, header_y))
    surface.blit(score_header, (score_x, header_y))
    surface.blit(date_header, (date_x, header_y))
    
    # Linea separatrice
    pygame.draw.line(surface, (100, 100, 100), (10, header_y + 35), (SCREEN_WIDTH - 10, header_y + 35), 2)
    
    # Top 10 punteggi
    start_y = header_y + 50
    visible_records = min(10, len(leaderboard))
    
    for i in range(visible_records):
        record = leaderboard[i]
        y_pos = start_y + i * 40
        
        # Colori diversi per le prime tre posizioni
        if i == 0:
            rank_color = (255, 215, 0)  # Oro
            bg_color = (50, 40, 0)
        elif i == 1:
            rank_color = (192, 192, 192)  # Argento
            bg_color = (40, 40, 40)
        elif i == 2:
            rank_color = (205, 127, 50)  # Bronzo
            bg_color = (40, 30, 20)
        else:
            rank_color = (255, 255, 255)
            bg_color = (30, 30, 30)
        
        # Sfondo per il record
        if i < 3:
            pygame.draw.rect(surface, bg_color, (10, y_pos - 5, SCREEN_WIDTH - 20, 35))
        
        # Posizione
        pos_text = font.render(f"{i+1}", True, rank_color)
        surface.blit(pos_text, (25, y_pos))
        
        # Nome (limitato a 15 caratteri)
        display_name = record['name'][:15] + "..." if len(record['name']) > 15 else record['name']
        name_text = font.render(display_name, True, rank_color)
        surface.blit(name_text, (name_x, y_pos))
        
        # Punteggio
        score_text = font.render(f"{record['score']}", True, rank_color)
        surface.blit(score_text, (score_x, y_pos))
        
        # Data (formato più compatto)
        date_text = small_font.render(record['date'], True, (200, 200, 200))
        surface.blit(date_text, (date_x, y_pos + 5))
    
    # Messaggio se nessun record
    if not leaderboard:
        no_records_text = font.render("Nessun record ancora registrato", True, (150, 150, 150))
        no_records_rect = no_records_text.get_rect(center=(SCREEN_WIDTH//2, 300))
        surface.blit(no_records_text, no_records_rect)
    
    # Istruzioni
    back_text = small_font.render("Premi ESC per tornare al menu", True, (200, 200, 200))
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
    surface.blit(back_text, back_rect)

def get_best_score():
    """Restituisce il miglior punteggio attuale"""
    if leaderboard:
        return leaderboard[0]['score']
    return 0

def restart_game():
    """Riavvia il gioco"""
    global magma, camera_y, game_score, game_start_time, objective_index, current_objective
    global gas_released, eruption_active, eruption_particles, stato, gas_bubbles, last_bubble_spawn
    global player_name, input_active, player_position
    
    # Reset magma
    magma = MagmaFluid()
    camera_y = 0
    
    # Reset punteggio e tempo
    game_score = 0
    game_start_time = pygame.time.get_ticks()
    
    # Reset obiettivi
    objective_index = 0
    current_objective = objectives[0][1]
    
    # Reset gas ed eruzione
    gas_released = False
    eruption_active = False
    eruption_particles = []
    
    # Reset bolle di gas
    gas_bubbles = []
    last_bubble_spawn = 0
    
    # Reset input nome
    player_name = ""
    input_active = False
    player_position = None
    
    # Torna al gioco
    stato = GIOCO

# Funzione per disegnare l’ambiente geologico
# Funzione per disegnare l'ambiente geologico
def draw_geological_environment(surface, camera_y):
    # Calcola le altezze delle sezioni
    mantello_height = 2000
    crosta_height = 2000
    vulcano_height = 2000
    superficie = section_heights["Vulcano"] + vulcano_height  # 6000
    
    base_y = SCREEN_HEIGHT - (0 - camera_y)
    superficie_screen_y = SCREEN_HEIGHT - (superficie - camera_y)
    
        # === AMBIENTE ESTERNO E CIELO ===
    if superficie_screen_y < SCREEN_HEIGHT:
        # CIELO - gradiente dal blu chiaro al blu scuro
        for y in range(max(0, int(superficie_screen_y)), SCREEN_HEIGHT):
            progress = (y - superficie_screen_y) / max(1, SCREEN_HEIGHT - superficie_screen_y)
            
            # Gradiente cielo: dal blu chiaro in alto al celeste in basso
            blue_intensity = int(135 + progress * 120)  # 135 -> 255
            sky_color = (
                int(100 + progress * 55),   # Rosso: 100 -> 155
                int(150 + progress * 105),  # Verde: 150 -> 255  
                blue_intensity              # Blu: 135 -> 255
            )
            pygame.draw.line(surface, sky_color, (0, y), (SCREEN_WIDTH, y))
        
        # NUVOLE STATICHE
        if camera_y > superficie - 400:
            for cloud_base_x, cloud_y_offset, cloud_circles in static_clouds:
                cloud_x = (cloud_base_x + int(camera_y * 0.05)) % (SCREEN_WIDTH + 100)  # Movimento più lento
                cloud_y = superficie_screen_y + cloud_y_offset
                if 0 <= cloud_y <= SCREEN_HEIGHT:
                    for cx, cy_offset, radius in cloud_circles:
                        final_x = cloud_x + cx
                        final_y = cloud_y + cy_offset
                        if 0 <= final_x <= SCREEN_WIDTH:
                            pygame.draw.circle(surface, (240, 240, 250), (int(final_x), int(final_y)), radius)
        
        # MONTAGNE LONTANE STATICHE
        if camera_y > superficie - 300:
            for mountain_x, mountain_height, mountain_width in static_mountains:
                points = [
                    (mountain_x - mountain_width, superficie_screen_y),
                    (mountain_x, superficie_screen_y - mountain_height),
                    (mountain_x + mountain_width, superficie_screen_y)
                ]
                if superficie_screen_y >= 0:
                    pygame.draw.polygon(surface, (80, 90, 120), points)
        
        # ENORME STRATOVULCANO NELL'AMBIENTE ESTERNO - RIDISEGNATO
        if superficie_screen_y >= 0 and superficie_screen_y < SCREEN_HEIGHT:
            center_x = SCREEN_WIDTH // 2
            
            # === TERRENO BASE MIGLIORATO ===
            # Terreno ondulato invece di linea piatta
            terrain_points = []
            for x in range(0, SCREEN_WIDTH + 20, 20):
                terrain_height = superficie_screen_y + random.randint(-5, 5)
                terrain_points.append((x, terrain_height))
            
            # Disegna terreno con gradiente
            for i in range(len(terrain_points) - 1):
                x1, y1 = terrain_points[i]
                x2, y2 = terrain_points[i + 1]
                # Terreno verde-marrone
                pygame.draw.line(surface, (60, 140, 60), (x1, y1), (x2, y2), 12)
                pygame.draw.line(surface, (80, 100, 40), (x1, y1 + 6), (x2, y2 + 6), 8)
            
            # === VULCANO MASSICCIO REALISTICO ===
            volcano_base_width = 400  # Base ancora più larga
            volcano_height = 220      # Più alto e imponente
            
            # FALDE DEL VULCANO con strati geologici visibili
            left_base = center_x - volcano_base_width
            right_base = center_x + volcano_base_width
            peak_y = superficie_screen_y - volcano_height
            
            # Disegna strati geologici del vulcano
            num_layers = 8
            for layer in range(num_layers):
                layer_progress = layer / num_layers
                layer_y = superficie_screen_y - (volcano_height * layer_progress)
                layer_width = volcano_base_width * (1 - layer_progress * 0.8)
                
                # Colori che cambiano con l'altitudine
                if layer_progress < 0.3:  # Base - rocce scure
                    layer_color = (70 + int(layer * 10), 60 + int(layer * 8), 50 + int(layer * 6))
                elif layer_progress < 0.7:  # Medio - rocce vulcaniche
                    layer_color = (90 + int(layer * 8), 70 + int(layer * 6), 55 + int(layer * 5))
                else:  # Sommità - rocce chiare
                    layer_color = (110 + int(layer * 5), 90 + int(layer * 4), 70 + int(layer * 3))
                
                # Pendio sinistro
                if layer_width > 40:
                    pygame.draw.line(surface, layer_color, 
                                   (center_x - layer_width, layer_y), 
                                   (center_x - 50, layer_y), 8)
                # Pendio destro
                if layer_width > 40:
                    pygame.draw.line(surface, layer_color, 
                                   (center_x + 50, layer_y), 
                                   (center_x + layer_width, layer_y), 8)
            
            # PROFILO ESTERNO DEL VULCANO
            # Pendio sinistro con forma realistica
            left_slope_points = []
            for i in range(20):
                progress = i / 19
                x = left_base + (volcano_base_width - 50) * progress
                y = superficie_screen_y - (volcano_height * math.pow(progress, 0.6))  # Curva realistica
                left_slope_points.append((x, y))
            
            # Pendio destro
            right_slope_points = []
            for i in range(20):
                progress = i / 19
                x = right_base - (volcano_base_width - 50) * progress
                y = superficie_screen_y - (volcano_height * math.pow(progress, 0.6))
                right_slope_points.append((x, y))
            
            # Disegna i profili con ombreggiature
            if len(left_slope_points) > 2:
                pygame.draw.lines(surface, (120, 100, 80), False, left_slope_points, 6)  # Pendio in ombra
            if len(right_slope_points) > 2:
                pygame.draw.lines(surface, (140, 120, 100), False, right_slope_points, 6)  # Pendio al sole
            
            # === CRATERE SPETTACOLARE ===
            crater_width = 100
            crater_depth = 40
            crater_rim_y = peak_y + 20
            
            # Bordo del cratere irregolare
            crater_rim_points = []
            for i in range(16):
                angle = i * math.pi * 2 / 16
                radius_variation = random.randint(-8, 8)
                rim_x = center_x + math.cos(angle) * (crater_width//2 + radius_variation)
                rim_y = crater_rim_y + random.randint(-6, 6)
                crater_rim_points.append((rim_x, rim_y))
            
            # Riempimento del cratere
            if len(crater_rim_points) > 2:
                pygame.draw.polygon(surface, (40, 25, 15), crater_rim_points)
                
            # Bordo luminoso del cratere
            for i in range(len(crater_rim_points)):
                p1 = crater_rim_points[i]
                p2 = crater_rim_points[(i + 1) % len(crater_rim_points)]
                pygame.draw.line(surface, (180, 140, 100), p1, p2, 3)
            
            # === FUMAROLE E DETTAGLI ===
            # Fumarole secondarie sui fianchi
            for i in range(6):
                fumarole_x = center_x + random.randint(-200, 200)
                fumarole_y = superficie_screen_y - random.randint(50, 150)
                
                # Vapore dalle fumarole
                for j in range(3):
                    steam_x = fumarole_x + random.randint(-5, 5)
                    steam_y = fumarole_y - j * 15
                    steam_alpha = 150 - j * 40
                    steam_size = 8 - j * 2
                    
                    if steam_alpha > 0:
                        steam_surface = pygame.Surface((steam_size*2, steam_size*2), pygame.SRCALPHA)
                        pygame.draw.circle(steam_surface, (200, 200, 220, steam_alpha), 
                                         (steam_size, steam_size), steam_size)
                        surface.blit(steam_surface, (steam_x - steam_size, steam_y - steam_size), 
                                   special_flags=pygame.BLEND_ALPHA_SDL2)
            
            # Rocce e detriti alla base
            for i in range(15):
                rock_x = center_x + random.randint(-volcano_base_width, volcano_base_width)
                rock_y = superficie_screen_y + random.randint(-10, 5)
                rock_size = random.randint(3, 8)
                rock_color = (random.randint(60, 100), random.randint(50, 80), random.randint(40, 70))
                pygame.draw.circle(surface, rock_color, (rock_x, rock_y), rock_size)
            
            # Vegetazione sparsa lontana dal vulcano
            for i in range(12):
                tree_distance = random.randint(250, 450)
                tree_side = 1 if i % 2 == 0 else -1
                tree_x = center_x + tree_side * tree_distance
                
                if 0 <= tree_x <= SCREEN_WIDTH:
                    tree_y = superficie_screen_y + random.randint(-5, 5)
                    # Alberi più piccoli e distanti
                    pygame.draw.line(surface, (101, 67, 33), (tree_x, tree_y), (tree_x, tree_y - 25), 3)
                    pygame.draw.circle(surface, (34, 139, 34), (tree_x, tree_y - 30), 12)
    
    # === SEZIONI GEOLOGICHE SOTTERRANEE ===
    
    # --- Mantello con effetti di calore ---
    mantello_rect = pygame.Rect(0, base_y - mantello_height, SCREEN_WIDTH, mantello_height)
    
    # Gradiente di calore con particelle luminose
    for i in range(mantello_rect.top, mantello_rect.bottom, 2):
        progress = (i - mantello_rect.top) / mantello_height
        base_shade = 20 + int(80 * progress)
        
        # Effetto pulsazione del calore
        heat_pulse = abs(math.sin(pygame.time.get_ticks() * 0.002 + progress * 2))
        heat_bonus = int(heat_pulse * 30)
        
        color = (base_shade + heat_bonus, 15 + heat_bonus//2, 10)
        pygame.draw.rect(surface, color, (0, i, SCREEN_WIDTH, 2))
    
    # Particelle di magma nel mantello
    for _ in range(150):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(mantello_rect.top, mantello_rect.bottom)
        
        # Particelle pulsanti
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.003 + x * 0.01))
        size = 1 + int(pulse * 2)
        brightness = 40 + int(pulse * 60)
        
        color = (brightness, brightness//2, brightness//4)
        pygame.draw.circle(surface, color, (x, y), size)
    
    # --- Crosta con stratificazione realistica ---
    crosta_rect = pygame.Rect(0, mantello_rect.top - crosta_height, SCREEN_WIDTH, crosta_height)
    
    # Strati geologici dettagliati
    for i in range(crosta_rect.top, crosta_rect.bottom, 4):
        progress = (i - crosta_rect.top) / crosta_height
        shade = 60 + int(70 * progress)
        
        # Variazione casuale per realismo
        variation = random.randint(-10, 10)
        r = max(0, min(255, shade + variation))
        g = max(0, min(255, shade - 10 + variation))
        b = max(0, min(255, shade - 30 + variation))
        
        pygame.draw.rect(surface, (r, g, b), (0, i, SCREEN_WIDTH, 4))
    
    # Strati principali con minerali
    for i in range(crosta_rect.top, crosta_rect.bottom, 80):
        # Strato roccioso principale
        pygame.draw.line(surface, (140, 120, 100), (0, i), (SCREEN_WIDTH, i), 3)
        
        # Minerali sparsi negli strati
        for _ in range(20):
            mineral_x = random.randint(0, SCREEN_WIDTH)
            mineral_color = random.choice([(180, 180, 200), (200, 200, 150), (150, 180, 160)])
            pygame.draw.circle(surface, mineral_color, (mineral_x, i + random.randint(-10, 10)), 2)
    
    # --- STRATOVULCANO REALISTICO ---
    vulcano_rect = pygame.Rect(0, crosta_rect.top - vulcano_height, SCREEN_WIDTH, vulcano_height)
    
    # Sfondo base del vulcano
    for i in range(vulcano_rect.top, vulcano_rect.bottom, 3):
        ratio = (i - vulcano_rect.top) / vulcano_height
        r = int(80 + 40 * ratio)
        g = int(60 + 30 * ratio)
        b = int(40 + 20 * ratio)
        pygame.draw.rect(surface, (r, g, b), (0, i, SCREEN_WIDTH, 3))
    
    # FORMA CONICA DEL STRATOVULCANO
    center_x = SCREEN_WIDTH // 2
    crater_y = vulcano_rect.top
    base_y_volcano = vulcano_rect.bottom
    
    # Disegna la forma conica del vulcano
    for y in range(crater_y, base_y_volcano, 5):
        progress = (y - crater_y) / vulcano_height
        
        # Larghezza che aumenta verso la base (forma conica)
        half_width = int(50 + progress * 300)  # Da 100px in cima a 600px alla base
        
        # Pendii del vulcano con strati geologici
        left_slope = center_x - half_width
        right_slope = center_x + half_width
        
        # Colore degli strati vulcanici
        layer_color = (90 + int(progress * 60), 70 + int(progress * 40), 50 + int(progress * 30))
        
        # Disegna i pendii
        if left_slope >= 0:
            pygame.draw.line(surface, layer_color, (0, y), (left_slope, y), 5)
        if right_slope < SCREEN_WIDTH:
            pygame.draw.line(surface, layer_color, (right_slope, y), (SCREEN_WIDTH, y), 5)
        
        # Strati di lava solidificata (ogni 100 unità)
        if int(y) % 100 == 0:
            lava_color = (120, 60, 30)
            if left_slope >= 0:
                pygame.draw.line(surface, lava_color, (0, y), (left_slope, y), 8)
            if right_slope < SCREEN_WIDTH:
                pygame.draw.line(surface, lava_color, (right_slope, y), (SCREEN_WIDTH, y), 8)
    
    # CAMERA MAGMATICA SPETTACOLARE
    camera_center_y = base_y_volcano - 400
    camera_width = 200
    camera_height = 300
    
    camera_rect = pygame.Rect(center_x - camera_width//2, camera_center_y - camera_height//2, 
                             camera_width, camera_height)
    
    # Alone luminoso della camera magmatica
    glow_surface = pygame.Surface((camera_width + 100, camera_height + 100), pygame.SRCALPHA)
    
    # Effetto glow multi-strato
    for glow_radius in range(80, 20, -10):
        alpha = max(20, 100 - glow_radius)
        glow_color = (255, 100, 20, alpha)
        pygame.draw.ellipse(glow_surface, glow_color, 
                          (50 - glow_radius//2, 50 - glow_radius//2, glow_radius, glow_radius))
    
    surface.blit(glow_surface, (camera_rect.centerx - 50, camera_rect.centery - 50), special_flags=pygame.BLEND_ADD)
    
    # Riempimento dinamico della camera con magma
    time_factor = pygame.time.get_ticks() * 0.001
    for y in range(camera_rect.top, camera_rect.bottom, 2):
        for x in range(camera_rect.left, camera_rect.right, 3):
            # Forma ellittica della camera
            dx = x - center_x
            dy = y - camera_center_y
            if (dx*dx)/(camera_width//2)**2 + (dy*dy)/(camera_height//2)**2 <= 1:
                # Animazione ondulante del magma
                wave = math.sin(time_factor + x * 0.02 + y * 0.01) * 0.3
                heat = 0.7 + 0.3 * wave
                
                r = int(255 * heat)
                g = int(100 * heat)
                b = int(20 * heat)
                
                # Bolle di gas nel magma
                if random.randint(1, 50) == 1:
                    bubble_size = random.randint(2, 5)
                    bubble_color = (255, 200, 100)
                    pygame.draw.circle(surface, bubble_color, (x, y), bubble_size)
                else:
                    pygame.draw.circle(surface, (r, g, b), (x, y), 2)
    
    # Bordo della camera magmatica con effetti
    pygame.draw.ellipse(surface, (255, 150, 50), camera_rect, 6)
    pygame.draw.ellipse(surface, (200, 100, 50), camera_rect, 3)
    
    # CONDOTTO PRINCIPALE MIGLIORATO
    conduit_width = 60
    conduit_rect = pygame.Rect(center_x - conduit_width//2, crater_y, 
                              conduit_width, camera_center_y - crater_y)
    
    # Sfondo del condotto con gradiente
    for i in range(conduit_rect.top, conduit_rect.bottom, 5):
        progress = (i - conduit_rect.top) / (conduit_rect.bottom - conduit_rect.top)
        shade = int(40 + progress * 60)
        color = (shade, shade - 10, shade - 20)
        pygame.draw.rect(surface, color, (conduit_rect.left, i, conduit_width, 5))
    
    # Flusso di magma nel condotto
    flow_surface = pygame.Surface((conduit_width - 10, conduit_rect.height), pygame.SRCALPHA)
    for i in range(0, conduit_rect.height, 8):
        flow_intensity = abs(math.sin(time_factor * 2 + i * 0.1))
        flow_color = (
            int(200 + flow_intensity * 55),
            int(80 + flow_intensity * 50),
            int(20 + flow_intensity * 30),
            180
        )
        pygame.draw.rect(flow_surface, flow_color, (5, i, conduit_width - 20, 6))
    
    surface.blit(flow_surface, (conduit_rect.left + 5, conduit_rect.top))
    
    # Pareti del condotto con dettagli
    pygame.draw.line(surface, (120, 100, 80), (conduit_rect.left, crater_y), 
                    (conduit_rect.left, camera_center_y), 4)
    pygame.draw.line(surface, (120, 100, 80), (conduit_rect.right, crater_y), 
                    (conduit_rect.right, camera_center_y), 4)
    
    # Crepe nelle pareti
    for i in range(5):
        crack_y = crater_y + i * (camera_center_y - crater_y) // 5
        crack_offset = random.randint(-5, 5)
        pygame.draw.line(surface, (80, 60, 40), 
                        (conduit_rect.left + crack_offset, crack_y), 
                        (conduit_rect.left + crack_offset + 15, crack_y + 20), 2)
    
    # CRATERE
    crater_width = 80
    crater_depth = 30
    crater_rect = pygame.Rect(center_x - crater_width//2, crater_y - crater_depth, 
                             crater_width, crater_depth)
    
    # Forma del cratere
    pygame.draw.ellipse(surface, (60, 40, 30), crater_rect)
    pygame.draw.ellipse(surface, (120, 80, 60), crater_rect, 3)
    
    # Bordi del cratere con rocce
    for i in range(0, crater_width, 10):
        rock_x = center_x - crater_width//2 + i
        rock_height = random.randint(5, 15)
        pygame.draw.line(surface, (90, 70, 50), (rock_x, crater_y), 
                        (rock_x, crater_y - rock_height), 3)
    
    # CONDOTTI SECONDARI E DIACLASI
    # Piccoli condotti secondari
    for i in range(3):
        side_x = center_x + random.randint(-150, 150)
        side_y = camera_center_y + random.randint(-100, 100)
        side_width = random.randint(10, 20)
        side_height = random.randint(200, 400)
        
        side_conduit = pygame.Rect(side_x - side_width//2, side_y - side_height, 
                                  side_width, side_height)
        pygame.draw.rect(surface, (50, 40, 35), side_conduit)
        pygame.draw.rect(surface, (80, 60, 50), side_conduit, 2)
    
    # Diaclasi (fratture nella roccia) STATICHE
    for fracture_x, fracture_y1_offset, fracture_length, fracture_x_offset in static_fractures:
        fracture_y1 = vulcano_rect.top + fracture_y1_offset
        fracture_y2 = fracture_y1 + fracture_length
        if fracture_y1 < vulcano_rect.bottom and fracture_y2 > vulcano_rect.top:
            pygame.draw.line(surface, (30, 25, 20), 
                           (fracture_x, fracture_y1), 
                           (fracture_x + fracture_x_offset, fracture_y2), 2)
    
    for f in faglie:
        f.draw(screen, camera_y)

# Genera faglie casuali nel vulcano e nella crosta (ridotte per meno caos)
def generate_random_faults():
    faglie = []
    center_x = SCREEN_WIDTH // 2
    crosta_base = section_heights["Crosta"]  # 2000
    crosta_top = section_heights["Vulcano"]  # 4000
    vulcano_base = section_heights["Vulcano"]  # 4000
    vulcano_top = section_heights["Vulcano"] + 2000  # 6000
    
    # === FAGLIE NELLA CROSTA (ridotte) ===
    num_faglie_crosta = random.randint(3, 5)  # Ridotto da 5-8 a 3-5
    
    for _ in range(num_faglie_crosta):
        start_x = center_x + random.randint(-200, 200)  # Meno dispersione
        start_y = crosta_base + random.randint(200, 1200)
        
        path = [(start_x, start_y)]
        current_x, current_y = start_x, start_y
        
        segments = random.randint(3, 5)  # Ridotto da 4-7 a 3-5
        segment_height = (crosta_top - start_y) / segments
        
        for i in range(segments):
            current_y += segment_height
            current_x += random.randint(-40, 40)  # Meno variazione
            current_x = max(center_x - 250, min(center_x + 250, current_x))
            current_y = min(crosta_top, current_y)
            path.append((current_x, current_y))
            
            if current_y >= crosta_top:
                break
        
        faglie.append(Faglia(path))
    
    # === FAGLIE NEL VULCANO (ridotte) ===
    num_faglie_vulcano = random.randint(4, 6)  # Ridotto da 8-12 a 4-6
    
    for _ in range(num_faglie_vulcano):
        start_x = center_x + random.randint(-150, 150)  # Meno dispersione
        start_y = vulcano_base + random.randint(300, 600)
        
        path = [(start_x, start_y)]
        current_x, current_y = start_x, start_y
        
        segments = random.randint(2, 4)  # Ridotto da 3-6 a 2-4
        segment_height = (vulcano_top - start_y) / segments
        
        for i in range(segments):
            current_y += segment_height
            current_x += random.randint(-30, 30)  # Meno variazione
            current_x = max(center_x - 200, min(center_x + 200, current_x))
            current_y = min(vulcano_top, current_y)
            path.append((current_x, current_y))
            
            if current_y >= vulcano_top:
                break
        
        faglie.append(Faglia(path))
    
    return faglie

# Istanzia oggetti
magma = MagmaFluid()
camera_y = 0
minimap = MiniMap()
props = MagmaProperties()
faglie = generate_random_faults()

# Sistema di bolle di gas boost
gas_bubbles = []
last_bubble_spawn = 0

# Variabili per l'essoluzione dei gas
gas_threshold = section_heights["Vulcano"] + 500  # Soglia di essoluzione a 4500
gas_released = False

# Inizializza sistema competitivo
game_start_time = pygame.time.get_ticks()

# Generazione fissa per elementi grafici (evita lampeggiamento)
random.seed(42)  # Seed fisso per elementi statici
static_mountains = []
static_clouds = []
static_fractures = []

# Genera montagne statiche
center_x = SCREEN_WIDTH // 2
for i in range(5):
    mountain_x = center_x + (i - 2) * 200 + random.randint(-50, 50)
    mountain_height = random.randint(80, 150)
    mountain_width = random.randint(60, 120)
    static_mountains.append((mountain_x, mountain_height, mountain_width))

# Genera nuvole statiche
for i in range(8):
    cloud_base_x = i * 120
    cloud_y_offset = -100 - (i % 3) * 30
    cloud_circles = []
    for j in range(4):
        cx = cloud_base_x + j * 15
        cy_offset = random.randint(-5, 5)
        radius = 15 + random.randint(-3, 8)
        cloud_circles.append((cx, cy_offset, radius))
    static_clouds.append((cloud_base_x, cloud_y_offset, cloud_circles))

# Genera fratture statiche
for i in range(10):
    fracture_x = random.randint(0, SCREEN_WIDTH)
    fracture_y1_offset = random.randint(0, 2000)
    fracture_length = random.randint(50, 200)
    fracture_x_offset = random.randint(-20, 20)
    static_fractures.append((fracture_x, fracture_y1_offset, fracture_length, fracture_x_offset))

# Reset del seed per elementi casuali normali
random.seed()

# Menu migliorato
def draw_menu():
    screen.fill((20, 30, 40))
    
    # Titolo principale
    title = big_font.render("MAGMA RISER", True, (255, 100, 50))
    title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 120))
    screen.blit(title, title_rect)
    
    # Sottotitolo
    subtitle = small_font.render("Simulazione Geologica Competitiva", True, (200, 200, 200))
    subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 170))
    screen.blit(subtitle, subtitle_rect)

    # Menu opzioni
    for i, option in enumerate(menu_options):
        color = (255, 255, 100) if i == selected_option else (255, 255, 255)
        bg_color = (80, 50, 50) if i == selected_option else None
        
        text = font.render(option, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, 250 + i * 60))
        
        if bg_color:
            padding = 20
            bg_rect = pygame.Rect(text_rect.x - padding, text_rect.y - 10, 
                                text_rect.width + 2*padding, text_rect.height + 20)
            pygame.draw.rect(screen, bg_color, bg_rect)
            pygame.draw.rect(screen, color, bg_rect, 2)
        
        screen.blit(text, text_rect)
    
    # Record attuale
    best_score = get_best_score()
    if best_score > 0:
        if leaderboard:
            best_player = leaderboard[0]['name']
            record_text = small_font.render(f"Record: {best_score} punti ({best_player})", True, (255, 215, 0))
        else:
            record_text = small_font.render(f"Record: {best_score} punti", True, (255, 215, 0))
        record_rect = record_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
        screen.blit(record_text, record_rect)

    pygame.display.flip()

# Carica la classifica all'avvio
load_leaderboard()

# Loop principale migliorato per competitività
di_gioco = True
player_position = None
while di_gioco:
    force = False
    move_left = False
    move_right = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            di_gioco = False
        
        if stato == MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected_option] == "GIOCA":
                        restart_game()
                    elif menu_options[selected_option] == "CLASSIFICA":
                        stato = CLASSIFICA
                    else:
                        di_gioco = False
        
        elif stato == INPUT_NAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Conferma nome e salva punteggio
                    player_position = add_score_to_leaderboard(player_name, game_score)
                    stato = GAME_OVER
                elif event.key == pygame.K_ESCAPE:
                    # Salta inserimento nome
                    player_name = "Anonimo"
                    player_position = add_score_to_leaderboard(player_name, game_score)
                    stato = GAME_OVER
                elif event.key == pygame.K_BACKSPACE:
                    # Cancella ultimo carattere
                    player_name = player_name[:-1]
                else:
                    # Aggiungi carattere (limita a 20 caratteri)
                    if len(player_name) < 20 and event.unicode.isprintable():
                        player_name += event.unicode
            
            # Attiva il campo di input
            input_active = True
        
        elif stato == CLASSIFICA:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    stato = MENU
        
        elif stato == GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    restart_game()
                elif event.key == pygame.K_ESCAPE:
                    stato = MENU

    if stato == MENU:
        draw_menu()
        continue
    elif stato == INPUT_NAME:
        draw_name_input(screen)
        pygame.display.flip()
        continue
    elif stato == CLASSIFICA:
        draw_leaderboard(screen)
        pygame.display.flip()
        continue
    elif stato == GAME_OVER:
        draw_game_over(screen)
        pygame.display.flip()
        continue

    # Controllo continuo dei tasti premuti per movimento fluido
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        force = True
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_left = True
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_right = True
    if keys[pygame.K_ESCAPE]:
        stato = MENU
        continue

    # Aggiorna gioco
    magma.update(force, move_left, move_right, gas_bubbles)
    props.update(sum(p.y for p in magma.particles) / len(magma.particles))

    # Camera segue il magma (con limite)
    avg_y = sum(p.y for p in magma.particles) / len(magma.particles)
    camera_y = avg_y - 250
    if camera_y < 0:
        camera_y = 0

    # SPAWN BOLLE DI GAS NELLA CROSTA - MIGLIORATO
    current_time = pygame.time.get_ticks()
    if current_time - last_bubble_spawn > 2000:  # Ridotto da 3000 a 2000ms (ogni 2 secondi)
        # Spawna bolla solo se il magma è nella crosta o nel vulcano
        if section_heights["Crosta"] <= avg_y <= section_heights["Vulcano"] + 1000:
            center_x = SCREEN_WIDTH // 2
            bubble_x = center_x + random.randint(-120, 120)  # Area più ampia
            bubble_y = avg_y + random.randint(30, 150)  # Più vicine al magma
            
            # Assicurati che sia nella crosta o vulcano
            if section_heights["Crosta"] <= bubble_y <= section_heights["Vulcano"] + 1000:
                # Bolle più potenti nelle sezioni superiori
                new_bubble = GasBubble(bubble_x, bubble_y)
                if bubble_y > section_heights["Vulcano"]:  # Nel vulcano
                    new_bubble.boost_power *= 1.5  # 50% più potenti
                gas_bubbles.append(new_bubble)
                last_bubble_spawn = current_time
    
    # Aggiorna bolle di gas esistenti
    gas_bubbles = [bubble for bubble in gas_bubbles if bubble.update()]

    # Sistema competitivo
    update_score(avg_y)
    check_objectives(avg_y)
    check_game_over()

    # Controlla se iniziare l'eruzione
    check_eruption(avg_y)
    update_eruption()

    # Disegna tutto con grafica pulita
    screen.fill((10, 15, 25))  # Sfondo più scuro e pulito
    draw_geological_environment(screen, camera_y)

    # Disegna bolle di gas boost
    for bubble in gas_bubbles:
        bubble.draw(screen, camera_y)

    magma.draw(screen, camera_y)
    draw_eruption(screen, camera_y)
    
    # HUD competitivo invece di info caotiche
    draw_hud(screen, avg_y)
    
    # Vittoria immediata se eruzione completata
    if eruption_active:
        time_since_eruption = pygame.time.get_ticks() - eruption_start_time
        if time_since_eruption > 5000:  # 5 secondi di eruzione = vittoria automatica
            stato = INPUT_NAME  # Vai all'inserimento nome

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()