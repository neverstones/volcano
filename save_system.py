import json, os
from datetime import datetime
from constants import SAVE_FILE

def load_scores():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Errore caricamento punteggi: {e}")
    return []

def save_score(name, score, height_km):
    scores = load_scores()
    scores.append({
        'name': name,
        'score': score,
        'height': height_km,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    scores.sort(key=lambda x: x['score'], reverse=True)
    scores = scores[:10]
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except Exception as e:
        print(f"Errore salvataggio punteggi: {e}")
    return scores
