# volcano_cone_map.py
# Generatore di mappa 2D per un vulcano a cono con tile, con pareti che si stringono man mano che si sale.

def generate_cone_map(width_tiles=31, height_tiles=60, min_width=5):
    """
    Genera una mappa 2D (lista di stringhe) di un vulcano a cono.
    width_tiles: larghezza massima in tile (base del vulcano)
    height_tiles: altezza della mappa in tile
    min_width: larghezza minima in tile (cratere)
    """
    cone_map = []
    for y in range(height_tiles):
        # Calcola la larghezza attuale del cono a questa altezza
        t = y / (height_tiles-1)
        curr_width = int(width_tiles * (1-t) + min_width * t)
        left_wall = (width_tiles - curr_width) // 2
        right_wall = left_wall + curr_width - 1
        row = []
        for x in range(width_tiles):
            if x == left_wall or x == right_wall:
                row.append('x')  # Parete
            elif left_wall < x < right_wall:
                row.append('o')  # Spazio libero
            else:
                row.append(' ')  # Esterno
        cone_map.append(''.join(row))
    return cone_map

if __name__ == "__main__":
    mappa = generate_cone_map()
    for riga in mappa:
        print(riga)
