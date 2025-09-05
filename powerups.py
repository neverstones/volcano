# ----------------- Volcano Level Generation (Deterministico) -----------------
import pygame, random, math, sys, json, os
import logging
from datetime import datetime
from game_constants import WIDTH, HEIGHT, TILE_SIZE, KM_PER_LEVEL, LEVEL_VULCANO


# ----------------- Power-ups -----------------
class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.collected = False
        self.radius = 20
        self.animation_time = 0
        self.effect_duration = 5.0  # secondi

        # Tipi di power-up vulcanologici
        self.types = {
            'thermal_boost': {'color': (255, 140, 0), 'effect': 'speed'},
            'magma_jump': {'color': (255, 0, 0), 'effect': 'jump'},
            'gas_shield': {'color': (0, 255, 255), 'effect': 'shield'},
            'volcanic_time': {'color': (255, 255, 0), 'effect': 'slow_time'}
        }

    def update(self, dt):
        self.animation_time += dt * 3

    def draw(self, surface, world_offset):
        if self.collected:
            return

        screen_y = self.y + world_offset
        if -50 < screen_y < HEIGHT + 50:
            # Animazione pulsante
            pulse = math.sin(self.animation_time) * 0.3 + 1.0
            radius = int(self.radius * pulse)

            color = self.types[self.type]['color']

            # Bagliore esterno
            glow_surface = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, 50), (radius*2, radius*2), radius*2)
            surface.blit(glow_surface, (self.x - radius*2, screen_y - radius*2))

            # Power-up principale
            pygame.draw.circle(surface, color, (int(self.x), int(screen_y)), radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(screen_y)), radius, 3)

            # Icona del power-up
            icon_color = (255, 255, 255)
            if self.type == 'thermal_boost':
                # Freccia verso l'alto
                points = [(self.x, screen_y-8), (self.x-6, screen_y+4), (self.x+6, screen_y+4)]
                pygame.draw.polygon(surface, icon_color, points)
            elif self.type == 'magma_jump':
                # Doppia freccia
                pygame.draw.polygon(surface, icon_color, [(self.x, screen_y-10), (self.x-4, screen_y-2), (self.x+4, screen_y-2)])
                pygame.draw.polygon(surface, icon_color, [(self.x, screen_y-2), (self.x-4, screen_y+6), (self.x+4, screen_y+6)])
            elif self.type == 'gas_shield':
                # Cerchio di protezione
                pygame.draw.circle(surface, icon_color, (int(self.x), int(screen_y)), 8, 2)
            elif self.type == 'volcanic_time':
                # Orologio
                pygame.draw.circle(surface, icon_color, (int(self.x), int(screen_y)), 6, 2)
                pygame.draw.line(surface, icon_color, (self.x, screen_y), (self.x, screen_y-4), 2)

    def check_collision(self, player):
        if self.collected:
            return False
        distance = math.hypot(player.x - self.x, player.y - self.y)
        return distance < (self.radius + player.radius)