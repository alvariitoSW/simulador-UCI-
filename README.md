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

- **Ratón / toque**: usar los botones y deslizadores del panel de acciones.
- **Barra espaciadora** (o el botón táctil "TOCA AQUÍ: COMPRIMIR" en pantalla): dar
  compresiones torácicas (RCP) durante un paro cardiorrespiratorio.
- **ESC**: volver a la selección de casos durante una partida.

## Jugar desde el móvil (versión web)

Pygame es una librería de escritorio, así que no corre nativamente en un navegador o app
de móvil. Para probarlo desde el teléfono, este proyecto está preparado para compilarse a
WebAssembly con [pygbag](https://github.com/pygame-web/pygbag) (código ya adaptado con un
bucle asíncrono y un botón táctil de RCP, ya que el móvil no tiene barra espaciadora).

Debes generarlo desde un ordenador con acceso normal a internet (pygbag descarga una
plantilla desde un CDN la primera vez):

```bash
pip install pygbag
pygbag main.py
```

Esto compila el juego y levanta un servidor local (por defecto en el puerto 8000).
Con el ordenador y el móvil en la **misma red WiFi**, abre en el navegador del móvil:

```
http://<IP-de-tu-ordenador-en-la-red-local>:8000
```

(la IP local se ve con `ipconfig` en Windows o `ip addr` / `ifconfig` en macOS/Linux).

Si en vez de un servidor temporal quieres un enlace permanente, compílalo una vez con
`pygbag --build main.py` (o `--archive` para generar un `.zip`) y sube el contenido de
`build/web/` a GitHub Pages, itch.io o cualquier hosting estático.

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
