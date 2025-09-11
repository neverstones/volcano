"""
Sistema di salvataggio e gestione punteggi per il gioco Volcano
"""
import json
import os
from datetime import datetime

SCORES_FILE = "volcano_scores.json"

def load_high_scores():
    """Carica i punteggi salvati da file."""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r', encoding='utf-8') as f:
                scores = json.load(f)
                # Assicurati che sia una lista di dizionari con le chiavi corrette
                valid_scores = []
                for score in scores:
                    if isinstance(score, dict) and 'name' in score and 'score' in score and 'date' in score:
                        valid_scores.append(score)
                return valid_scores
    except Exception as e:
        print(f"Errore nel caricamento punteggi: {e}")
    return []

def save_high_scores(scores):
    """Salva i punteggi su file."""
    try:
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio punteggi: {e}")
        return False

def add_score(name, score):
    """Aggiunge un nuovo punteggio alla classifica."""
    scores = load_high_scores()
    
    new_score = {
        'name': name,
        'score': score,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    scores.append(new_score)
    
    # Ordina per punteggio decrescente e mantieni solo i primi 10
    scores.sort(key=lambda x: x['score'], reverse=True)
    scores = scores[:10]
    
    save_high_scores(scores)
    return scores

def get_top_scores(limit=10):
    """Restituisce i migliori punteggi."""
    scores = load_high_scores()
    return scores[:limit]