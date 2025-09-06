"""
Levels and volcano map system for the volcano game.
"""
import pygame
import math
from constants import *

# Level names and configuration
level_names = ["Mantello", "Crosta Terrestre", "Vulcano"]

# Tile size for the volcano map
TILE_SIZE = 32

# Volcano map configuration
PIXEL_PER_KM = 50

# Volcano static map ('x' = solid barrier, 'o' = free space)
VOLCANO_MAP = [
    "xxxxxxxxxxxxxxxxxxxoooooooooooooooxxxxxxxxxxxxxxxxxxx",  # Cratere stretto in cima
    "xxxxxxxxxxxxxxxxxxoooooooooooooooooxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxoooooooooooooooooooxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxoooooooooooooooooooooxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxoooooooooooooooooooooooxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxoooooooooooooooooooooooooxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxoooooooooooooooooooooooooooxxxxxxxxxxxxx",
    "xxxxxxxxxxxxoooooooooooooooooooooooooooooxxxxxxxxxxxx",
    "xxxxxxxxxxxoooooooooooooooooooooooooooooooxxxxxxxxxxx",
    "xxxxxxxxxxoooooooooooooooooooooooooooooooooxxxxxxxxxx",
    "xxxxxxxxxoooooooooooooooooooooooooooooooooooxxxxxxxxx",
    "xxxxxxxxoooooooooooooooooooooooooooooooooooooxxxxxxxx",
    "xxxxxxxoooooooooooooooooooooooooooooooooooooooxxxxxxx",
    "xxxxxxoooooooooooooooooooooooooooooooooooooooooxxxxxx",
    "xxxxxoooooooooooooooooooooooooooooooooooooooooooxxxxx",
    "xxxxoooooooooooooooooooooooooooooooooooooooooooooxxxx",
    "xxxoooooooooooooooooooooooooooooooooooooooooooooooxxx",
    "xxoooooooooooooooooooooooooooooooooooooooooooooooooxx",
    "xooooooooooooooooooooooooooooooooooooooooooooooooooox",
    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Base larga del vulcano
    "xxxxxxxxxxxxxxxxxxxxoooooooooooooxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxoooooooooooxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxoooooooooxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxoooooooxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxoooooxxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxxoooxxxxxxxxxxxxxxxxxxxxxxxxx",
    "xxxxxxxxxxxxxxxxxxxxxxxxxooxxxxxxxxxxxxxxxxxxxxxxxxxxx",
]

# Calculate map dimensions
VOLCANO_MAP_HEIGHT_PX = len(VOLCANO_MAP) * TILE_SIZE
VOLCANO_MAP_WIDTH_PX = len(VOLCANO_MAP[0]) * TILE_SIZE

def get_volcano_collision_rects():
    """Generate solid rectangles (barriers) from the volcano static map."""
    rects = []
    for row_idx, row in enumerate(VOLCANO_MAP):
        for col_idx, ch in enumerate(row):
            if ch == 'x':
                x = col_idx * TILE_SIZE
                y = (len(VOLCANO_MAP) - 1 - row_idx) * TILE_SIZE  # 0 at bottom
                rects.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
    return rects

VOLCANO_COLLISION_RECTS = get_volcano_collision_rects()

def build_volcano_platforms():
    """Create horizontal platforms on the upper surfaces of 'x' blocks."""
    platforms = []
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (SCREEN_HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    rows = len(VOLCANO_MAP)
    cols = len(VOLCANO_MAP[0])

    for row_idx in range(rows):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        col = 0
        while col < cols:
            ch = row[col]
            above_open = (row_idx == 0) or (VOLCANO_MAP[row_idx-1][col] == 'o')
            if ch == 'x' and above_open:
                start_col = col
                while col < cols and row[col] == 'x' and ((row_idx == 0) or (VOLCANO_MAP[row_idx-1][col] == 'o')):
                    col += 1
                width = (col - start_col) * TILE_SIZE
                x_world = start_col * TILE_SIZE
                platforms.append(pygame.Rect(x_world, y_world, width, 12))
            else:
                col += 1
    return platforms

def build_conical_volcano_platforms():
    """Create invisible platforms that follow the conical shape of the volcano."""
    platforms = []
    
    # Conical volcano parameters
    base_width = SCREEN_WIDTH * 0.65
    crater_width = SCREEN_WIDTH * 0.15
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    
    map_top_world_y = (SCREEN_HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    
    platform_spacing = 90
    num_levels = int(VOLCANO_MAP_HEIGHT_PX / platform_spacing)
    
    for i in range(num_levels):
        height_ratio = i / num_levels
        y_world = map_top_world_y + (VOLCANO_MAP_HEIGHT_PX - i * platform_spacing)
        
        current_passage_width = base_width - (base_width - crater_width) * height_ratio
        passage_left = (SCREEN_WIDTH - current_passage_width) / 2
        passage_right = SCREEN_WIDTH - passage_left
        
        platform_width = min(70, current_passage_width * 0.4)
        passage_usable = current_passage_width - platform_width - 20
        
        if passage_usable > 0 and current_passage_width > 50:
            if current_passage_width > 200:
                num_platforms_at_level = 3
            elif current_passage_width > 120:
                num_platforms_at_level = 2
            else:
                num_platforms_at_level = 1
            
            for j in range(num_platforms_at_level):
                if num_platforms_at_level == 1:
                    x = (passage_left + passage_right) / 2 - platform_width / 2
                else:
                    spacing = passage_usable / (num_platforms_at_level - 1) if num_platforms_at_level > 1 else 0
                    x = passage_left + 10 + j * spacing
                
                x = max(passage_left + 10, min(passage_right - platform_width - 10, x))
                platform = pygame.Rect(x, y_world, platform_width, 12)
                platforms.append(platform)
    
    # Special platform near crater
    crater_platform_y = map_top_world_y + VOLCANO_MAP_HEIGHT_PX - 150
    crater_platform_x = (SCREEN_WIDTH - 80) / 2
    crater_platform = pygame.Rect(crater_platform_x, crater_platform_y, 80, 12)
    platforms.append(crater_platform)
    
    return platforms

def get_crater_info_from_conical_volcano(world_offset):
    """Return (crater_left, crater_right, crater_top) in screen coordinates."""
    crater_width = SCREEN_WIDTH * 0.15
    crater_left = (SCREEN_WIDTH - crater_width) / 2
    crater_right = SCREEN_WIDTH - crater_left
    crater_top = 80
    
    return int(crater_left), int(crater_right), int(crater_top)

def check_crater_entry(player, y_offset):
    """Check if the player has entered the volcano crater."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (SCREEN_HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    
    crater_world_y = map_top_world_y + VOLCANO_MAP_HEIGHT_PX - 50
    crater_width = SCREEN_WIDTH * 0.15
    crater_left = (SCREEN_WIDTH - crater_width) / 2
    crater_right = crater_left + crater_width
    
    player_world_y = player.y
    player_center_x = player.x + player.radius
    
    is_in_crater_vertically = player_world_y <= crater_world_y
    is_in_crater_horizontally = crater_left <= player_center_x <= crater_right
    
    return is_in_crater_vertically and is_in_crater_horizontally

def check_conical_volcano_walls_collision(ball, world_offset):
    """Check that the ball stays within the volcano passage."""
    base_width = SCREEN_WIDTH * 0.65
    crater_width = SCREEN_WIDTH * 0.15
    
    volcano_start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    volcano_end_km = KM_PER_LEVEL[LEVEL_VULCANO]
    current_km = world_offset / PIXEL_PER_KM
    
    if current_km < volcano_start_km or current_km > volcano_end_km:
        return False
    
    volcano_progress = (current_km - volcano_start_km) / (volcano_end_km - volcano_start_km)
    volcano_progress = max(0, min(1, volcano_progress))
    
    current_passage_width = base_width - (base_width - crater_width) * volcano_progress
    passage_left = (SCREEN_WIDTH - current_passage_width) / 2
    passage_right = SCREEN_WIDTH - passage_left
    
    collision = False
    
    if ball.x - ball.radius < passage_left:
        ball.x = passage_left + ball.radius + 2
        collision = True
    elif ball.x + ball.radius > passage_right:
        ball.x = passage_right - ball.radius - 2
        collision = True
    
    return collision

def draw_volcano_static(surface, world_offset):
    """Draw the volcano section based on static map."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (SCREEN_HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    first_visible_row = max(0, int((0 - world_offset - map_top_world_y) // TILE_SIZE))
    last_visible_row = min(len(VOLCANO_MAP)-1, int((SCREEN_HEIGHT - world_offset - map_top_world_y) // TILE_SIZE) + 1)

    for row_idx in range(first_visible_row, last_visible_row + 1):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        y_screen = int(y_world + world_offset)
        for col_idx, ch in enumerate(row):
            if ch == 'x':
                x_world = col_idx * TILE_SIZE
                x_screen = int(x_world)
                color = (90, 45, 10)
                pygame.draw.rect(surface, color, (x_screen, y_screen, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(surface, (120, 60, 15), (x_screen+2, y_screen+2, TILE_SIZE-4, TILE_SIZE-4), 1)

def check_volcano_tile_collision(ball, world_offset):
    """Check collision with 'x' blocks in the volcano map."""
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (SCREEN_HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px

    landed = False
    landing_y = None
    margin = 8

    player_left = int((ball.x - ball.radius) // TILE_SIZE)
    player_right = int((ball.x + ball.radius) // TILE_SIZE) + 1
    player_world_y = ball.y
    player_row = int((player_world_y - map_top_world_y) // TILE_SIZE)

    row_start = max(0, player_row - 2)
    row_end = min(len(VOLCANO_MAP)-1, player_row + 2)
    col_start = max(0, player_left - 1)
    col_end = min(len(VOLCANO_MAP[0])-1, player_right + 1)

    for row_idx in range(row_start, row_end + 1):
        row = VOLCANO_MAP[row_idx]
        y_world = map_top_world_y + row_idx * TILE_SIZE
        tile_top = y_world
        tile_bottom = y_world + TILE_SIZE
        for col_idx in range(col_start, col_end + 1):
            if row[col_idx] != 'x':
                continue
            x_world = col_idx * TILE_SIZE
            tile_left = x_world
            tile_right = x_world + TILE_SIZE

            if (ball.x + ball.radius) > tile_left and (ball.x - ball.radius) < tile_right:
                if ball.vy >= 0:  # Landing from above
                    if (ball.y + ball.radius) >= tile_top - margin and (ball.y - ball.radius) < tile_top:
                        landed = True
                        landing_y = tile_top - ball.radius
                        return landed, landing_y

    return landed, landing_y

# Initialize volcano platforms
VOLCANO_PLATFORMS = build_conical_volcano_platforms()
