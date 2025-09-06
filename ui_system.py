"""
User interface system for the volcano game.
"""
import pygame
import math
from constants import *

def draw_menu(screen, selected_option=0):
    """Draw the main menu."""
    screen.fill((50, 20, 20))

    # Title with lava effect
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    small_font = pygame.font.SysFont("Arial", 16)
    font = pygame.font.SysFont("Arial", 24)
    
    title_y = 150
    title_text = title_font.render("VOLCANO JUMP", True, (255, 165, 0))
    title_shadow = title_font.render("VOLCANO JUMP", True, (100, 50, 0))

    screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_text.get_width()//2 + 3, title_y + 3))
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, title_y))

    # Subtitle
    subtitle = font.render("Enhanced Edition", True, (255, 255, 255))
    screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, title_y + 60))

    # Menu options
    menu_options = ["GIOCA", "CLASSIFICA", "ESCI"]

    for i, option in enumerate(menu_options):
        y = 350 + i * 50
        color = (255, 200, 0) if i == selected_option else (255, 255, 255)
        text = font.render(option, True, color)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))

    # Instructions
    instructions = [
        "Usa FRECCE o WASD per muoverti",
        "SPAZIO per saltare",
        "Raccogli power-ups e cristalli!",
        "Evita i nemici vulcanici"
    ]

    for i, instruction in enumerate(instructions):
        text = small_font.render(instruction, True, (200, 200, 200))
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 500 + i * 25))

def draw_leaderboard(screen, high_scores):
    """Draw the leaderboard screen."""
    screen.fill((30, 30, 50))

    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 16)

    title = title_font.render("CLASSIFICA", True, (255, 215, 0))
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))

    if high_scores:
        for i, score_entry in enumerate(high_scores[:10]):
            y = 150 + i * 40
            name_text = font.render(f"{i+1}. {score_entry['name']}", True, (255, 255, 255))
            score_text = font.render(f"{score_entry['score']} ({score_entry['height']:.1f}km)", True, (255, 215, 0))
            date_text = small_font.render(score_entry['date'], True, (150, 150, 150))

            screen.blit(name_text, (50, y))
            screen.blit(score_text, (250, y))
            screen.blit(date_text, (450, y + 5))
    else:
        no_scores = font.render("Nessun punteggio registrato", True, (150, 150, 150))
        screen.blit(no_scores, (SCREEN_WIDTH//2 - no_scores.get_width()//2, 300))

    back_text = small_font.render("Premi ESC per tornare al menu", True, (200, 200, 200))
    screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, SCREEN_HEIGHT - 50))

def draw_game_over(screen, score, world_offset):
    """Draw the game over screen."""
    # Create dark semi-transparent overlay that pulses
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    pulse = (math.sin(pygame.time.get_ticks() * 0.002) * 0.1 + 0.7)
    overlay.set_alpha(int(160 * pulse))
    screen.blit(overlay, (0, 0))

    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    font = pygame.font.SysFont("Arial", 24)

    # "GAME OVER" text with red glow effect
    glow_size = int(4 + math.sin(pygame.time.get_ticks() * 0.004) * 2)
    for offset in range(glow_size, 0, -1):
        glow_color = (128, 0, 0, int(255 / offset))
        game_over_text = title_font.render("GAME OVER", True, glow_color)
        pos_x = SCREEN_WIDTH//2 - game_over_text.get_width()//2
        pos_y = SCREEN_HEIGHT//2 - 100
        screen.blit(game_over_text, (pos_x - offset, pos_y))
        screen.blit(game_over_text, (pos_x + offset, pos_y))
        screen.blit(game_over_text, (pos_x, pos_y - offset))
        screen.blit(game_over_text, (pos_x, pos_y + offset))
    
    # Main "GAME OVER" text
    game_over_text = title_font.render("GAME OVER", True, (255, 0, 0))
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 100))

    # Final score
    final_score_text = font.render(f"Punteggio Finale: {score}", True, (255, 255, 255))
    screen.blit(final_score_text, (SCREEN_WIDTH//2 - final_score_text.get_width()//2, SCREEN_HEIGHT//2 - 20))

    # Height reached
    height_km = world_offset / 50  # PIXEL_PER_KM equivalent
    height_text = font.render(f"Altezza Raggiunta: {height_km:.2f} km", True, (255, 255, 255))
    screen.blit(height_text, (SCREEN_WIDTH//2 - height_text.get_width()//2, SCREEN_HEIGHT//2))

    # Instructions with pulsing effect
    pulse_color = int(200 + math.sin(pygame.time.get_ticks() * 0.005) * 55)
    restart_text = font.render("Premi R per riprovare", True, (pulse_color, pulse_color, pulse_color))
    screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 40))
    
    quit_text = font.render("Premi ESC per tornare al menu", True, (180, 180, 180))
    screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, SCREEN_HEIGHT//2 + 80))

def draw_name_input(screen, player_name):
    """Draw the name input screen."""
    screen.fill((30, 30, 60))

    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 16)

    title = title_font.render("NUOVO RECORD!", True, (255, 215, 0))
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))

    prompt = font.render("Inserisci il tuo nome:", True, (255, 255, 255))
    screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 300))

    # Input box
    input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, 350, 300, 40)
    pygame.draw.rect(screen, (255, 255, 255), input_box, 2)

    name_surface = font.render(player_name, True, (255, 255, 255))
    screen.blit(name_surface, (input_box.x + 10, input_box.y + 10))

    instruction = small_font.render("Premi ENTER per confermare", True, (200, 200, 200))
    screen.blit(instruction, (SCREEN_WIDTH//2 - instruction.get_width()//2, 420))

def draw_hud(screen, player, world_offset, current_level, score):
    """Draw the heads-up display during gameplay."""
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 16)
    
    from levels import level_names
    
    # Health
    for i in range(player.max_health):
        x = 10 + i * 30
        y = 10
        if i < player.health:
            pygame.draw.circle(screen, (255, 0, 0), (x + 10, y + 10), 8)
        else:
            pygame.draw.circle(screen, (100, 100, 100), (x + 10, y + 10), 8, 2)

    # Active power-ups
    y_offset = 50
    for powerup_type, time_left in player.active_powerups.items():
        text = small_font.render(f"{powerup_type}: {time_left:.1f}s", True, (255, 255, 0))
        screen.blit(text, (10, y_offset))
        y_offset += 20

    # Height and score
    height_km = world_offset / 50  # PIXEL_PER_KM equivalent
    height_text = font.render(f"Altezza: {height_km:.2f} km", True, (255, 255, 255))
    level_text = font.render(f"Livello: {level_names[current_level]}", True, (255, 255, 255))
    score_text = font.render(f"Punteggio: {score}", True, (255, 255, 255))

    screen.blit(height_text, (10, SCREEN_HEIGHT - 80))
    screen.blit(level_text, (10, SCREEN_HEIGHT - 60))
    screen.blit(score_text, (10, SCREEN_HEIGHT - 40))
