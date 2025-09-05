import pygame, math


class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.audio_available = pygame.mixer is not None
        if self.audio_available:
            try:
                # Crea suoni procedurali se non ci sono file audio
                self.create_procedural_sounds()
            except Exception as e:
                print(f"Audio non disponibile: {e}")
                self.audio_available = False

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
            sample_rate = 22050
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

audio = AudioManager()