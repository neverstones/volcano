import pygame
from game_constants import WIDTH, HEIGHT, KM_PER_LEVEL, LEVEL_VULCANO, LEVEL_CROSTA, PIXEL_PER_KM, VOLCANO_MAP, VOLCANO_MAP_HEIGHT_PX, TILE_SIZE

def create_static_platforms():
    platforms = []
    platform_types = []
    powerups = []
    collectibles = []
    enemies = []
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
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
                platform_types.append(LEVEL_CROSTA)  # esempio, puoi migliorare la logica
            else:
                col += 1
    # powerups, collectibles, enemies: logica da aggiungere se serve
    return platforms, platform_types, powerups, collectibles, enemies

def build_conical_volcano_platforms():
    # ...estrai la logica da riseup.py...
    platforms = []
    base_width = WIDTH * 0.65
    crater_width = WIDTH * 0.15
    start_km = KM_PER_LEVEL[LEVEL_CROSTA]
    start_px = start_km * PIXEL_PER_KM
    map_top_world_y = (HEIGHT - VOLCANO_MAP_HEIGHT_PX) - start_px
    platform_spacing = 90
    num_levels = int(VOLCANO_MAP_HEIGHT_PX / platform_spacing)
    for i in range(num_levels):
        height_ratio = i / num_levels
        y_world = map_top_world_y + (VOLCANO_MAP_HEIGHT_PX - i * platform_spacing)
        current_passage_width = base_width - (base_width - crater_width) * height_ratio
        passage_left = (WIDTH - current_passage_width) / 2
        passage_right = WIDTH - passage_left
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
    crater_platform_y = map_top_world_y + VOLCANO_MAP_HEIGHT_PX - 150
    crater_passage_width = crater_width + 40
    crater_platform_x = (WIDTH - 80) / 2
    crater_platform = pygame.Rect(crater_platform_x, crater_platform_y, 80, 12)
    platforms.append(crater_platform)
    return platforms

def check_platform_collision(player, platforms, world_offset):
    # ...implementazione da riseup.py...
    # Qui va la logica di collisione piattaforme
    # Placeholder: return False, None
    return False, None

def check_crater_entry(player, world_offset):
    # ...implementazione da riseup.py...
    # Qui va la logica di check_crater_entry
    # Placeholder: return False
    return False

def get_crater_info_from_conical_volcano(world_offset):
    # ...implementazione da riseup.py...
    # Qui va la logica di get_crater_info_from_conical_volcano
    # Placeholder: return 0, 0, 0
    return 0, 0, 0

def check_conical_volcano_walls_collision(player, world_offset):
    # ...implementazione da riseup.py...
    # Qui va la logica di check_conical_volcano_walls_collision
    # Placeholder: return False
    return False

def check_volcano_tile_collision(player, world_offset):
    # ...implementazione da riseup.py...
    # Qui va la logica di check_volcano_tile_collision
    # Placeholder: return False, None
    return False, None
