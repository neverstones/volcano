"""
Audio system for the volcano game.
"""
import pygame
import math
import os
from constants import AUDIO_FREQUENCY, AUDIO_BUFFER

class AudioManager:
    def play_background_eruption(self, base_path):
        eruption_path = os.path.join(base_path, 'erupting_volcano.wav')
        if os.path.exists(eruption_path):
            try:
                pygame.mixer.music.load(eruption_path)
                pygame.mixer.music.play(-1)
                print(f"DEBUG: erupting_volcano.wav in loop")
            except Exception as e:
                print(f"DEBUG: errore riproduzione erupting_volcano.wav: {e}")
        else:
            print(f"DEBUG: erupting_volcano.wav non trovato")
    def play_background_lava(self, base_path):
        lava_path = os.path.join(base_path, 'bubbling_volcano_lava.wav')
        if os.path.exists(lava_path):
            try:
                pygame.mixer.music.load(lava_path)
                pygame.mixer.music.play(-1)
                print(f"DEBUG: bubbling_volcano_lava.wav in loop")
            except Exception as e:
                print(f"DEBUG: errore riproduzione bubbling_volcano_lava.wav: {e}")
        else:
            print(f"DEBUG: bubbling_volcano_lava.wav non trovato")

    def stop_background(self):
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"DEBUG: errore stop musica: {e}")
    def __init__(self, base_path):
        self.sounds = {}
        self.music_playing = False
        self.audio_available = pygame.mixer is not None
        if self.audio_available:
            try:
                # Carica fire-whoosh.wav come suono del salto automatico
                fire_whoosh_path = os.path.join(base_path, 'fire-whoosh.wav')
                if os.path.exists(fire_whoosh_path):
                    self.sounds['jump'] = pygame.mixer.Sound(fire_whoosh_path)
                    self.sounds['jump'].set_volume(0.35)  # Volume abbassato
                    print(f"DEBUG: fire-whoosh.wav caricato correttamente: {fire_whoosh_path} (volume 0.35)")
                else:
                    print(f"DEBUG: fire-whoosh.wav non trovato, uso suono procedurale")
                    self.sounds['jump'] = self.create_tone(300, 0.1)
                # Carica altri suoni se disponibili, altrimenti procedurali
                self.sounds['powerup'] = self.create_tone(500, 0.3)
                self.sounds['collect'] = self.create_tone(800, 0.2)
                self.sounds['lava_hit'] = self.create_tone(150, 0.5)
                self.sounds['eruption'] = self.create_tone(100, 1.0)
            except Exception as e:
                print(f"Audio non disponibile: {e}")
                self.audio_available = False
    def play_background_wind(self, base_path):
        wind_path = os.path.join(base_path, 'wind_blowing.wav')
        if os.path.exists(wind_path):
            try:
                pygame.mixer.music.load(wind_path)
                pygame.mixer.music.play(-1)
                print(f"DEBUG: wind_blowing.wav in loop")
            except Exception as e:
                print(f"DEBUG: errore riproduzione wind_blowing.wav: {e}")
        else:
            print(f"DEBUG: wind_blowing.wav non trovato")

    def create_procedural_sounds(self):
        # Crea suoni procedurali usando onde sinusoidali
        self.sounds['jump'] = self.create_tone(300, 0.1)
        self.sounds['powerup'] = self.create_tone(500, 0.3)
        self.sounds['collect'] = self.create_tone(800, 0.2)
        self.sounds['lava_hit'] = self.create_tone(150, 0.5)
        self.sounds['eruption'] = self.create_tone(100, 1.0)

    def create_tone(self, frequency, duration):
        try:
            import numpy as np
            sample_rate = AUDIO_FREQUENCY
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = 4096 * math.sin(2 * math.pi * frequency * i / sample_rate)
                arr.append([int(wave), int(wave)])
            
            # Usa numpy se disponibile, altrimenti disabilita audio
            arr_np = np.array(arr, dtype=np.int16)
            sound = pygame.sndarray.make_sound(arr_np)
            return sound
        except ImportError:
            # Se numpy non è disponibile, crea un suono silenzioso
            return pygame.mixer.Sound(buffer=bytes(1024))
        except Exception:
            # Per qualsiasi altro errore, ritorna un suono silenzioso
            return pygame.mixer.Sound(buffer=bytes(1024))

    def play(self, sound_name):
        if self.audio_available and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Errore riproduzione suono '{sound_name}': {e}")
