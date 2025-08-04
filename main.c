// Gioco "Risalita del magma" - Condotto vulcanico
#include <SDL.h>
#include <stdio.h>
#include <stdbool.h>
#include <math.h>

#define WIDTH 800
#define HEIGHT 600
#define FPS 60

// Stati del gioco
typedef enum {
    STATO_MENU,
    STATO_GIOCO,
    STATO_ERUZIONE,
    STATO_GAME_OVER,
    STATO_VITTORIA
} StatoGioco;

// Struttura magma
typedef struct {
    float y;
    float temperatura;
    int clic_necessari;
    int clic_attuali;
} Magma;


typedef struct {
    int x, y;
    int lunghezza;  // lunghezza della faglia
    bool attiva;
} Faglia;

typedef struct {
    int x, y;
    float velocita_y;  // velocità di salita delle bolle
    bool usato;
} Gas;

typedef struct {
    int x, y;
    bool attiva;
} Acqua;

// Nuove strutture per insidie e fasi ambientali
typedef struct {
    int x, y;
    int larghezza, altezza;
    bool attiva;
    int tipo; // 0=cristallizzazione/minerali, 1=raffreddamento rapido, 2=gas che si espandono
    float viscosita_aggiunta; // Quanto rallenta il magma
} Insidia;

typedef enum {
    FASE_MANTELLO,      // Profondità massima
    FASE_CROSTA,        // Zona intermedia
    FASE_CONDOTTO       // Superficie
} FaseAmbiente;

int mappa_offset = 0;
float telecamera_velocita = 2.0f;

// Variabili per animazioni fluide
float magma_y_smooth = 1500.0f;  // Posizione smooth del magma
float camera_offset_smooth = 0.0f;  // Offset camera smooth
bool condotto_scavato[3000];  // Array per tracciare le zone scavate (fino a 3000 pixel di profondità)
int altezza_condotto_scavato = 0; // Quanto condotto è stato scavato dal magma

// Funzione semplice per disegnare caratteri bitmap
void disegna_carattere(SDL_Renderer* renderer, char c, int x, int y, int size) {
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    
    switch(c) {
        case 'R':
            // Lettera R
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i); // linea sinistra
                if(i < size/2) SDL_RenderDrawPoint(renderer, x + size/2, y + i); // linea destra superiore
                if(i == 0 || i == size/2 - 1) {
                    for(int j = 0; j <= size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i); // linee orizzontali
                }
                if(i > size/2) SDL_RenderDrawPoint(renderer, x + (i - size/2), y + i); // diagonale
            }
            break;
        case 'I':
            // Lettera I
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x + size/4, y + i); // linea centrale
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case 'S':
            // Lettera S
            for(int i = 0; i < size; i++) {
                if(i == 0 || i == size/2 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
                if(i < size/2) SDL_RenderDrawPoint(renderer, x, y + i);
                else SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
            }
            break;
        case 'A':
            // Lettera A
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                SDL_RenderDrawPoint(renderer, x + size/2, y + i);
                if(i == 0 || i == size/2) {
                    for(int j = 0; j <= size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case 'L':
            // Lettera L
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                if(i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case 'T':
            // Lettera T
            for(int i = 0; i < size; i++) {
                if(i == 0) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
                SDL_RenderDrawPoint(renderer, x + size/4, y + i);
            }
            break;
        case 'D':
            // Lettera D
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2 - 1; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
                if(i > 0 && i < size - 1) SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
            }
            break;
        case 'E':
            // Lettera E
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                if(i == 0 || i == size/2 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case 'M':
            // Lettera M
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                SDL_RenderDrawPoint(renderer, x + size/2, y + i);
                if(i < size/2) {
                    SDL_RenderDrawPoint(renderer, x + i/2, y + i);
                    SDL_RenderDrawPoint(renderer, x + size/2 - i/2, y + i);
                }
            }
            break;
        case 'G':
            // Lettera G
            for(int i = 0; i < size; i++) {
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
                SDL_RenderDrawPoint(renderer, x, y + i);
                if(i > size/2) SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
                if(i == size/2) {
                    for(int j = size/4; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case 'O':
            // Lettera O
            for(int i = 0; i < size; i++) {
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                } else {
                    SDL_RenderDrawPoint(renderer, x, y + i);
                    SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
                }
            }
            break;
        case 'V':
            // Lettera V
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x + i/3, y + i);
                SDL_RenderDrawPoint(renderer, x + size/2 - 1 - i/3, y + i);
            }
            break;
        case 'N':
            // Lettera N
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
                SDL_RenderDrawPoint(renderer, x + i/2, y + i);
            }
            break;
        case 'C':
            // Lettera C
            for(int i = 0; i < size; i++) {
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                } else {
                    SDL_RenderDrawPoint(renderer, x, y + i);
                }
            }
            break;
        case 'H':
            // Lettera H
            for(int i = 0; i < size; i++) {
                SDL_RenderDrawPoint(renderer, x, y + i);
                SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
                if(i == size/2) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                }
            }
            break;
        case ' ':
            // Spazio
            break;
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
            // Numeri semplici
            for(int i = 0; i < size; i++) {
                if(i == 0 || i == size - 1) {
                    for(int j = 0; j < size/2; j++) SDL_RenderDrawPoint(renderer, x + j, y + i);
                } else {
                    SDL_RenderDrawPoint(renderer, x, y + i);
                    SDL_RenderDrawPoint(renderer, x + size/2 - 1, y + i);
                }
            }
            break;
        case ':':
            // Due punti
            SDL_RenderDrawPoint(renderer, x + size/4, y + size/3);
            SDL_RenderDrawPoint(renderer, x + size/4, y + 2*size/3);
            break;
    }
}

// Funzione per disegnare una stringa
void disegna_stringa(SDL_Renderer* renderer, const char* str, int x, int y, int size) {
    int offset_x = 0;
    for(int i = 0; str[i] != '\0'; i++) {
        disegna_carattere(renderer, str[i], x + offset_x, y, size);
        offset_x += size * 3/4; // spaziatura tra caratteri
    }
}

void disegna_faglie(SDL_Renderer* renderer, Faglia faglie[], int n) {
    extern int mappa_offset;
    SDL_SetRenderDrawColor(renderer, 180, 180, 180, 255);
    for (int i = 0; i < n; i++) {
        if (faglie[i].attiva) {
            int y_mondo = faglie[i].y;
            int y = y_mondo - mappa_offset;
            if (y >= 0 && y < HEIGHT) {
                int x = faglie[i].x;
                int lunghezza = faglie[i].lunghezza;
                
                // Disegna la faglia con lunghezza variabile
                for (int j = 0; j < lunghezza; j++) {
                    int offset_x = (int)(3 * sin(j * 0.3)) + j * 2;
                    SDL_RenderDrawLine(renderer, x - offset_x, y + j * 2, 
                                     x + offset_x, y + j * 2);
                    // Aggiungi dettagli rocciosi
                    if (j % 3 == 0) {
                        SDL_RenderDrawPoint(renderer, x - offset_x - 1, y + j * 2);
                        SDL_RenderDrawPoint(renderer, x + offset_x + 1, y + j * 2);
                    }
                }
            }
        }
    }
}

void disegna_gas(SDL_Renderer* renderer, Gas g) {
    extern int mappa_offset;
    if (!g.usato) {
        int y = g.y - mappa_offset;
        if (y >= 0 && y < HEIGHT) {
            // Disegna bolla di gas con effetto animato
            Uint32 time = SDL_GetTicks();
            int size_variation = (int)(3 * sin(time * 0.01 + g.x * 0.1));
            int base_size = 15 + size_variation;
            
            // Bolla principale
            SDL_SetRenderDrawColor(renderer, 200, 200, 255, 150);
            for (int dx = -base_size/2; dx <= base_size/2; dx++) {
                for (int dy = -base_size/2; dy <= base_size/2; dy++) {
                    if (dx*dx + dy*dy <= (base_size/2)*(base_size/2)) {
                        SDL_RenderDrawPoint(renderer, g.x + dx, y + dy);
                    }
                }
            }
            
            // Riflesso sulla bolla
            SDL_SetRenderDrawColor(renderer, 240, 240, 255, 200);
            for (int dx = -3; dx <= 3; dx++) {
                for (int dy = -3; dy <= 3; dy++) {
                    if (dx*dx + dy*dy <= 9) {
                        SDL_RenderDrawPoint(renderer, g.x - base_size/4 + dx, y - base_size/4 + dy);
                    }
                }
            }
        }
    }
}

void disegna_acqua(SDL_Renderer* renderer, Acqua a) {
    extern int mappa_offset;
    if (a.attiva) {
        int y = a.y - mappa_offset;
        if (y >= 0 && y < HEIGHT) {
            SDL_SetRenderDrawColor(renderer, 100, 200, 255, 200);
            SDL_Rect r = {a.x - 5, y - 5, 10, 10};
            SDL_RenderFillRect(renderer, &r);
        }
    }
}

void disegna_testo(SDL_Renderer* renderer, const char* stato) {
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect r = {WIDTH / 2 - 100, 260, 200, 80};
    SDL_RenderDrawRect(renderer, &r);
}

// Funzione per disegnare menu principale
void disegna_menu(SDL_Renderer* renderer) {
    SDL_SetRenderDrawColor(renderer, 20, 20, 40, 255);
    SDL_RenderClear(renderer);
    
    // Effetto magma animato in background
    Uint32 time = SDL_GetTicks();
    for (int i = 0; i < 100; i++) {
        int x = (int)(WIDTH * (0.1 + 0.8 * ((i * 73) % 100) / 100.0));
        int y = HEIGHT - 80 + (int)(30 * sin((time * 0.002 + i) * 0.4));
        int size = 2 + (int)(4 * sin((time * 0.003 + i) * 0.6));
        
        SDL_SetRenderDrawColor(renderer, 255, 50 + (i % 100), 0, 150 - (i % 100));
        SDL_Rect particle = {x, y, size, size};
        SDL_RenderFillRect(renderer, &particle);
    }
    
    // Montagne di sfondo
    SDL_SetRenderDrawColor(renderer, 60, 60, 80, 255);
    for (int x = 0; x < WIDTH; x += 20) {
        int h = 150 + (int)(50 * sin(x * 0.01));
        for (int y = HEIGHT - h; y < HEIGHT - 100; y++) {
            SDL_RenderDrawPoint(renderer, x + (rand() % 20), y);
        }
    }
    
    // Titolo del gioco
    SDL_SetRenderDrawColor(renderer, 255, 100, 0, 255);
    SDL_Rect titolo = {WIDTH / 2 - 200, 80, 400, 60};
    SDL_RenderFillRect(renderer, &titolo);
    
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &titolo);
    
    // Titolo "RISALITA DEL MAGMA"
    disegna_stringa(renderer, "RISALITA DEL MAGMA", WIDTH / 2 - 180, 100, 20);
    
    // Pulsante Start
    SDL_SetRenderDrawColor(renderer, 100, 200, 100, 255);
    SDL_Rect start_btn = {WIDTH / 2 - 100, 200, 200, 50};
    SDL_RenderFillRect(renderer, &start_btn);
    
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &start_btn);
    
    // Testo "START"
    disegna_stringa(renderer, "START", WIDTH / 2 - 40, 215, 16);
    
    // Istruzioni
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    disegna_stringa(renderer, "CLICCA PER FAR SALIRE IL MAGMA", WIDTH / 2 - 180, 300, 12);
    disegna_stringa(renderer, "RACCOGLI GAS E FAGLIE PER AIUTO", WIDTH / 2 - 180, 320, 12);
    disegna_stringa(renderer, "ATTENZIONE AI MINERALI CHE", WIDTH / 2 - 150, 340, 12);
    disegna_stringa(renderer, "CRISTALLIZZANO E AUMENTANO", WIDTH / 2 - 150, 355, 12);
    disegna_stringa(renderer, "LA VISCOSITA DEL MAGMA!", WIDTH / 2 - 120, 370, 12);
    
    // Effetto cratere
    SDL_SetRenderDrawColor(renderer, 100, 50, 20, 255);
    for (int i = 0; i < 360; i += 10) {
        int x = WIDTH / 2 + (int)(150 * cos(i * 3.14159 / 180));
        int y = HEIGHT - 50 + (int)(30 * sin(i * 3.14159 / 180));
        SDL_Rect rock = {x, y, 5, 5};
        SDL_RenderFillRect(renderer, &rock);
    }
}

// Funzione per disegnare schermata game over
void disegna_game_over(SDL_Renderer* renderer, float temperatura, int tempo_rimanente) {
    SDL_SetRenderDrawColor(renderer, 40, 0, 0, 255);
    SDL_RenderClear(renderer);
    
    // Effetto fumo/cenere
    Uint32 time = SDL_GetTicks();
    for (int i = 0; i < 80; i++) {
        int x = (int)(WIDTH * ((i * 67) % 100) / 100.0);
        int y = (int)(HEIGHT * 0.8 - fmod(time * 0.05 + i * 10, HEIGHT * 0.8));
        int size = 2 + (i % 4);
        SDL_SetRenderDrawColor(renderer, 60 + (i % 40), 60 + (i % 40), 60 + (i % 40), 100);
        SDL_Rect smoke = {x, y, size, size};
        SDL_RenderFillRect(renderer, &smoke);
    }
    
    // Titolo Game Over
    SDL_SetRenderDrawColor(renderer, 200, 0, 0, 255);
    SDL_Rect game_over = {WIDTH / 2 - 150, 120, 300, 80};
    SDL_RenderFillRect(renderer, &game_over);
    
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &game_over);
    
    // Testo "GAME OVER"
    disegna_stringa(renderer, "GAME OVER", WIDTH / 2 - 90, 145, 20);
    
    // Motivo del game over
    if (temperatura <= 0) {
        disegna_stringa(renderer, "IL MAGMA SI E RAFFREDDATO", WIDTH / 2 - 150, 230, 12);
    } else if (tempo_rimanente <= 0) {
        disegna_stringa(renderer, "TEMPO SCADUTO", WIDTH / 2 - 80, 230, 12);
    }
    
    // Statistiche finali
    SDL_SetRenderDrawColor(renderer, 80, 40, 40, 255);
    SDL_Rect stats = {WIDTH / 2 - 150, 280, 300, 100};
    SDL_RenderFillRect(renderer, &stats);
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &stats);
    
    disegna_stringa(renderer, "STATISTICHE FINALI", WIDTH / 2 - 110, 290, 12);
    
    // Pulsante restart
    SDL_SetRenderDrawColor(renderer, 100, 100, 200, 255);
    SDL_Rect restart = {WIDTH / 2 - 80, 420, 160, 40};
    SDL_RenderFillRect(renderer, &restart);
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &restart);
    
    disegna_stringa(renderer, "RIPROVA", WIDTH / 2 - 35, 435, 12);
}

// Funzione per disegnare eruzione spettacolare
void disegna_eruzione(SDL_Renderer* renderer, Uint32 tempo_eruzione) {
    Uint32 time = SDL_GetTicks();
    float eruzione_progress = (tempo_eruzione / 3000.0f); // 3 secondi di eruzione
    if (eruzione_progress > 1.0f) eruzione_progress = 1.0f;
    
    // Sfondo drammatico dell'eruzione
    SDL_SetRenderDrawColor(renderer, 40 + (int)(30 * eruzione_progress), 20, 10, 255);
    SDL_RenderClear(renderer);
    
    // FONTANA DI LAVA GIGANTE
    int centro_x = WIDTH / 2;
    int base_y = HEIGHT - 50;
    
    for (int i = 0; i < 200; i++) {
        // Particelle di lava che volano in aria
        float angle = (float)i * 0.314f + sin(time * 0.01 + i) * 2;
        float speed = 150 + (i % 100) + sin(time * 0.008 + i) * 50;
        float gravity_time = (tempo_eruzione + i * 20) * 0.003f;
        
        int x = centro_x + (int)(cos(angle) * speed * eruzione_progress);
        int y = base_y - (int)(sin(angle) * speed * eruzione_progress) + (int)(gravity_time * gravity_time * 100);
        
        if (y > base_y) continue; // Non disegnare particelle cadute
        if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) continue;
        
        // Colori incandescenti per le particelle
        int red = 255;
        int green = 150 + (int)(sin(time * 0.02 + i) * 100);
        int blue = 30 + (int)(cos(time * 0.025 + i) * 50);
        
        if (green > 255) green = 255;
        if (green < 50) green = 50;
        if (blue > 100) blue = 100;
        if (blue < 10) blue = 10;
        
        SDL_SetRenderDrawColor(renderer, red, green, blue, 255);
        
        // Disegna particella con dimensione variabile
        int size = 2 + (int)(eruzione_progress * 3);
        for (int px = 0; px < size; px++) {
            for (int py = 0; py < size; py++) {
                SDL_RenderDrawPoint(renderer, x + px, y + py);
            }
        }
    }
    
    // COLONNA CENTRALE DI MAGMA
    for (int y = base_y; y >= base_y - (int)(200 * eruzione_progress); y -= 2) {
        int larghezza = 30 + (int)(sin((base_y - y) * 0.1 + time * 0.01) * 15);
        for (int x = centro_x - larghezza/2; x <= centro_x + larghezza/2; x++) {
            if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT) {
                // Colore della colonna principale
                int dist_center = abs(x - centro_x);
                int red = 255;
                int green = 200 - dist_center * 3;
                int blue = 50 - dist_center;
                
                if (green < 60) green = 60;
                if (blue < 5) blue = 5;
                
                SDL_SetRenderDrawColor(renderer, red, green, blue, 255);
                SDL_RenderDrawPoint(renderer, x, y);
            }
        }
    }
    
    // Testo dell'eruzione
    disegna_stringa(renderer, "ERUZIONE!", WIDTH / 2 - 50, 50, 16);
    disegna_stringa(renderer, "IL VULCANO E' IN ERUZIONE!", WIDTH / 2 - 140, 100, 12);
}

// Funzione per disegnare schermata vittoria
void disegna_vittoria(SDL_Renderer* renderer, float temperatura_finale, int tempo_impiegato) {
    SDL_SetRenderDrawColor(renderer, 0, 20, 40, 255);
    SDL_RenderClear(renderer);
    
    // Effetto di celebrazione con eruzioni
    Uint32 time = SDL_GetTicks();
    for (int i = 0; i < 120; i++) {
        int x = (int)(WIDTH * (0.3 + 0.4 * sin((time * 0.003 + i) * 0.7)));
        int y = (int)(HEIGHT * (0.2 + 0.5 * cos((time * 0.002 + i) * 0.8)));
        int size = 2 + (int)(4 * sin((time * 0.005 + i) * 0.6));
        
        if (i % 4 == 0) SDL_SetRenderDrawColor(renderer, 255, 215, 0, 200); // Oro
        else if (i % 4 == 1) SDL_SetRenderDrawColor(renderer, 255, 100, 0, 200); // Arancione
        else if (i % 4 == 2) SDL_SetRenderDrawColor(renderer, 255, 50, 0, 200); // Rosso
        else SDL_SetRenderDrawColor(renderer, 255, 255, 255, 200); // Bianco
        
        SDL_Rect star = {x, y, size, size};
        SDL_RenderFillRect(renderer, &star);
    }
    
    // Simulazione eruzione di successo
    for (int i = 0; i < 50; i++) {
        int x = WIDTH / 2 + (int)(80 * sin((time * 0.01 + i) * 0.5));
        int y = 50 + (int)(100 * fmod(time * 0.02 + i * 10, 100) / 100.0);
        SDL_SetRenderDrawColor(renderer, 255, 100 + (i % 100), 0, 150);
        SDL_Rect lava = {x, y, 4, 4};
        SDL_RenderFillRect(renderer, &lava);
    }
    
    // Titolo Vittoria
    SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255);
    SDL_Rect vittoria = {WIDTH / 2 - 150, 120, 300, 80};
    SDL_RenderFillRect(renderer, &vittoria);
    
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &vittoria);
    
    // Testo "VITTORIA"
    disegna_stringa(renderer, "VITTORIA", WIDTH / 2 - 80, 145, 20);
    
    // Messaggio di congratulazioni
    disegna_stringa(renderer, "COMPLIMENTI! HAI RAGGIUNTO", WIDTH / 2 - 160, 230, 12);
    disegna_stringa(renderer, "LA SUPERFICIE!", WIDTH / 2 - 80, 250, 12);
    
    // Statistiche finali
    SDL_SetRenderDrawColor(renderer, 50, 100, 150, 255);
    SDL_Rect stats = {WIDTH / 2 - 150, 290, 300, 100};
    SDL_RenderFillRect(renderer, &stats);
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &stats);
    
    disegna_stringa(renderer, "STATISTICHE FINALI", WIDTH / 2 - 110, 300, 12);
    char tempo_str[50];
    sprintf(tempo_str, "TEMPO IMPIEGATO: %d SEC", tempo_impiegato);
    disegna_stringa(renderer, tempo_str, WIDTH / 2 - 120, 320, 10);
    
    char temp_str[50];
    sprintf(temp_str, "TEMPERATURA FINALE: %.0f", temperatura_finale);
    disegna_stringa(renderer, temp_str, WIDTH / 2 - 140, 340, 10);
    
    // Pulsante restart
    SDL_SetRenderDrawColor(renderer, 100, 200, 100, 255);
    SDL_Rect restart = {WIDTH / 2 - 80, 420, 160, 40};
    SDL_RenderFillRect(renderer, &restart);
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &restart);
    
    disegna_stringa(renderer, "GIOCA ANCORA", WIDTH / 2 - 65, 435, 10);
}

// Nuova funzione per disegnare countdown
void disegna_countdown(SDL_Renderer* renderer, int tempo) {
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect r = {WIDTH - 120, 20, 100, 20};
    SDL_RenderDrawRect(renderer, &r);
    SDL_Rect b = {WIDTH - 120, 20, tempo * (100 / 60), 20};
    SDL_SetRenderDrawColor(renderer, 255, 255, 0, 255);
    SDL_RenderFillRect(renderer, &b);
}

// Funzione per determinare la fase ambientale basata sulla profondità
FaseAmbiente get_fase_ambiente(int y_mondo) {
    if (y_mondo > 1500) return FASE_MANTELLO;
    else if (y_mondo > 500) return FASE_CROSTA;
    else return FASE_CONDOTTO;
}

// Funzione per disegnare insidie geologiche realistiche
void disegna_insidie(SDL_Renderer* renderer, Insidia insidie[], int n) {
    extern int mappa_offset;
    
    for (int i = 0; i < n; i++) {
        if (insidie[i].attiva) {
            int y = insidie[i].y - mappa_offset;
            if (y >= -50 && y < HEIGHT + 50) {
                SDL_Rect rect = {insidie[i].x, y, insidie[i].larghezza, insidie[i].altezza};
                
                switch(insidie[i].tipo) {
                    case 0: // Cristallizzazione/Minerali
                        // Zona di cristallizzazione con minerali che aumentano viscosità
                        SDL_SetRenderDrawColor(renderer, 150, 100, 200, 180);
                        SDL_RenderFillRect(renderer, &rect);
                        SDL_SetRenderDrawColor(renderer, 200, 150, 255, 255);
                        SDL_RenderDrawRect(renderer, &rect);
                        
                        // Cristalli che si formano
                        Uint32 time = SDL_GetTicks();
                        for (int j = 0; j < 8; j++) {
                            int cx = insidie[i].x + (j * insidie[i].larghezza / 8);
                            int cy = y + (j * insidie[i].altezza / 8);
                            int crystal_size = 2 + (int)(2 * sin((time * 0.01 + j) * 0.3));
                            
                            SDL_SetRenderDrawColor(renderer, 255, 200, 255, 200);
                            SDL_Rect crystal = {cx, cy, crystal_size, crystal_size};
                            SDL_RenderFillRect(renderer, &crystal);
                            
                            // Effetto scintillio
                            if ((time + j * 100) % 500 < 100) {
                                SDL_SetRenderDrawColor(renderer, 255, 255, 255, 150);
                                SDL_RenderDrawPoint(renderer, cx + 1, cy + 1);
                            }
                        }
                        break;
                        
                    case 1: // Raffreddamento rapido
                        // Zona dove il magma si raffredda rapidamente e diventa viscoso
                        SDL_SetRenderDrawColor(renderer, 100, 50, 150, 160);
                        SDL_RenderFillRect(renderer, &rect);
                        SDL_SetRenderDrawColor(renderer, 150, 100, 200, 255);
                        SDL_RenderDrawRect(renderer, &rect);
                        
                        // Effetto di raffreddamento con gradiente
                        for (int x = insidie[i].x; x < insidie[i].x + insidie[i].larghezza; x += 4) {
                            for (int yy = y; yy < y + insidie[i].altezza; yy += 4) {
                                int cooling_intensity = 50 + (rand() % 100);
                                SDL_SetRenderDrawColor(renderer, cooling_intensity, cooling_intensity/2, cooling_intensity + 50, 120);
                                SDL_Rect cool_spot = {x, yy, 2, 2};
                                SDL_RenderFillRect(renderer, &cool_spot);
                            }
                        }
                        break;
                        
                    case 2: // Gas che si espandono
                        // Bolle di gas che si espandono e creano resistenza
                        SDL_SetRenderDrawColor(renderer, 200, 200, 100, 140);
                        SDL_RenderFillRect(renderer, &rect);
                        
                        // Bolle di gas in espansione
                        for (int j = 0; j < 6; j++) {
                            int bx = insidie[i].x + (j * insidie[i].larghezza / 6) + (int)(3 * sin((SDL_GetTicks() * 0.008 + j) * 0.5));
                            int by = y + (j * insidie[i].altezza / 6) + (int)(2 * cos((SDL_GetTicks() * 0.006 + j) * 0.7));
                            int bubble_size = 4 + (int)(3 * sin((SDL_GetTicks() * 0.01 + j) * 0.4));
                            
                            // Bolla principale
                            SDL_SetRenderDrawColor(renderer, 255, 255, 150, 180);
                            for (int dx = -bubble_size/2; dx <= bubble_size/2; dx++) {
                                for (int dy = -bubble_size/2; dy <= bubble_size/2; dy++) {
                                    if (dx*dx + dy*dy <= (bubble_size/2)*(bubble_size/2)) {
                                        SDL_RenderDrawPoint(renderer, bx + dx, by + dy);
                                    }
                                }
                            }
                            
                            // Riflesso sulla bolla
                            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 220);
                            SDL_RenderDrawPoint(renderer, bx - bubble_size/4, by - bubble_size/4);
                        }
                        break;
                }
                
                // Etichetta del tipo di insidia
                const char* etichette[] = {"CRISTALLI", "RAFFRED.", "GAS EXPAND"};
                SDL_SetRenderDrawColor(renderer, 255, 255, 255, 200);
                disegna_stringa(renderer, etichette[insidie[i].tipo], insidie[i].x + 2, y - 12, 6);
            }
        }
    }
}


// Funzione per calcolare larghezza del condotto nelle tre fasi
int condotto_width_at_y(int y) {
    FaseAmbiente fase = get_fase_ambiente(y);
    
    switch(fase) {
        case FASE_MANTELLO:
            // Mantello: condotto molto largo, ambiente roccioso denso
            return 350 - (int)(50 * sin(y * 0.001)); // 300-400px con variazioni
            
        case FASE_CROSTA:
            // Crosta terrestre: condotto medio, più strutturato
            return 250 - (int)(100 * ((float)(y - 500) / 1000)); // da 250 a 150px
            
        case FASE_CONDOTTO:
            // Condotto vulcanico vero: si restringe verso la superficie
            return 150 - (int)(100 * ((float)y / 500)); // da 150 a 50px
            
        default:
            return 200;
    }
}

// Funzione per disegnare condotto che viene scavato progressivamente dal magma
void disegna_condotto(SDL_Renderer* renderer) {
    extern int mappa_offset;
    extern int altezza_condotto_scavato;
    
    for (int y = 0; y < HEIGHT; y++) {
        int y_mondo = y + mappa_offset;
        
        // Il condotto esiste solo dove il magma è già passato
        if (y_mondo < altezza_condotto_scavato) {
            FaseAmbiente fase = get_fase_ambiente(y_mondo);
            int w = condotto_width_at_y(y_mondo);
            int x = WIDTH / 2 - w / 2;
            
            // Sfondo del condotto
            SDL_SetRenderDrawColor(renderer, 15, 10, 5, 255);
            for (int i = x; i <= x + w; i++) {
                SDL_RenderDrawPoint(renderer, i, y);
            }
            
            // Pareti del condotto scavato
            SDL_SetRenderDrawColor(renderer, 80, 60, 40, 255);
            SDL_RenderDrawPoint(renderer, x - 1, y);
            SDL_RenderDrawPoint(renderer, x + w + 1, y);
            
            // Dettagli delle pareti scavate
            if (y_mondo % 20 == 0) {
                for (int i = 0; i < 3; i++) {
                    int rock_x = x - 2 + (rand() % 4);
                    SDL_SetRenderDrawColor(renderer, 60 + (rand() % 20), 40 + (rand() % 15), 20, 255);
                    SDL_Rect rock = {rock_x, y, 2, 2};
                    SDL_RenderFillRect(renderer, &rock);
                    
                    rock_x = x + w - 2 + (rand() % 4);
                    rock = (SDL_Rect){rock_x, y, 2, 2};
                    SDL_RenderFillRect(renderer, &rock);
                }
            }
        } else {
            // Roccia solida non ancora scavata
            FaseAmbiente fase = get_fase_ambiente(y_mondo);
            int w = WIDTH; // Tutta la larghezza è roccia
            
            switch(fase) {
                case FASE_MANTELLO:
                    SDL_SetRenderDrawColor(renderer, 60, 20, 10, 255);
                    break;
                case FASE_CROSTA:
                    SDL_SetRenderDrawColor(renderer, 80, 60, 40, 255);
                    break;
                case FASE_CONDOTTO:
                    SDL_SetRenderDrawColor(renderer, 50, 40, 30, 255);
                    break;
            }
            
            for (int i = 0; i < WIDTH; i++) {
                SDL_RenderDrawPoint(renderer, i, y);
            }
            
            // Texture della roccia
            if (y_mondo % 15 == 0) {
                for (int i = 0; i < WIDTH; i += 20) {
                    SDL_SetRenderDrawColor(renderer, 40 + (rand() % 20), 30 + (rand() % 15), 15, 255);
                    SDL_Rect rock = {i, y, 3 + (rand() % 2), 1 + (rand() % 2)};
                    SDL_RenderFillRect(renderer, &rock);
                }
            }
        }
    }
    
    // Effetti di luce solo nel condotto scavato
    Uint32 time = SDL_GetTicks();
    for (int i = 0; i < 10; i++) {
        int light_y = (i * 89 + mappa_offset / 5) % HEIGHT;
        int light_y_mondo = light_y + mappa_offset;
        
        if (light_y >= 0 && light_y < HEIGHT && light_y_mondo < altezza_condotto_scavato) {
            int light_x = WIDTH / 2 + (int)(20 * sin((time * 0.003 + i) * 0.5));
            SDL_SetRenderDrawColor(renderer, 255, 150, 50, 60);
            SDL_Rect light = {light_x, light_y, 3, 3};
            SDL_RenderFillRect(renderer, &light);
        }
    }
}

// Funzione per disegnare magma che si comporta come VERO FLUIDO
void disegna_magma(SDL_Renderer* renderer, Magma magma) {
    extern int mappa_offset;
    extern int altezza_condotto_scavato;
    
    Uint32 time = SDL_GetTicks();
    int magma_height = 150; // Magma alto per effetto fluido
    
    int y_start_mondo = (int)magma.y;
    int y_end_mondo = y_start_mondo + magma_height;
    
    // MAGMA FLUIDO che riempie TUTTO il condotto disponibile
    for (int y = y_start_mondo; y < y_end_mondo; y++) {
        int y_schermo = y - mappa_offset;
        if (y_schermo < 0 || y_schermo >= HEIGHT) continue;
        
        // LARGHEZZA DINAMICA: riempie tutto il condotto scavato
        int w = condotto_width_at_y(y);
        if (y < altezza_condotto_scavato) {
            w = condotto_width_at_y(y) - 4; // Leggero margine dalle pareti
        } else {
            w = 60; // Larghezza base quando scava nuovo terreno
        }
        
        int x = WIDTH / 2 - w / 2;
        
        // Effetto fluido: il magma "scorre" lungo le pareti
        float fluidity_factor = (float)(y - y_start_mondo) / magma_height;
        float wall_interaction = sin((y + time * 0.008) * 0.3) * (4.0f * fluidity_factor);
        
        // Onde fluide multiple per movimento realistico
        float wave1 = sin((y + time * 0.006) * 0.15) * 3;
        float wave2 = cos((y + time * 0.009) * 0.22) * 2;
        float wave3 = sin((y + time * 0.004) * 0.18) * 4;
        int base_offset = (int)(wave1 + wave2 + wave3 + wall_interaction);
        
        for (int dx = 0; dx < w; dx++) {
            // COMPORTAMENTO FLUIDO: maggiore densità verso il basso
            float height_intensity = 1.3f - (float)(y - y_start_mondo) / magma_height;
            if (height_intensity > 1.0f) height_intensity = 1.0f;
            if (height_intensity < 0.3f) height_intensity = 0.3f;
            
            // Effetto fluido locale: onde che si propagano
            float local_wave = sin((dx + y + time * 0.02) * 0.5) * 2;
            float viscosity_wave = cos((dx * 0.3 + time * 0.015)) * 1.5;
            int final_offset = base_offset + (int)(local_wave + viscosity_wave);
            
            // COLORI FLUIDI - più realistici con gradazioni
            float distance_from_center = fabs(dx - w/2.0f) / (w/2.0f);
            
            int red = (int)(255 * height_intensity);
            int green = (int)(140 * height_intensity + 60 * sin((dx + time * 0.02) * 0.4));
            int blue = (int)(50 * height_intensity + 20 * distance_from_center);
            
            // Assicura colori visibili
            if (red < 180) red = 180;
            if (green > 255) green = 255;
            if (green < 40) green = 40;
            if (blue < 5) blue = 5;
            
            // NUCLEO INCANDESCENTE al centro (zona più calda)
            if (distance_from_center < 0.4) {
                red = 255;
                green = 255; // Centro bianco-giallo brillante
                blue = (int)(220 * (0.4 - distance_from_center) / 0.4);
            }
            
            // BORDI FLUIDI: effetto di adesione alle pareti
            if (dx < 3 || dx >= w-3) {
                red = (int)(red * 0.9f); // Leggermente più scuro ai bordi
                green = (int)(green * 0.85f);
                float adhesion = sin((y + time * 0.01) * 0.6) * 1;
                final_offset += (int)adhesion; // Il magma "si attacca" alle pareti
            }
            
            SDL_SetRenderDrawColor(renderer, red, green, blue, 255);
            
            // Disegna pixel multipli per maggiore presenza
            SDL_RenderDrawPoint(renderer, x + dx + final_offset, y_schermo);
            SDL_RenderDrawPoint(renderer, x + dx + final_offset + 1, y_schermo); // Pixel aggiuntivo
            
            // Particelle incandescenti più frequenti
            if ((dx + y + time/30) % 12 == 0) {
                SDL_SetRenderDrawColor(renderer, 255, 255, 200, 255);
                SDL_RenderDrawPoint(renderer, x + dx + final_offset, y_schermo - 1);
                SDL_RenderDrawPoint(renderer, x + dx + final_offset + 1, y_schermo - 1);
                SDL_RenderDrawPoint(renderer, x + dx + final_offset, y_schermo + 1);
            }
        }
    }
    
    // SUPERFICIE DEL MAGMA CON EFFETTI SPETTACOLARI
    int surface_y = y_start_mondo - mappa_offset;
    if (surface_y >= 0 && surface_y < HEIGHT) {
        int w = condotto_width_at_y(y_start_mondo) - 5;
        if (w < 30) w = 30;
        int x = WIDTH / 2 - w / 2;
        
        // Bolle più grandi e luminose
        for (int dx = 0; dx < w; dx += 3) {
            float bubble = sin((dx + time * 0.03) * 0.8) * 5;
            SDL_SetRenderDrawColor(renderer, 255, 255, 150, 255);
            SDL_Rect bubble_rect = {x + dx, surface_y + (int)bubble - 2, 4, 4};
            SDL_RenderFillRect(renderer, &bubble_rect);
            
            // Riflessi delle bolle
            SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
            SDL_RenderDrawPoint(renderer, x + dx + 1, surface_y + (int)bubble - 1);
        }
        
        // Bagliore intenso sulla superficie
        SDL_SetRenderDrawColor(renderer, 255, 255, 150, 200);
        for (int dx = 0; dx < w; dx++) {
            SDL_RenderDrawPoint(renderer, x + dx, surface_y - 3);
            SDL_RenderDrawPoint(renderer, x + dx, surface_y - 2);
            SDL_RenderDrawPoint(renderer, x + dx, surface_y - 1);
        }
    }
    
    // ALONE LUMINOSO ESTESO MOLTO VISIBILE
    int halo_y = y_start_mondo - mappa_offset;
    if (halo_y >= 5 && halo_y < HEIGHT - 5) {
        int w = condotto_width_at_y(y_start_mondo) + 15;
        int x = WIDTH / 2 - w / 2;
        
        // Alone a multipli livelli
        for (int level = 0; level < 6; level++) {
            int alpha = 150 - (level * 25);
            SDL_SetRenderDrawColor(renderer, 255, 150 - level * 15, 50, alpha);
            
            for (int dx = -level * 3; dx < w + level * 3; dx++) {
                if (x + dx >= 0 && x + dx < WIDTH) {
                    SDL_RenderDrawPoint(renderer, x + dx, halo_y - (4 + level));
                    SDL_RenderDrawPoint(renderer, x + dx, halo_y + magma_height + (4 + level));
                }
            }
        }
    }
    
    // PARTICELLE VOLANTI INCANDESCENTI
    for (int i = 0; i < 12; i++) {
        int particle_x = WIDTH / 2 + (int)(30 * sin((time * 0.025 + i * 0.8))) + (rand() % 15) - 7;
        int particle_y = surface_y - 15 + (int)(20 * cos((time * 0.02 + i * 1.2)));
        
        if (particle_y >= 0 && particle_y < HEIGHT && particle_x >= 0 && particle_x < WIDTH) {
            SDL_SetRenderDrawColor(renderer, 255, 200 + (rand() % 55), 100 + (rand() % 50), 255);
            SDL_Rect particle = {particle_x, particle_y, 3, 3};
            SDL_RenderFillRect(renderer, &particle);
            
            // Bagliore delle particelle
            SDL_SetRenderDrawColor(renderer, 255, 255, 200, 150);
            SDL_RenderDrawPoint(renderer, particle_x + 1, particle_y + 1);
        }
    }
}

void disegna_bordo_incandescente(SDL_Renderer* renderer, int y) {
    extern int mappa_offset;
    int y_mondo = y;
    int y_schermo = y_mondo - mappa_offset;
    if (y_schermo < 0 || y_schermo >= HEIGHT) return;
    int w = condotto_width_at_y(y_mondo);
    int x = WIDTH / 2 - w / 2;
    SDL_SetRenderDrawColor(renderer, 255, 100, 0, 180); // arancione semi-trasparente
    SDL_RenderDrawLine(renderer, x, y_schermo, x + w, y_schermo);
}

void disegna_particelle(SDL_Renderer* renderer, int frame) {
    extern int mappa_offset;
    for (int i = 0; i < 10; i++) {
        int x = WIDTH / 2 + (rand() % 40) - 20;
        int y_mondo = 50 + (rand() % 30);
        int y = y_mondo - mappa_offset;
        if (y >= 0 && y < HEIGHT) {
            SDL_SetRenderDrawColor(renderer, 200, 200, 255, 120 + rand() % 100);
            SDL_RenderDrawPoint(renderer, x, y + (int)(5 * sin((frame + i) * 0.2)));
        }
    }
}

// Funzione per disegnare temperatura
void disegna_temperatura(SDL_Renderer* renderer, float t) {
    int bar_w = (int)(t * 2); // max 200 px
    SDL_Rect bar = {20, 20, bar_w, 20};
    SDL_SetRenderDrawColor(renderer, 255, 100, 0, 255);
    SDL_RenderFillRect(renderer, &bar);

    SDL_Rect frame = {20, 20, 200, 20};
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &frame);
}

// Funzione per disegnare indicatore di viscosità
void disegna_viscosita(SDL_Renderer* renderer, float viscosita) {
    // Barra della viscosità
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect frame_visc = {20, 110, 120, 15};
    SDL_RenderDrawRect(renderer, &frame_visc);
    
    // Riempimento della barra (più viscoso = più rosso)
    int visc_width = (int)(viscosita * 60); // Massimo 120px quando viscosità = 2
    if (visc_width > 120) visc_width = 120;
    
    int red = 100 + (int)(viscosita * 77); // Da verde a rosso
    int green = 200 - (int)(viscosita * 100);
    if (red > 255) red = 255;
    if (green < 0) green = 0;
    
    SDL_SetRenderDrawColor(renderer, red, green, 0, 255);
    SDL_Rect visc_bar = {20, 110, visc_width, 15};
    SDL_RenderFillRect(renderer, &visc_bar);
    
    // Etichetta
    disegna_stringa(renderer, "VISCOSITA", 145, 112, 8);
}

// Funzione per disegnare indicatore di fase
void disegna_indicatore_fase(SDL_Renderer* renderer, int y_magma) {
    FaseAmbiente fase = get_fase_ambiente(y_magma);
    const char* nome_fase;
    SDL_Color colore_fase;
    
    switch(fase) {
        case FASE_MANTELLO:
            nome_fase = "MANTELLO";
            colore_fase = (SDL_Color){255, 100, 50, 255};
            break;
        case FASE_CROSTA:
            nome_fase = "CROSTA";
            colore_fase = (SDL_Color){150, 120, 80, 255};
            break;
        case FASE_CONDOTTO:
            nome_fase = "CONDOTTO";
            colore_fase = (SDL_Color){100, 100, 100, 255};
            break;
    }
    
    // Sfondo indicatore
    SDL_SetRenderDrawColor(renderer, colore_fase.r, colore_fase.g, colore_fase.b, 200);
    SDL_Rect indicator = {20, 50, 150, 25};
    SDL_RenderFillRect(renderer, &indicator);
    
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_RenderDrawRect(renderer, &indicator);
    
    // Testo fase
    disegna_stringa(renderer, nome_fase, 25, 57, 10);
    
    // Profondità
    char profondita[50];
    sprintf(profondita, "PROF: %dm", y_magma);
    disegna_stringa(renderer, profondita, 20, 80, 8);
}

int main(int argc, char* argv[]) {
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window* window = SDL_CreateWindow("Risalita del Magma", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, WIDTH, HEIGHT, 0);
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);

    StatoGioco stato_corrente = STATO_MENU;
    bool running = true;
    SDL_Event e;
    
    // Variabili per statistiche finali
    float temperatura_finale = 0;
    int tempo_impiegato = 0;
    int tempo_rimanente = 0;

    // Aggiunta strutture dati e variabili per gas, faglie e countdown
    Faglia faglie[5];
    Gas gas_bubbles[3];
    Acqua molecola;
    Insidia insidie[8]; // Nuove insidie
    int countdown;
    Uint32 countdown_timer;
    Magma magma;
    Uint32 last_time;
    float raffreddamento = 0.05f;
    float risalita = 5.0f;
    int frame = 0;
    int target_offset = 0; // Per telecamera fluida
    float viscosita_corrente = 1.0f; // Traccia la viscosità del magma
    
    // Variabili per l'eruzione
    Uint32 tempo_inizio_eruzione = 0;
    bool eruzione_iniziata = false;

    while (running) {
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                running = false;
            }
            
            if (stato_corrente == STATO_MENU) {
                if (e.type == SDL_MOUSEBUTTONDOWN || e.type == SDL_KEYDOWN) {
                    // Reset del gioco
                    faglie[0] = (Faglia){WIDTH / 2 - 40, 400, 15, true};
                    faglie[1] = (Faglia){WIDTH / 2 + 20, 350, 25, true};
                    faglie[2] = (Faglia){WIDTH / 2 - 60, 250, 35, true};
                    faglie[3] = (Faglia){WIDTH / 2 + 45, 180, 10, true};
                    faglie[4] = (Faglia){WIDTH / 2 - 30, 120, 20, true};
                    
                    gas_bubbles[0] = (Gas){WIDTH / 2, 450, -2.0f, false};
                    gas_bubbles[1] = (Gas){WIDTH / 2 + 30, 320, -1.5f, false};
                    gas_bubbles[2] = (Gas){WIDTH / 2 - 25, 200, -2.5f, false};
                    
                    molecola = (Acqua){WIDTH / 2 - 30, 200, true};
                    
                    // Inizializza insidie geologiche realistiche nelle tre fasi
                    insidie[0] = (Insidia){WIDTH / 2 - 60, 1800, 120, 40, true, 2, 0.3f}; // Gas che si espandono nel mantello
                    insidie[1] = (Insidia){WIDTH / 2 - 80, 1600, 160, 30, true, 1, 0.4f}; // Raffreddamento nel mantello
                    insidie[2] = (Insidia){WIDTH / 2 + 20, 1400, 100, 50, true, 0, 0.5f}; // Cristallizzazione nel mantello
                    insidie[3] = (Insidia){WIDTH / 2 - 50, 1000, 100, 35, true, 0, 0.6f}; // Minerali nella crosta
                    insidie[4] = (Insidia){WIDTH / 2 + 10, 800, 80, 25, true, 1, 0.7f};  // Raffreddamento rapido nella crosta
                    insidie[5] = (Insidia){WIDTH / 2 - 40, 600, 80, 30, true, 2, 0.4f};  // Gas in espansione nella crosta
                    insidie[6] = (Insidia){WIDTH / 2 - 30, 300, 60, 20, true, 0, 0.8f};  // Cristallizzazione nel condotto
                    insidie[7] = (Insidia){WIDTH / 2 + 5, 150, 50, 25, true, 1, 0.9f};   // Raffreddamento finale nel condotto
                    
                    countdown = 60;
                    countdown_timer = SDL_GetTicks();
                    magma = (Magma){.y = 1500, .temperatura = 100.0f, .clic_necessari = 1, .clic_attuali = 0}; // Inizia nel mantello, ma visibile
                    altezza_condotto_scavato = 1500; // Il condotto inizia dalla posizione del magma
                    last_time = SDL_GetTicks();
                    frame = 0;
                    mappa_offset = 1500 - HEIGHT / 2; // Inizia centrato sul magma
                    target_offset = mappa_offset;
                    
                    stato_corrente = STATO_GIOCO;
                }
            }
            else if (stato_corrente == STATO_GIOCO) {
                if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
                    magma.clic_attuali++;
                    if (magma.clic_attuali >= magma.clic_necessari) {
                        magma.y -= risalita;
                        magma.temperatura += 1.0f;
                        magma.clic_attuali = 0;

                        // Il magma scava il condotto man mano che sale
                        if (magma.y < altezza_condotto_scavato) {
                            altezza_condotto_scavato = (int)magma.y;
                        }

                        // Aumenta difficoltà
                        if ((int)magma.y % 100 == 0 && magma.clic_necessari < 5)
                            magma.clic_necessari++;
                    }
                }
            }
            else if (stato_corrente == STATO_ERUZIONE) {
                // Durante l'eruzione, passa automaticamente alla vittoria dopo 3 secondi
                if (SDL_GetTicks() - tempo_inizio_eruzione > 3000) {
                    temperatura_finale = magma.temperatura;
                    tempo_impiegato = 60 - countdown;
                    stato_corrente = STATO_VITTORIA;
                }
                // Oppure permetti di saltare con click/key
                if (e.type == SDL_MOUSEBUTTONDOWN || e.type == SDL_KEYDOWN) {
                    temperatura_finale = magma.temperatura;
                    tempo_impiegato = 60 - countdown;
                    stato_corrente = STATO_VITTORIA;
                }
            }
            else if (stato_corrente == STATO_GAME_OVER || stato_corrente == STATO_VITTORIA) {
                if (e.type == SDL_MOUSEBUTTONDOWN || e.type == SDL_KEYDOWN) {
                    stato_corrente = STATO_MENU;
                }
            }
        }
        
        if (stato_corrente == STATO_GIOCO) {
            // Aggiorna posizione delle bolle di gas
            for (int i = 0; i < 3; i++) {
                if (!gas_bubbles[i].usato) {
                    gas_bubbles[i].y += gas_bubbles[i].velocita_y;
                    // Resetta le bolle quando escono dallo schermo
                    if (gas_bubbles[i].y < 0) {
                        gas_bubbles[i].y = magma.y + 200;
                        gas_bubbles[i].x = WIDTH / 2 + (rand() % 80) - 40;
                    }
                }
            }
            
            // Verifica collisioni con insidie geologiche
            viscosita_corrente = 1.0f; // Reset viscosità
            bool in_insidia = false;
            
            for (int i = 0; i < 8; i++) {
                if (insidie[i].attiva) {
                    // Controlla se il magma tocca l'insidia
                    if (magma.y >= insidie[i].y && magma.y <= insidie[i].y + insidie[i].altezza &&
                        WIDTH / 2 >= insidie[i].x && WIDTH / 2 <= insidie[i].x + insidie[i].larghezza) {
                        
                        in_insidia = true;
                        viscosita_corrente += insidie[i].viscosita_aggiunta;
                        
                        switch(insidie[i].tipo) {
                            case 0: // Cristallizzazione/Minerali - aumenta viscosità
                                magma.clic_necessari += 1;
                                if (magma.clic_necessari > 6) magma.clic_necessari = 6;
                                magma.temperatura -= 5.0f; // Leggera perdita di calore
                                break;
                                
                            case 1: // Raffreddamento rapido - aumenta molto la viscosità
                                magma.temperatura -= 15.0f; // Forte raffreddamento
                                magma.clic_necessari += 2;
                                if (magma.clic_necessari > 8) magma.clic_necessari = 8;
                                break;
                                
                            case 2: // Gas in espansione - crea resistenza ma anche spinta
                                magma.temperatura += 5.0f; // I gas possono riscaldare
                                magma.clic_necessari += 1;
                                // Ogni tanto i gas danno una spinta
                                if ((SDL_GetTicks() / 1000) % 3 == 0) {
                                    magma.y -= 5; // Spinta occasionale dai gas
                                }
                                break;
                        }
                        
                        // Non rimuovere l'insidia immediatamente - rappresenta un processo continuo
                        // L'insidia si "consuma" lentamente
                        if (rand() % 100 < 5) { // 5% di probabilità di consumarsi ogni frame
                            insidie[i].attiva = false;
                        }
                    }
                }
            }
            
            // Applica la viscosità alla velocità di risalita
            if (in_insidia) {
                risalita = 5.0f / viscosita_corrente; // Più viscoso = più lento
                if (risalita < 1.0f) risalita = 1.0f; // Velocità minima
            } else {
                risalita = 5.0f; // Velocità normale
            }
            
            // Verifica raccolta gas/faglie
            for (int i = 0; i < 5; i++) {
                if (faglie[i].attiva && fabs(magma.y - faglie[i].y) < 15) {
                    magma.clic_necessari = (magma.clic_necessari > 1) ? magma.clic_necessari - 1 : 1;
                    magma.y -= 20;  // accelera la risalita
                    faglie[i].attiva = false;
                }
            }
            
            // Verifica raccolta bolle di gas
            for (int i = 0; i < 3; i++) {
                if (!gas_bubbles[i].usato && fabs(magma.y - gas_bubbles[i].y) < 25) {
                    magma.temperatura += 15.0f;
                    magma.y -= 30;  // le bolle fanno salire il magma
                    gas_bubbles[i].usato = true;
                    // Rigenera la bolla dopo un po'
                    gas_bubbles[i].y = magma.y + 200;
                    gas_bubbles[i].usato = false;
                    gas_bubbles[i].x = WIDTH / 2 + (rand() % 80) - 40;
                }
            }
            
            if (molecola.attiva && fabs(magma.y - molecola.y) < 10 && abs(WIDTH / 2 - molecola.x) < 50) {
                magma.temperatura += 15.0f;
                magma.clic_necessari = (magma.clic_necessari > 1) ? magma.clic_necessari - 1 : 1;
                molecola.attiva = false;
            }

            // Raffreddamento e countdown
            Uint32 now = SDL_GetTicks();
            if (now - last_time > 1000) {
                magma.temperatura -= raffreddamento;
                last_time = now;
            }
            if (now - countdown_timer > 1000) {
                countdown--;
                countdown_timer = now;
            }

            // Condizioni di fine gioco
            if (magma.temperatura <= 0.0f) {
                temperatura_finale = magma.temperatura;
                tempo_rimanente = countdown;
                stato_corrente = STATO_GAME_OVER;
            }
            if (countdown <= 0) {
                temperatura_finale = magma.temperatura;
                tempo_rimanente = countdown;
                stato_corrente = STATO_GAME_OVER;
            }
            if (magma.y <= 0.0f && !eruzione_iniziata) {
                // Inizia l'eruzione spettacolare!
                eruzione_iniziata = true;
                tempo_inizio_eruzione = SDL_GetTicks();
                stato_corrente = STATO_ERUZIONE;
            }

            // Telecamera SEMPRE centrata sul magma - MOVIMENTO DIRETTO
            mappa_offset = (int)magma.y - HEIGHT / 2;
        }

        // Rendering basato sullo stato
        if (stato_corrente == STATO_MENU) {
            disegna_menu(renderer);
        }
        else if (stato_corrente == STATO_GIOCO) {
            // Rendering del gioco con sfondo meno scuro
            SDL_SetRenderDrawColor(renderer, 25, 15, 10, 255);
            SDL_RenderClear(renderer);

            disegna_condotto(renderer);
            disegna_insidie(renderer, insidie, 8); // Disegna le insidie
            disegna_magma(renderer, magma);
            disegna_faglie(renderer, faglie, 5);
            
            // Disegna tutte le bolle di gas
            for (int i = 0; i < 3; i++) {
                disegna_gas(renderer, gas_bubbles[i]);
            }
            
            disegna_acqua(renderer, molecola);
            disegna_countdown(renderer, countdown);
            disegna_temperatura(renderer, magma.temperatura);
            disegna_viscosita(renderer, viscosita_corrente); // Nuovo indicatore di viscosità
            disegna_indicatore_fase(renderer, (int)magma.y); // Nuovo indicatore di fase

            // DEBUG: Mostra posizione magma e telecamera
            char debug_info[100];
            sprintf(debug_info, "MAGMA Y: %.0f CAMERA: %d", magma.y, mappa_offset);
            disegna_stringa(renderer, debug_info, 10, HEIGHT - 30, 8);
            
            // Crosshair al centro dello schermo per vedere dove dovrebbe essere il magma
            SDL_SetRenderDrawColor(renderer, 255, 255, 0, 255);
            SDL_RenderDrawLine(renderer, WIDTH/2 - 10, HEIGHT/2, WIDTH/2 + 10, HEIGHT/2);
            SDL_RenderDrawLine(renderer, WIDTH/2, HEIGHT/2 - 10, WIDTH/2, HEIGHT/2 + 10);

            disegna_bordo_incandescente(renderer, (int)magma.y);
            disegna_particelle(renderer, frame);
            frame++;
        }
        else if (stato_corrente == STATO_ERUZIONE) {
            // Disegna l'eruzione spettacolare
            Uint32 tempo_eruzione = SDL_GetTicks() - tempo_inizio_eruzione;
            disegna_eruzione(renderer, tempo_eruzione);
        }
        else if (stato_corrente == STATO_GAME_OVER) {
            disegna_game_over(renderer, temperatura_finale, tempo_rimanente);
        }
        else if (stato_corrente == STATO_VITTORIA) {
            disegna_vittoria(renderer, temperatura_finale, tempo_impiegato);
        }

        SDL_RenderPresent(renderer);
        SDL_Delay(1000 / FPS);
    }

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
