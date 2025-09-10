import json
import os
from datetime import datetime


class ScoreSystem:
    def __init__(self, filename="volcano_scores.json"):
        self.filename = filename
        self.scores = self.load_scores()
        
    def load_scores(self):
        """Carica i punteggi dal file JSON."""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_scores(self):
        """Salva i punteggi nel file JSON."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Errore nel salvare i punteggi: {e}")
    
    def add_score(self, score, level_reached=0, collectibles_collected=0):
        """Aggiunge un nuovo punteggio."""
        score_entry = {
            'score': score,
            'level_reached': level_reached,
            'collectibles_collected': collectibles_collected,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.scores.append(score_entry)
        
        # Ordina per punteggio decrescente
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Mantieni solo i top 10
        self.scores = self.scores[:10]
        
        self.save_scores()
        
        return self.get_rank(score)
    
    def get_rank(self, score):
        """Restituisce la posizione del punteggio nella classifica."""
        for i, entry in enumerate(self.scores):
            if entry['score'] == score:
                return i + 1
        return len(self.scores) + 1
    
    def get_top_scores(self, limit=10):
        """Restituisce i migliori punteggi."""
        return self.scores[:limit]
    
    def get_best_score(self):
        """Restituisce il miglior punteggio."""
        if self.scores:
            return self.scores[0]['score']
        return 0
    
    def clear_scores(self):
        """Cancella tutti i punteggi."""
        self.scores = []
        self.save_scores()
