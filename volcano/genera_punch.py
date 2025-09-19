import numpy as np
import wave

sample_rate = 44100
duration = 0.15  # secondi
frequency = 330  # Hz (buzz medio)
volume = 0.7

t = np.linspace(0, duration, int(sample_rate * duration), False)
# Semplice onda quadra per effetto punch
signal = (np.sign(np.sin(2 * np.pi * frequency * t)) * volume * 32767).astype(np.int16)

with wave.open("./audio/punch.wav", "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sample_rate)
    f.writeframes(signal.tobytes())

print("File punch.wav generato!")