# TDF Random Select

Herramienta de escritorio para Windows que arma el draft de selección
random de personaje (Street Fighter 6) en torneos de **TDF e-deportes**:
baneo alternado de personajes sobre una grilla compartida y asignación
random del personaje final por jugador, con overlay en vivo integrado a
OBS Studio.

Proyecto independiente de `tdf-edeportes` (la web del club) — sin
dependencia de Render/Vercel/Supabase.

## Qué hace

- **Panel de control** (staff): arma el match, corre el baneo alternado,
  dispara el random, controla el reveal.
- **Overlay para OBS**: grilla de personajes con retratos oficiales,
  animación de baneo y de reveal, pensada como Browser Source.
- **Integración con OBS**: cambia de escena automáticamente al iniciar el
  draft, vuelve a la escena anterior al terminar (con override manual).
- **Todo local**: SQLite propio, sin depender de la web del club para
  funcionar durante el stream.

## Stack

| Capa                | Tecnología                                  |
|----------------------|-----------------------------------------------|
| Panel de control      | Python, PyQt6, `qasync`                       |
| Backend embebido       | Flask, flask-socketio, SQLite (SQLAlchemy)     |
| Overlay                | React + Vite + TypeScript, `socket.io-client`  |
| Integración OBS         | `obsws-python` (OBS WebSocket v5)              |
| Empaquetado             | PyInstaller (`.exe` para Windows)              |

Arquitectura de referencia: [TournamentStreamHelper](https://github.com/joaorb64/TournamentStreamHelper)
(MIT) — ver `SPECS.md §2` para el detalle de qué se toma de ahí y qué se
hace distinto.

## Estructura del proyecto

```
tdf-random-select/
├── SPECS.md                  # especificación técnica completa
├── README.md                  # este archivo
├── CODESTYLE.md                # reglas de estilo de código
├── ROADMAP.md                  # hoja de ruta del proyecto
├── AGENTS.md                    # orden de trabajo obligatorio en el repo
├── main.py                      # entry point: PyQt6 + qasync
├── backend/
│   └── app/
│       ├── __init__.py           # factory de Flask + flask-socketio
│       ├── models/                # SQLAlchemy (SQLite local)
│       ├── services/
│       │   └── obs_service.py      # obsws-python
│       └── sockets/                 # eventos Socket.IO (ban, reveal, etc.)
├── control_panel/                 # widgets PyQt6 del panel de staff
├── overlay_app/                    # React + Vite + TS (build servido por Flask)
└── tasks/
    └── lessons.md                   # lecciones aprendidas del proyecto
```

## Cómo correrlo (desarrollo local)

Requiere Python 3.11+, Node 20+, y una instancia de OBS Studio 28+ con
OBS WebSocket habilitado (Tools → WebSocket Server Settings) para probar
la integración real.

```bash
git clone <repo-url> tdf-random-select
cd tdf-random-select

# Backend + panel de control
python -m venv .venv
source .venv/bin/activate        # o .venv\Scripts\activate en Windows
pip install -r requirements.txt

# Overlay
cd overlay_app
npm install
npm run build                     # genera overlay_app/build, servido por Flask
cd ..

python main.py
```

## Roadmap

Ver `ROADMAP.md` para el orden de construcción, empezando por el walking
skeleton (ver `SPECS.md §7`).
