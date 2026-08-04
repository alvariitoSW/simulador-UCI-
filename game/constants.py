"""Constantes globales del juego."""

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "Simulador UCI"

# Cuánto tiempo simulado (segundos "de paciente") avanza por cada segundo real.
# Permite que escenarios de varios minutos se resuelvan en un par de minutos de juego.
SIM_TIME_SCALE = 6.0

# --- Paleta de colores (estilo monitor de UCI) ---
BLACK = (8, 10, 14)
PANEL_BG = (18, 22, 28)
PANEL_BG_LIGHT = (28, 34, 42)
WHITE = (235, 238, 240)
GREY = (140, 148, 156)
GREY_DARK = (70, 78, 86)
GREEN = (60, 220, 100)
GREEN_DARK = (30, 120, 60)
CYAN = (60, 210, 230)
YELLOW = (235, 210, 60)
ORANGE = (235, 150, 50)
RED = (235, 70, 70)
RED_DARK = (140, 30, 30)
BLUE = (90, 140, 235)
PURPLE = (170, 120, 235)
MAGENTA = (220, 90, 190)

# Rangos "normales" para alarmas
NORMAL_RANGES = {
    "hr": (60, 100),
    "sbp": (90, 140),
    "map": (65, 105),
    "spo2": (94, 100),
    "rr": (12, 20),
    "temp": (36.0, 37.8),
}
