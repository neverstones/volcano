"""
Background rendering system for the volcano game.
"""
import pygame
import math
import random
from volcano.constants import *
from levels import *

def draw_enhanced_background(world_offset, screen):
    """Draw the enhanced background with smooth transitions."""
    km_height = world_offset / PIXEL_PER_KM

    # Smooth transitions between levels
    if km_height < KM_PER_LEVEL[LEVEL_MANTELLO]:
        draw_level_background(LEVEL_MANTELLO, 1.0, world_offset, screen)
    elif km_height < KM_PER_LEVEL[LEVEL_MANTELLO] + 2:
        # Mantello-crosta transition
        transition_progress = (km_height - KM_PER_LEVEL[LEVEL_MANTELLO]) / 2
        transition_progress = max(0, min(1, transition_progress))

        draw_level_background(LEVEL_MANTELLO, 1 - transition_progress, world_offset, screen)
        draw_level_background(LEVEL_CROSTA, transition_progress, world_offset, screen)
        draw_transition_effects(transition_progress, LEVEL_MANTELLO, LEVEL_CROSTA, screen)

    elif km_height < KM_PER_LEVEL[LEVEL_CROSTA]:
        draw_level_background(LEVEL_CROSTA, 1.0, world_offset, screen)
    elif km_height < KM_PER_LEVEL[LEVEL_CROSTA] + 2:
        # Crosta-vulcano transition
        transition_progress = (km_height - KM_PER_LEVEL[LEVEL_CROSTA]) / 2
        transition_progress = max(0, min(1, transition_progress))

        draw_level_background(LEVEL_CROSTA, 1 - transition_progress, world_offset, screen)
        draw_volcano_section(transition_progress, world_offset, km_height, screen)
        draw_transition_effects(transition_progress, LEVEL_CROSTA, LEVEL_VULCANO, screen)

    else:
        # Full volcano section
        draw_volcano_section(1.0, world_offset, km_height, screen)

def draw_level_background(level, alpha, world_offset, screen):
    """Draw background for a specific level with alpha blending."""
    scroll_y = int(world_offset % SCREEN_HEIGHT)

    # Create surface with alpha for transitions
    level_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    if alpha < 1.0:
        level_surface.set_alpha(int(255 * alpha))

    # Draw background color for level
    level_surface.fill(LEVEL_COLORS[level])

    # Add environmental effects for each level
    add_environmental_effects(level_surface, level, world_offset)
    screen.blit(level_surface, (0, 0))

def add_environmental_effects(surface, level, world_offset):
    """Add environmental effects for each level."""
    if level == LEVEL_MANTELLO:
        # Floating magma particles
        time_seed = int(pygame.time.get_ticks() / 1000) % 1000
        offset_seed = int(world_offset / 100) % 100
        
        for i in range(15):
            particle_seed = (time_seed + offset_seed + i * 23) % 1000
            x = (particle_seed % SCREEN_WIDTH)
            y = ((particle_seed + 200) % SCREEN_HEIGHT)
            size = 2 + (particle_seed % 4)
            alpha = 50 + (particle_seed % 101)

            particle_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color_variation = 100 + (particle_seed % 101)
            color = (255, color_variation, 0, alpha)
            pygame.draw.circle(particle_surface, color, (size, size), size)
            surface.blit(particle_surface, (x-size, y-size))

    elif level == LEVEL_CROSTA:
        # Crystals and minerals
        time_seed = int(pygame.time.get_ticks() / 2000) % 1000
        offset_seed = int(world_offset / 150) % 100
        
        for i in range(8):
            crystal_seed = (time_seed + offset_seed + i * 31) % 1000
            x = (crystal_seed % SCREEN_WIDTH)
            y = ((crystal_seed + 300) % SCREEN_HEIGHT)

            # Brilliant crystal
            points = []
            for j in range(6):
                angle = j * math.pi / 3
                radius = 3 + (crystal_seed % 6)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))

            colors = [(100, 200, 255), (200, 255, 100), (255, 200, 100)]
            color = colors[crystal_seed % len(colors)]
            pygame.draw.polygon(surface, color, points)

    elif level == LEVEL_VULCANO:
        # Sparks and embers following conical shape
        base_width = SCREEN_WIDTH * 0.85
        crater_width = SCREEN_WIDTH * 0.25
        time_seed = int(pygame.time.get_ticks() / 800) % 1000
        offset_seed = int(world_offset / 200) % 100
        
        for i in range(20):
            spark_seed = (time_seed + offset_seed + i * 19) % 1000
            y = (spark_seed % SCREEN_HEIGHT)
            height_ratio = (SCREEN_HEIGHT - y) / SCREEN_HEIGHT
            
            current_width = base_width - (base_width - crater_width) * height_ratio
            passage_left = (SCREEN_WIDTH - current_width) / 2
            passage_right = SCREEN_WIDTH - passage_left
            
            placement_choice = (spark_seed + 100) % 100
            if placement_choice < 70:
                x_range = int(passage_right - passage_left)
                if x_range > 0:
                    x = int(passage_left) + ((spark_seed + 200) % x_range)
                else:
                    x = SCREEN_WIDTH // 2
            else:
                wall_positions = [
                    max(0, int(passage_left - 20)),
                    min(SCREEN_WIDTH, int(passage_right + 20))
                ]
                x = wall_positions[(spark_seed + 300) % 2]
                x = max(0, min(SCREEN_WIDTH, x))
            
            size = 1 + (spark_seed % 4)
            spark_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            
            intensity = 0.5 + height_ratio * 0.5
            color = (255, int(255 * intensity), random.randint(0, int(100 * intensity)), 
                    random.randint(100, 255))
            pygame.draw.circle(spark_surface, color, (size, size), size)
            surface.blit(spark_surface, (x-size, y-size))

def draw_transition_effects(progress, from_level, to_level, screen):
    """Draw special effects during level transitions."""
    if from_level == LEVEL_MANTELLO and to_level == LEVEL_CROSTA:
        # Magma solidification effect
        num_effects = int(20 * progress)
        for _ in range(num_effects):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(5, 15)

            color_intensity = 1 - progress
            color = (int(255 * color_intensity), int(100 * color_intensity), 0)

            effect_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surface, (*color, int(100 * progress)), (size, size), size, 2)
            screen.blit(effect_surface, (x-size, y-size))

    elif from_level == LEVEL_CROSTA and to_level == LEVEL_VULCANO:
        # Conveyor belt effect + volcano entrance with widening cracks
        
        # 1. CONVEYOR BELT EFFECT
        conveyor_lines = 8
        current_time = pygame.time.get_ticks()
        
        for i in range(conveyor_lines):
            line_spacing = SCREEN_HEIGHT // conveyor_lines
            base_y = i * line_spacing + (current_time * 0.05) % line_spacing
            
            alpha = int(150 * progress)
            color = (100, 100, 100, alpha)
            
            convergence_factor = progress * 0.3
            
            left_start = 0
            left_end = int(SCREEN_WIDTH * 0.4 + (SCREEN_WIDTH * 0.1 * convergence_factor))
            
            right_start = int(SCREEN_WIDTH * 0.6 - (SCREEN_WIDTH * 0.1 * convergence_factor))
            right_end = SCREEN_WIDTH
            
            belt_surface = pygame.Surface((SCREEN_WIDTH, 4), pygame.SRCALPHA)
            pygame.draw.line(belt_surface, color, (left_start, 2), (left_end, 2), 2)
            pygame.draw.line(belt_surface, color, (right_start, 2), (right_end, 2), 2)
            screen.blit(belt_surface, (0, base_y))

def draw_volcano_section(alpha, world_offset, km_height, screen):
    """Draw the volcano section with fixed zoom and conveyor belt effect."""
    volcano_start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    volcano_end_km = KM_PER_LEVEL[LEVEL_VULCANO]
    volcano_progress = (km_height - volcano_start_km) / (volcano_end_km - volcano_start_km)
    volcano_progress = max(0, min(1, volcano_progress))
    
    # Fixed zoom factor
    zoom_factor = 1.4
    
    # Draw volcano walls normally
    draw_volcano_tile_walls(world_offset, km_height, screen)
    
    # Eruption effects if near crater
    if km_height > KM_PER_LEVEL[LEVEL_VULCANO] * 0.9:
        crater_info = get_crater_info_from_conical_volcano(world_offset)
        from game_states import draw_eruption_effects
        draw_eruption_effects(crater_info, km_height, screen)
    
    # Apply fixed zoom as post-effect
    current_surface = screen.copy()
    
    zoom_width = int(SCREEN_WIDTH * zoom_factor)
    zoom_height = int(SCREEN_HEIGHT * zoom_factor)
    
    scaled_surface = pygame.transform.scale(current_surface, (zoom_width, zoom_height))
    
    center_offset_x = (zoom_width - SCREEN_WIDTH) // 2
    center_offset_y = (zoom_height - SCREEN_HEIGHT) // 2
    
    screen.fill((20, 10, 5))
    
    if (center_offset_x >= 0 and center_offset_y >= 0 and 
        center_offset_x + SCREEN_WIDTH <= zoom_width and 
        center_offset_y + SCREEN_HEIGHT <= zoom_height):
        try:
            center_rect = pygame.Rect(center_offset_x, center_offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)
            final_surface = scaled_surface.subsurface(center_rect)
            screen.blit(final_surface, (0, 0))
        except:
            screen.blit(current_surface, (0, 0))
    else:
        screen.blit(current_surface, (0, 0))

def draw_volcano_tile_walls(world_offset, km_height, screen):
    """Draw volcano walls using PNG tiles that narrow gradually towards the crater."""
    
    # Fill screen with external sky background
    draw_external_sky_background(screen)
    
    volcano_start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    volcano_end_km = KM_PER_LEVEL[LEVEL_VULCANO]
    volcano_progress = (km_height - volcano_start_km) / (volcano_end_km - volcano_start_km)
    volcano_progress = max(0, min(1, volcano_progress))
    
    # Calculate Y offset for conveyor belt effect
    conveyor_offset = int((km_height - volcano_start_km) * 3)
    
    # Wall parameters that narrow (in pixels)
    base_wall_distance = SCREEN_WIDTH - 100
    crater_wall_distance = 4
    tile_size = 32
    
    num_tile_rows = SCREEN_HEIGHT // tile_size + 1
    
    for row in range(num_tile_rows):
        row_height_ratio = row / num_tile_rows
        
        current_wall_distance = base_wall_distance - (base_wall_distance - crater_wall_distance) * row_height_ratio
        
        left_wall_x = (SCREEN_WIDTH - current_wall_distance) / 2
        right_wall_x = left_wall_x + current_wall_distance
        
        y = SCREEN_HEIGHT - (row + 1) * tile_size - (conveyor_offset % (tile_size * 4))
        
        # Determine tile type based on height
        if row_height_ratio < 0.3:
            tile_color = (139, 69, 19)  # Ground/rock
        elif row_height_ratio < 0.7:
            tile_color = (105, 105, 105)  # Normal stone
        elif row_height_ratio < 0.95:
            tile_color = (169, 169, 169)  # Stone wall
        else:
            tile_color = (255, 69, 0)  # Lava near crater
        
        # Draw left wall tiles
        num_left_tiles = max(1, int(left_wall_x / tile_size))
        for tile_x in range(num_left_tiles):
            x = tile_x * tile_size
            if x < left_wall_x and y > -tile_size and y < SCREEN_HEIGHT:
                pygame.draw.rect(screen, tile_color, (x, y, tile_size, tile_size))
        
        # Draw right wall tiles
        start_right_x = int(right_wall_x / tile_size) * tile_size
        num_right_tiles = (SCREEN_WIDTH - start_right_x) // tile_size + 1
        for tile_x in range(num_right_tiles):
            x = start_right_x + tile_x * tile_size
            if x >= right_wall_x and x < SCREEN_WIDTH and y > -tile_size and y < SCREEN_HEIGHT:
                pygame.draw.rect(screen, tile_color, (x, y, tile_size, tile_size))

def draw_external_sky_background(screen):
    """Draw external sky background."""
    # Simple gradient from dark blue to black
    for y in range(SCREEN_HEIGHT):
        progress = y / SCREEN_HEIGHT
        color_value = int(30 * (1 - progress))
        color = (color_value, color_value, color_value + 20)
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
