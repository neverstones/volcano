import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class MainMenu:
    def __init__(self, score_system):
        self.score_system = score_system
        self.selected_option = 0
        self.options = ["Gioca", "Classifica", "Esci"]
        self.font_title = pygame.font.SysFont(None, 72)
        self.font_menu = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 36)
        
        # Stato del menu
        self.state = "main"  # "main", "leaderboard"
        
    def handle_input(self, event):
        """Gestisce l'input del menu."""
        if event.type == pygame.KEYDOWN:
            if self.state == "main":
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.get_selected_action()
            elif self.state == "leaderboard":
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.state = "main"
                    return None
        return None
    
    def get_selected_action(self):
        """Restituisce l'azione selezionata."""
        if self.selected_option == 0:  # Gioca
            return "play"
        elif self.selected_option == 1:  # Classifica
            self.state = "leaderboard"
            return None
        elif self.selected_option == 2:  # Esci
            return "quit"
        return None
    
    def draw(self, screen):
        """Disegna il menu."""
        if self.state == "main":
            self.draw_main_menu(screen)
        elif self.state == "leaderboard":
            self.draw_leaderboard(screen)
    
    def draw_main_menu(self, screen):
        """Disegna il menu principale."""
        # Sfondo vulcanico
        screen.fill((20, 20, 30))
        
        # Disegna sfondo vulcanico semplificato
        for i in range(0, SCREEN_HEIGHT, 50):
            color_intensity = int(50 + (i / SCREEN_HEIGHT) * 100)
            color = (color_intensity, color_intensity // 3, 0)
            pygame.draw.rect(screen, color, (0, i, SCREEN_WIDTH, 50))
        
        # Titolo
        title_text = self.font_title.render("🌋 VOLCANO JUMP 🌋", True, (255, 200, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Sottotitolo
        subtitle_text = self.font_small.render("Salta verso il cratere!", True, (255, 150, 50))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Opzioni menu
        for i, option in enumerate(self.options):
            color = (255, 255, 255) if i == self.selected_option else (150, 150, 150)
            if i == self.selected_option:
                # Evidenziazione per opzione selezionata
                highlight_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 300 + i * 70 - 5, 200, 60)
                pygame.draw.rect(screen, (100, 50, 0), highlight_rect)
                pygame.draw.rect(screen, (255, 200, 0), highlight_rect, 3)
            
            text = self.font_menu.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 320 + i * 70))
            screen.blit(text, text_rect)
        
        # Istruzioni
        instructions = [
            "↑↓ - Naviga",
            "INVIO/SPAZIO - Seleziona",
            "Nel gioco: WASD/Frecce - Movimento, ESC - Menu, R - Restart"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, (200, 200, 200))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120 + i * 30))
            screen.blit(text, text_rect)
        
        # Miglior punteggio
        best_score = self.score_system.get_best_score()
        if best_score > 0:
            best_text = self.font_small.render(f"Record: {best_score} punti", True, (255, 215, 0))
            best_rect = best_text.get_rect(center=(SCREEN_WIDTH // 2, 260))
            screen.blit(best_text, best_rect)
    
    def draw_leaderboard(self, screen):
        """Disegna la classifica."""
        screen.fill((20, 20, 30))
        
        # Titolo
        title_text = self.font_title.render("🏆 CLASSIFICA 🏆", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_text, title_rect)
        
        # Intestazioni
        headers = ["Pos", "Punti", "Livello", "Oggetti", "Data"]
        header_y = 150
        positions = [100, 200, 320, 420, 520]
        
        for i, header in enumerate(headers):
            text = self.font_small.render(header, True, (255, 200, 0))
            screen.blit(text, (positions[i], header_y))
        
        # Linea sotto le intestazioni
        pygame.draw.line(screen, (255, 200, 0), (50, header_y + 35), (SCREEN_WIDTH - 50, header_y + 35), 2)
        
        # Punteggi
        scores = self.score_system.get_top_scores(8)  # Mostra top 8 per fare spazio
        
        if not scores:
            no_scores_text = self.font_menu.render("Nessun punteggio ancora!", True, (150, 150, 150))
            no_scores_rect = no_scores_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
            screen.blit(no_scores_text, no_scores_rect)
        else:
            for i, score_entry in enumerate(scores):
                y = header_y + 60 + i * 40
                
                # Posizione
                pos_text = self.font_small.render(f"{i+1}.", True, (255, 255, 255))
                screen.blit(pos_text, (positions[0], y))
                
                # Punti
                score_text = self.font_small.render(str(score_entry['score']), True, (255, 255, 255))
                screen.blit(score_text, (positions[1], y))
                
                # Livello
                level_text = self.font_small.render(str(score_entry.get('level_reached', 0)), True, (255, 255, 255))
                screen.blit(level_text, (positions[2], y))
                
                # Oggetti raccolti
                collectibles_text = self.font_small.render(str(score_entry.get('collectibles_collected', 0)), True, (255, 255, 255))
                screen.blit(collectibles_text, (positions[3], y))
                
                # Data (solo giorno/mese)
                date_str = score_entry.get('date', '')
                if date_str:
                    try:
                        date_parts = date_str.split(' ')[0].split('-')
                        if len(date_parts) >= 3:
                            formatted_date = f"{date_parts[2]}/{date_parts[1]}"
                        else:
                            formatted_date = date_str[:10]
                    except:
                        formatted_date = date_str[:10]
                else:
                    formatted_date = "N/A"
                
                date_text = self.font_small.render(formatted_date, True, (255, 255, 255))
                screen.blit(date_text, (positions[4], y))
        
        # Istruzioni
        instruction_text = self.font_small.render("ESC/INVIO - Torna al menu", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(instruction_text, instruction_rect)


class VictoryScreen:
    def __init__(self, score_system):
        self.score_system = score_system
        self.font_title = pygame.font.SysFont(None, 72)
        self.font_text = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 36)
        self.timer = 0
        self.duration = 4.0  # 4 secondi
        self.score_saved = False
        
    def update(self, dt, final_score, level_reached, collectibles_collected):
        """Aggiorna la schermata di vittoria."""
        self.timer += dt
        
        # Salva il punteggio solo una volta dopo 1 secondo
        if not self.score_saved and self.timer > 1.0:
            rank = self.score_system.add_score(final_score, level_reached, collectibles_collected)
            self.rank = rank
            self.score_saved = True
            print(f"🏆 Punteggio salvato! Posizione in classifica: #{rank}")
        
        return self.timer >= self.duration
    
    def draw(self, screen, final_score, level_reached, collectibles_collected):
        """Disegna la schermata di vittoria."""
        # Sfondo con effetto di fuoco
        screen.fill((50, 20, 0))
        
        # Effetto particelle di fuoco semplificato
        import random
        for _ in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(2, 8)
            intensity = random.randint(100, 255)
            color = (intensity, intensity // 2, 0)
            pygame.draw.circle(screen, color, (x, y), size)
        
        # Titolo vittoria
        title_text = self.font_title.render("🎉 VITTORIA! 🎉", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Sottotitolo
        subtitle_text = self.font_text.render("Hai raggiunto il cratere!", True, (255, 150, 50))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Statistiche
        stats = [
            f"Punteggio finale: {final_score}",
            f"Livello raggiunto: {level_reached}",
            f"Oggetti raccolti: {collectibles_collected}"
        ]
        
        for i, stat in enumerate(stats):
            text = self.font_small.render(stat, True, (255, 255, 255))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 300 + i * 40))
            screen.blit(text, text_rect)
        
        # Mostra posizione in classifica se disponibile
        if self.score_saved and hasattr(self, 'rank'):
            rank_text = self.font_small.render(f"Posizione in classifica: #{self.rank}", True, (255, 215, 0))
            rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH // 2, 420))
            screen.blit(rank_text, rank_rect)
        
        # Timer
        remaining_time = max(0, self.duration - self.timer)
        timer_text = self.font_small.render(f"Torno al menu tra: {remaining_time:.1f}s", True, (200, 200, 200))
        timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(timer_text, timer_rect)
    
    def reset(self):
        """Resetta la schermata di vittoria."""
        self.timer = 0
        self.score_saved = False
