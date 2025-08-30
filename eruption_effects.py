def draw_eruption_effects(crater_info, km_height):
    """Disegna gli effetti di eruzione usando le informazioni del cratere"""
    crater_left, crater_right, crater_top = crater_info
    
    # Calcola l'intensità dell'eruzione in base alla vicinanza al cratere
    max_height = KM_PER_LEVEL[LEVEL_VULCANO]
    eruption_intensity = min(1.0, (km_height - max_height * 0.9) / (max_height * 0.1))
    
    # Crea una superficie per gli effetti con alpha blending
    effects_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Disegna particelle di lava dal cratere
    num_particles = int(20 * eruption_intensity)
    for _ in range(num_particles):
        x = random.randint(int(crater_left), int(crater_right))
        y = random.randint(int(crater_top), int(crater_top + 100))
        size = random.randint(2, 6)
        alpha = random.randint(100, 200)
        color = (255, random.randint(100, 200), 0, alpha)
        pygame.draw.circle(effects_surface, color, (x, y), size)
    
    # Disegna un bagliore rosso intorno al cratere
    glow_surface = pygame.Surface((crater_right - crater_left, 100), pygame.SRCALPHA)
    glow_color = (255, 50, 0, int(100 * eruption_intensity))
    pygame.draw.rect(glow_surface, glow_color, (0, 0, crater_right - crater_left, 100))
    effects_surface.blit(glow_surface, (crater_left, crater_top))
    
    # Aggiungi colate di lava lungo le pareti
    num_flows = int(6 * eruption_intensity)
    for _ in range(num_flows):
        # Scegli un punto di partenza lungo il cratere
        start_x = random.randint(int(crater_left), int(crater_right))
        start_y = crater_top
        
        # Crea un percorso di lava che scende
        points = [(start_x, start_y)]
        current_x = start_x
        current_y = start_y
        
        for _ in range(random.randint(5, 15)):
            current_x += random.randint(-10, 10)
            current_y += random.randint(10, 20)
            # Mantieni il flusso entro i limiti del vulcano
            current_x = max(crater_left, min(crater_right, current_x))
            points.append((current_x, current_y))
        
        # Disegna il flusso di lava
        if len(points) > 1:
            lava_color = (255, random.randint(50, 150), 0, int(150 * eruption_intensity))
            pygame.draw.lines(effects_surface, lava_color, False, points, 3)
            
            # Aggiungi un bagliore attorno al flusso
            glow_color = (255, 50, 0, int(50 * eruption_intensity))
            pygame.draw.lines(effects_surface, glow_color, False, points, 5)
    
    # Applica gli effetti allo schermo
    screen.blit(effects_surface, (0, 0))
