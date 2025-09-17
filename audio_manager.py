import pygame
import os

class AudioManager:
    def __init__(self, base_path):
        self.sounds = {}
        self.base_path = base_path
        self._load_sounds()

    def _load_sounds(self):
        for key, filename in {
            'jump': 'jumping.wav',
            'bubble': 'bubbling_volcano_lava.wav',
            'erupt': 'erupting_volcano.wav',
            'win': 'winning.wav',
            'powerup': 'powerup.wav',
            'collect': 'collect.wav',
            'lava_hit': 'lava_hit.wav',
            'eruption': 'eruption.wav'
        }.items():
            sound = self._load(filename)
            self.sounds[key] = sound
            print(f"AudioManager: caricato {filename}: {bool(sound)}")

    def _load(self, filename):
        path = os.path.join(self.base_path, filename)
        print(f"AudioManager: provo a caricare {path}")
        if os.path.exists(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"AudioManager: ERRORE nel caricamento {path}: {e}")
        else:
            print(f"AudioManager: file non trovato {path}")
        return None

    def play(self, name):
        print(f"AudioManager: play chiamato per {name}")
        sound = self.sounds.get(name)
        if sound:
            print(f"AudioManager: riproduco suono {name}")
            try:
                sound.play()
                print(f"AudioManager: suono {name} in riproduzione")
            except Exception as e:
                print(f"AudioManager: ERRORE riproduzione {name}: {e}")
        else:
            print(f"AudioManager: suono {name} non trovato")
