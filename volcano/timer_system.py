import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class CooldownTimer:
    def __init__(self, total_time=240):  # 4 minuti = 240 secondi
        self.total_time = total_time
        self.current_time = total_time
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        
    def update(self, dt):
        """Aggiorna il timer."""
        self.current_time -= dt
        if self.current_time < 0:
            self.current_time = 0
        return self.current_time <= 0  # Ritorna True se il tempo è scaduto
    
    def is_expired(self):
        """Controlla se il timer è scaduto."""
        return self.current_time <= 0
    
    def apply_damage(self, seconds):
        """Applica danno sottraendo secondi dal timer."""
        self.current_time -= seconds
        if self.current_time < 0:
            self.current_time = 0
    
    def get_remaining_time(self):
        """Restituisce il tempo rimanente in secondi."""
        return self.current_time
    
    def subtract_time(self, seconds):
        """Sottrae tempo dal timer."""
        self.current_time -= seconds
        if self.current_time < 0:
            self.current_time = 0
    
    def get_time_remaining(self):
        """Restituisce il tempo rimanente in minuti e secondi."""
        minutes = int(self.current_time // 60)
        seconds = int(self.current_time % 60)
        return minutes, seconds
    
    def get_progress_percentage(self):
        """Restituisce la percentuale di tempo rimanente."""
        return self.current_time / self.total_time
    
    def draw(self, surface):
        """Disegna il timer di raffreddamento."""
        minutes, seconds = self.get_time_remaining()
        progress = self.get_progress_percentage()
        
        # Posizione in alto a destra
        timer_x = SCREEN_WIDTH - 150
        timer_y = 20
        
        # Colore che cambia in base al tempo rimanente
        if progress > 0.5:
            color = (0, 255, 0)  # Verde
        elif progress > 0.25:
            color = (255, 255, 0)  # Giallo
        else:
            color = (255, 0, 0)  # Rosso
        
        # Testo del timer
        timer_text = f"{minutes:02d}:{seconds:02d}"
        text_surface = self.font_large.render(timer_text, True, color)
        
        # Sfondo semi-trasparente
        bg_rect = pygame.Rect(timer_x - 10, timer_y - 5, 140, 50)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (0, 0, 0, 150), bg_surface.get_rect())
        pygame.draw.rect(bg_surface, color, bg_surface.get_rect(), 2)
        surface.blit(bg_surface, bg_rect.topleft)
        
        # Testo
        surface.blit(text_surface, (timer_x, timer_y))
        
        # Etichetta "Raffreddamento"
        label_text = self.font_medium.render("Raffreddamento", True, (255, 255, 255))
        surface.blit(label_text, (timer_x - 20, timer_y + 50))
        
        # Barra di progresso
        bar_width = 120
        bar_height = 8
        bar_x = timer_x - 10
        bar_y = timer_y + 75
        
        # Sfondo barra
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Barra riempimento
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
        
        # Bordo barra
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def reset(self):
        """Resetta il timer."""
        self.current_time = self.total_time


class ScorePopup:
    def __init__(self, x, y, score, text=""):
        self.x = x
        self.y = y
        self.start_y = y
        self.score = score
        self.text = text
        self.timer = 0
        self.duration = 2.0  # 2 secondi di durata
        self.font = pygame.font.SysFont(None, 36)
        
    def update(self, dt):
        """Aggiorna il popup."""
        self.timer += dt
        # Movimento verso l'alto
        self.y = self.start_y - (self.timer * 30)  # Sale di 30 pixel al secondo
        return self.timer < self.duration  # Ritorna False quando deve essere rimosso
    
    def draw(self, surface):
        """Disegna il popup del punteggio."""
        if self.timer < self.duration:
            # Calcola alpha per fade out
            alpha = max(0, 255 * (1 - self.timer / self.duration))
            
            # Testo del punteggio
            score_text = f"+{self.score}"
            if self.text:
                score_text = f"{self.text} +{self.score}"
            
            # Colore oro per i punti
            color = (255, 215, 0)
            
            text_surface = self.font.render(score_text, True, color)
            
            # Applica trasparenza
            text_surface.set_alpha(int(alpha))
            
            # Posizione centrata
            text_rect = text_surface.get_rect(center=(self.x, self.y))
            surface.blit(text_surface, text_rect)
