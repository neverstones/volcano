import pygame
import os

class AudioManager:
    def __init__(self, base_path):
        self.sounds = {}
        self.base_path = base_path
        self._load_sounds()
        # Carica punch.wav una sola volta
        punch_path = os.path.join(self.base_path, 'punch.wav')
        print(f"DEBUG: path usato per punch.wav: {punch_path}")
        if os.path.exists(punch_path):
            try:
                self.sounds['enemy_hit'] = pygame.mixer.Sound(punch_path)
                self.sounds['enemy_hit'].set_volume(0.7)
                print(f"DEBUG: punch.wav caricato correttamente: {punch_path}")
            except Exception as e:
                print(f"DEBUG: Errore caricamento punch.wav: {e}")
        else:
            print(f"DEBUG: punch.wav non trovato in {punch_path}")
        print(f"DEBUG: suoni caricati dopo punch: {list(self.sounds.keys())}")
        if 'enemy_hit' not in self.sounds:
            print("ATTENZIONE: punch.wav NON caricato! Nessun suono per collisione minerale.")

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
        if name == 'enemy_hit':
            sound = self.sounds.get('enemy_hit')
            if sound:
                sound.play()
                print(f"DEBUG: punch.wav riprodotto per enemy_hit.")
            else:
                print(f"DEBUG: punch.wav non caricato.")
            return
        sound = self.sounds.get(name)
        if sound:
            print(f"AudioManager: riproduco suono {name}")
            try:
                sound.play()
                print(f"AudioManager: suono {name} in riproduzione")
            except Exception as e:
                print(f"AudioManager: ERRORE riproduzione {name}: {e}")
        else:
            print(f"AudioManager: suono {name} non trovato.")
