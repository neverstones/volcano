import logging
import pygame

def log_game_event(message):
    print(f"🌋 {message}")
    logging.info(message)

def _state_to_name(value):
    return {0: "MENU", 1: "PLAYING", 2: "GAME_OVER", 3: "LEADERBOARD", 4: "ENTER_NAME"}.get(value, str(value))

def debug_input_event(ev, prefix="KEYDOWN", game_state=None, enable_debug=True):
    if not enable_debug:
        return
    try:
        key_name = pygame.key.name(ev.key)
    except Exception:
        key_name = str(getattr(ev, 'key', '?'))
    state_name = _state_to_name(game_state) if game_state is not None else "?"
    logging.info(f"[INPUT] {prefix} key={key_name} code={getattr(ev,'key','?')} state={state_name}")
