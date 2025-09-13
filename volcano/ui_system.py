"""
Sistema di interfaccia utente per il gioco Volcano
"""
import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, MENU, PLAYING, SCORE_LIST, ENTER_NAME, GAME_OVER
from save_system import get_top_scores, add_score

class UISystem:
    def __init__(self):
        self.font_big = pygame.font.Font(None, 64)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)
        
        # Colori
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.red = (255, 0, 0)
        self.orange = (255, 180, 0)
        self.gray = (128, 128, 128)
        self.dark_gray = (64, 64, 64)
        self.blue = (100, 150, 255)
        
        # Menu principale
        self.menu_selected = 0
        self.menu_options = ["Gioca", "Come si gioca", "Classifiche", "Esci"]

        # Stato input/cursore sempre inizializzato
        self.input_text = ""
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0
    def draw_how_to_play(self, screen):
        """Schermata di spiegazione del gioco."""
        screen.fill(self.black)
        title = self.font_big.render("COME SI GIOCA", True, self.orange)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)

        lines = [
            "Sei una goccia di magma che deve risalire il vulcano!",
            "Salta sulle piattaforme evitando di cadere.",
            "Raccogli le bolle di magma per aumentare il punteggio.",
            "Evita i nemici (i minerali): se li tocchi il raffreddamento accelera!",
            "Raggiungi il cratere per vincere!",
            "",
            "Barra di raffreddamento: se si esaurisce perdi.",
            "Usa le FRECCE per muoverti.",
            "",
            "Premi ESC per tornare al menu."
        ]
        for i, line in enumerate(lines):
            text = self.font_small.render(line, True, self.white)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 180 + i * 40))
            screen.blit(text, text_rect)
        
    def draw_menu(self, screen):
        """Disegna il menu principale."""
        # Background con gradiente
        for y in range(SCREEN_HEIGHT):
            color_value = int(20 + (y / SCREEN_HEIGHT) * 40)
            pygame.draw.line(screen, (color_value, color_value // 2, 0), (0, y), (SCREEN_WIDTH, y))
        
        # Titolo
        title = self.font_big.render("VOLCANO", True, self.orange)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Wobbly Jump", True, self.white)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(subtitle, subtitle_rect)
        
        # Opzioni menu
        start_y = 300
        for i, option in enumerate(self.menu_options):
            color = self.orange if i == self.menu_selected else self.white
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 60))
            
            # Evidenzia opzione selezionata
            if i == self.menu_selected:
                pygame.draw.rect(screen, self.dark_gray, text_rect.inflate(20, 10), 0, 5)
                
            screen.blit(text, text_rect)
        
        # Istruzioni
        instructions = [
            "Usa FRECCE SU/GIU per navigare",
            "Premi INVIO per selezionare",
            "SPAZIO per saltare durante il gioco"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_tiny.render(instruction, True, self.gray)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100 + i * 25))
            screen.blit(text, text_rect)
    
    def draw_scores(self, screen):
        """Disegna la schermata delle classifiche."""
        # Background
        screen.fill(self.black)
        
        # Titolo
        title = self.font_big.render("CLASSIFICHE", True, self.orange)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title, title_rect)
        
        # Carica punteggi
        scores = get_top_scores()
        
        if not scores:
            no_scores = self.font_medium.render("Nessun punteggio ancora!", True, self.white)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(no_scores, no_scores_rect)
        else:
            # Header tabella
            headers = ["Pos", "Nome", "Punteggio", "Data"]
            header_y = 150
            header_positions = [100, 250, 400, 550]
            
            for i, header in enumerate(headers):
                text = self.font_small.render(header, True, self.orange)
                screen.blit(text, (header_positions[i], header_y))
            
            # Linea separatore
            pygame.draw.line(screen, self.orange, (50, header_y + 30), (SCREEN_WIDTH - 50, header_y + 30), 2)
            
            # Punteggi
            for i, score in enumerate(scores[:10]):
                y_pos = header_y + 60 + i * 40
                color = self.white if i > 2 else [self.orange, self.white, (200, 200, 200)][i]
                
                # Posizione
                pos_text = self.font_small.render(f"{i+1}.", True, color)
                screen.blit(pos_text, (header_positions[0], y_pos))
                
                # Nome
                name_text = self.font_small.render(score['name'][:15], True, color)
                screen.blit(name_text, (header_positions[1], y_pos))
                
                # Punteggio
                score_text = self.font_small.render(str(score['score']), True, color)
                screen.blit(score_text, (header_positions[2], y_pos))
                
                # Data
                date_str = score['date'].split(' ')[0]  # Solo la data, senza ora
                date_text = self.font_small.render(date_str, True, color)
                screen.blit(date_text, (header_positions[3], y_pos))
        
        # Istruzioni per tornare
        back_text = self.font_small.render("Premi ESC per tornare al menu", True, self.gray)
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(back_text, back_rect)
    
    def draw_name_input(self, screen, score):
        """Disegna la schermata di inserimento nome."""
        # Background semi-trasparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(self.black)
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))
        
        # Box centrale
        box_width = 500
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        
        pygame.draw.rect(screen, self.dark_gray, (box_x, box_y, box_width, box_height), 0, 10)
        pygame.draw.rect(screen, self.orange, (box_x, box_y, box_width, box_height), 3, 10)
        
        # Titolo
        title = self.font_big.render("VITTORIA!", True, self.orange)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, box_y + 50))
        screen.blit(title, title_rect)
        
        # Punteggio
        score_text = self.font_medium.render(f"Punteggio: {score}", True, self.white)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 100))
        screen.blit(score_text, score_rect)
        
        # Label input
        label = self.font_small.render("Inserisci il tuo nome:", True, self.white)
        label_rect = label.get_rect(center=(SCREEN_WIDTH // 2, box_y + 150))
        screen.blit(label, label_rect)
        
        # Campo input
        input_box_width = 300
        input_box_height = 40
        input_x = (SCREEN_WIDTH - input_box_width) // 2
        input_y = box_y + 180
        
        pygame.draw.rect(screen, self.white, (input_x, input_y, input_box_width, input_box_height))
        pygame.draw.rect(screen, self.black, (input_x + 2, input_y + 2, input_box_width - 4, input_box_height - 4))
        
        # Testo input
        input_surface = self.font_medium.render(self.input_text, True, self.white)
        screen.blit(input_surface, (input_x + 10, input_y + 8))
        
        # Cursore lampeggiante
        if self.input_active and self.cursor_visible:
            cursor_x = input_x + 10 + input_surface.get_width()
            pygame.draw.line(screen, self.white, (cursor_x, input_y + 5), (cursor_x, input_y + input_box_height - 5), 2)
        
        # Istruzioni
        instructions = self.font_tiny.render("Premi INVIO per salvare", True, self.gray)
        instructions_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, box_y + 250))
        screen.blit(instructions, instructions_rect)
    
    def draw_game_over(self, screen):
        """Disegna la schermata di game over."""
        # Overlay semi-trasparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(self.black)
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))
        
        # Testo Game Over
        game_over_text = self.font_big.render("GAME OVER", True, self.red)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(game_over_text, game_over_rect)
        
        # Istruzioni
        restart_text = self.font_medium.render("R - Ricomincia", True, self.white)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(restart_text, restart_rect)
        
        menu_text = self.font_medium.render("ESC - Menu Principale", True, self.white)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        screen.blit(menu_text, menu_rect)
    
    def handle_menu_input(self, event):
        """Gestisce l'input del menu principale."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                return self.menu_selected
        return None
    
    def handle_name_input(self, event):
        """Gestisce l'input del nome."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.input_text.strip():
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 15 and event.unicode.isprintable():
                self.input_text += event.unicode
        return False
    
    def update(self, dt):
        """Aggiorna l'UI (per cursore lampeggiante)."""
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def reset_input(self):
        """Reset del campo input."""
        self.input_text = ""
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0