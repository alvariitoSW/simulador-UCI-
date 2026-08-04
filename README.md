# Simulador UCI

Videojuego indie en 2D (Python + Pygame) para estudiar cuidados intensivos mientras juegas.
Manejas un monitor de signos vitales en tiempo real y tomas decisiones clínicas: fluidos,
fármacos, ventilación mecánica y reanimación cardiopulmonar.

> ⚠️ Proyecto educativo e informal. No sustituye la formación clínica ni los protocolos
> oficiales (ACLS, guías de sepsis, ARDSnet, etc.). Los modelos fisiológicos están
> simplificados para que el juego sea divertido y comprensible, no para ser exactos al 100%.

## Requisitos

- Python 3.9+
- [Pygame](https://www.pygame.org/) 2.5+

## Instalación y ejecución

```bash
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

## Controles

- **Ratón**: usar los botones y deslizadores del panel de acciones.
- **Barra espaciadora**: dar compresiones torácicas (RCP) durante un paro cardiorrespiratorio.
- **ESC**: volver a la selección de casos durante una partida.

## Casos clínicos incluidos

1. **Shock séptico** — reanimación con cristaloides, noradrenalina y antibiótico precoz.
   Objetivo: TAM ≥ 65 mmHg, frecuencia cardiaca controlada y lactato en descenso.
2. **Insuficiencia respiratoria aguda (SDRA)** — decide cuándo intubar y ajusta el
   ventilador (volumen tidal protector, PEEP, FiO2) evitando hipoxemia y barotrauma.
3. **Paro cardiorrespiratorio (ACLS)** — RCP de alta calidad, desfibrilación y epinefrina
   según protocolo hasta lograr el retorno de la circulación espontánea (RCE).
4. **Sedación y analgesia** — titula propofol y fentanilo para lograr una sedación ligera
   y objetivo (escala RASS -1 a 0), evitando sobresedación y agitación peligrosa.

Cada caso termina con una pantalla de resultados que resume la puntuación obtenida y una
lista de **puntos clave para estudiar**, pensada como repaso rápido del tema.

El progreso (mejores puntuaciones y estrellas por caso) se guarda localmente en
`save/progress.json` (no se versiona en git).

## Estructura del proyecto

```
main.py                 Punto de entrada
game/
  app.py                Bucle principal y gestor de escenas
  constants.py           Colores, tamaños de pantalla, rangos normales de signos vitales
  progress.py            Guardado/carga de progreso local
  scenes/                Pantallas del juego (menú, selección, partida, resultados)
  ui/                     Widgets reutilizables y el monitor de signos vitales
  sim/                    Modelo fisiológico del paciente, fármacos, ventilador y RCP
  cases/                  Los 4 casos clínicos jugables
save/                    Progreso guardado localmente (ignorado por git)
```

## Añadir un nuevo caso clínico

Cada caso es una clase en `game/cases/` que hereda de `BaseCase`
(`game/cases/base.py`) e implementa `create_widgets()` (panel de acciones) y
`update(dt_sim, dt_real, cpr_tracker)` (fisiología y condiciones de victoria/derrota).
Regístralo añadiéndolo a la lista `CASES` en `game/cases/registry.py`.
