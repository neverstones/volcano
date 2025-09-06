"""
Eruption effects drawing for the volcano game.
"""
import pygame
import math
from constants import *

# -------------------------------
# Effetti grafici (helper interni)
# -------------------------------
def _draw_lava_column(surface, crater_info, eruption_intensity, wave, current_time):
    crater_left, crater_right, crater_top = crater_info
    crater_width = crater_right - crater_left
    crater_center = (crater_left + crater_right) // 2

    column_height = int(200 * eruption_intensity * wave)
    column_points = []
    base_width = crater_width * 0.7
    
    for y in range(column_height, 0, -10):
        progress = y / column_height
        width = base_width * (1 - progress * 0.7)
        wobble = math.sin(current_time * 0.005 + y * 0.1) * (20 * progress)
        left = crater_center - width/2 + wobble
        right = crater_center + width/2 + wobble
        column_points.append((left, crater_top - y))
        column_points.append((right, crater_top - y))

    if len(column_points) >= 4:
        for i in range(0, len(column_points) - 2, 2):
            points = [column_points[i], column_points[i+1],
                      column_points[i+3], column_points[i+2]]
            progress = 1 - (i / len(column_points))
            alpha = int(200 * progress * eruption_intensity)
            color = (255, int(150 * progress + 50), 0, alpha)
            pygame.draw.polygon(surface, color, points)


def _draw_lava_particles(surface, crater_info, eruption_intensity, wave, current_time):
    crater_left, crater_right, crater_top = crater_info
    crater_center = (crater_left + crater_right) // 2

    num_particles = int(40 * eruption_intensity * wave)
    time_seed = int(current_time / 100)

    for i in range(num_particles):
        particle_seed = (i + time_seed) * 37
        angle = (particle_seed % 314) / 100.0
        distance = ((particle_seed % 150)) * wave

        x = crater_center + math.cos(angle) * distance
        y = crater_top - math.sin(angle) * distance - ((particle_seed % 50))
        size = 3 + (particle_seed % 6)
        alpha = int((150 + (particle_seed % 105)) * (1 - distance/200))
        color_variation = 150 + (particle_seed % 50)
        color = (255, color_variation, 0, alpha)

        glow_size = size * 2
        glow_alpha = alpha // 2
        glow_color = (255, 100, 0, glow_alpha)
        pygame.draw.circle(surface, glow_color, (int(x), int(y)), glow_size)
        pygame.draw.circle(surface, color, (int(x), int(y)), size)


def _draw_lava_flows(surface, crater_info, eruption_intensity, current_time):
    crater_left, crater_right, crater_top = crater_info
    crater_width = crater_right - crater_left
    crater_center = (crater_left + crater_right) // 2

    num_flows = int(8 * eruption_intensity)
    for i in range(num_flows):
        angle = (i / num_flows) * math.pi
        start_x = crater_center + math.cos(angle) * crater_width/2
        start_y = crater_top

        points = [(start_x, start_y)]
        current_x, current_y = start_x, start_y
        flow_steps = 8 + (i * 3) % 13
        max_flow_length = 100

        for step in range(flow_steps):
            if current_y - crater_top > max_flow_length:
                break
            progress = step / 20
            current_x += math.sin(current_time * 0.001 + progress * 10) * 8
            current_y += 15 - progress * 5
            current_x = max(crater_left - 50, min(crater_right + 50, current_x))
            points.append((current_x, current_y))

        if len(points) > 1:
            pulse = (math.sin(current_time * 0.004 + i) * 0.3 + 0.7)
            for thickness in range(6, 0, -2):
                progress = thickness / 6
                alpha = int(200 * progress * eruption_intensity * pulse)
                color = (255, int(100 * progress + 50), 0, alpha)
                pygame.draw.lines(surface, color, False, points, thickness)


def _draw_crater_glow(surface, crater_info, eruption_intensity, wave):
    crater_left, crater_right, crater_top = crater_info
    crater_width = crater_right - crater_left

    crater_glow = pygame.Surface((crater_width + 100, 150), pygame.SRCALPHA)
    for i in range(3):
        glow_alpha = int(100 * eruption_intensity * wave * (3-i)/3)
        glow_color = (255, 50, 0, glow_alpha)
        glow_rect = pygame.Rect(50-i*20, 50-i*20, crater_width+i*40, 100+i*40)
        pygame.draw.ellipse(crater_glow, glow_color, glow_rect)
    surface.blit(crater_glow, (crater_left-50, crater_top-50))

# -------------------------------
# Funzione principale
# -------------------------------
def draw_eruption_effects(crater_info, km_height, screen):
    crater_left, crater_right, crater_top = crater_info
    max_height = KM_PER_LEVEL[LEVEL_VULCANO]

    eruption_intensity = min(1.0, (km_height - max_height * 0.9) / (max_height * 0.1))
    current_time = pygame.time.get_ticks()
    wave = math.sin(current_time * 0.003) * 0.3 + 0.7

    effects_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    _draw_lava_column(effects_surface, crater_info, eruption_intensity, wave, current_time)
    _draw_lava_particles(effects_surface, crater_info, eruption_intensity, wave, current_time)
    _draw_lava_flows(effects_surface, crater_info, eruption_intensity, current_time)
    _draw_crater_glow(effects_surface, crater_info, eruption_intensity, wave)

    screen.blit(effects_surface, (0, 0))
