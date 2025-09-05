# ----------------- Volcano Level Generation (Deterministico) -----------------
import pygame, random, math, sys, json, os
import logging
from datetime import datetime
from game_constants import WIDTH, HEIGHT, TILE_SIZE, KM_PER_LEVEL, LEVEL_VULCANO

def generate_volcano_platforms():
    platforms = []
    platform_types = []
    powerups = []
    collectibles = []
    enemies = []

    platform_width = 100
    start_y = HEIGHT - 50
    x_center = WIDTH // 2 - platform_width // 2

    # Piattaforme fisse: una centrale ogni 80px, più alcune laterali
    for i in range(15):
        y = start_y - i * 80
        # Centrale
        platforms.append(pygame.Rect(x_center, y, platform_width, 16))
        platform_types.append(LEVEL_VULCANO)
        # Laterali
        if i % 3 == 0:
            platforms.append(pygame.Rect(80, y - 40, platform_width, 16))
            platform_types.append(LEVEL_VULCANO)
            platforms.append(pygame.Rect(WIDTH - 180, y - 40, platform_width, 16))
            platform_types.append(LEVEL_VULCANO)

    # Powerup e collectibles fissi
    powerups.append(PowerUp(WIDTH//2, start_y - 7*80 - 30, 'magma_jump'))
    collectibles.append(Collectible(WIDTH//2, start_y - 10*80 - 25))

    return platforms, platform_types, powerups, collectibles, enemies

# ----------------- Volcano Level Drawing -----------------
def draw_volcano_level(surface, platforms, world_offset):
    # Sfondo vulcano
    surface.fill((30, 30, 30))
    # Pareti vulcano
    wall_color = (120, 60, 15)
    pygame.draw.rect(surface, wall_color, (0, 0, 80, HEIGHT))
    pygame.draw.rect(surface, wall_color, (WIDTH-80, 0, 80, HEIGHT))
    # Lava
    pygame.draw.rect(surface, (255, 80, 0), (80, HEIGHT-60, WIDTH-160, 40))
    # Fumo animato
    for i in range(8):
        fx = WIDTH//2 + (i-4)*30 + int(math.sin(pygame.time.get_ticks()/600 + i)*10)
        fy = 60 + i*18 + int(math.cos(pygame.time.get_ticks()/400 + i)*8)
        pygame.draw.circle(surface, (120,120,120,80), (fx, fy), 22)
    # Bagliore cratere
    pygame.draw.ellipse(surface, (255, 120, 0, 80), (WIDTH//2-90, 40, 180, 40))
    # Piattaforme
    for plat in platforms:
        rect = plat.copy()
        rect.y += world_offset
        pygame.draw.rect(surface, (200, 100, 40), rect)