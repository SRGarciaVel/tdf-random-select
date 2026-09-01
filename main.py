#!/usr/bin/env python3
import asyncio
import sys
import threading

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from backend.app import create_app, socketio
from backend.app.models import get_engine, get_session_factory, init_db
from backend.app.services.character_stats_service import warm_up_tdf_edeportes
from control_panel.main_window import MainWindow

BACKEND_HOST = "localhost"
BACKEND_PORT = 5001
# Cada cuanto se hace ping a tdf-edeportes para mantenerlo despierto
# (checkpoint HUD-10) - Render duerme la capa gratis a los 15 min sin
# trafico, este intervalo deja margen de sobra sin ser demasiado
# seguido.
WARMUP_INTERVAL_MS = 10 * 60 * 1000


def _run_backend(session_factory) -> None:
    # allow_unsafe_werkzeug: el server de desarrollo de Flask-SocketIO no
    # está pensado para correr fuera del thread principal por defecto.
    # Es intencional acá porque el thread principal lo ocupa Qt (ver
    # SPECS.md §7) — no es apto para producción expuesta a internet, pero
    # esto solo escucha en localhost para el Browser Source de OBS.
    app = create_app(session_factory)
    socketio.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


def _warm_up_in_background() -> None:
    # requests.get bloquea hasta 20s (ver character_stats_service.py) -
    # en un thread aparte para que el ping nunca trabe la UI de Qt.
    threading.Thread(target=warm_up_tdf_edeportes, daemon=True).start()


def main() -> int:
    engine = get_engine()
    init_db(engine)  # idempotente - solo crea tablas que no existen
    session_factory = get_session_factory(engine)

    backend_thread = threading.Thread(
        target=_run_backend, args=(session_factory,), daemon=True
    )
    backend_thread.start()

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(session_factory)
    window.show()

    # Precarga de tdf-edeportes: primera vez ya al arrancar (no esperar
    # los 10 minutos), despues en bucle - checkpoint HUD-10, a pedido de
    # Seba: "que cuando se necesite desplegar la informacion las
    # estadisticas ya esten despiertas". warmup_timer necesita quedar
    # referenciado mientras la app viva, si no Qt lo recolecta como
    # basura y deja de sonar.
    _warm_up_in_background()
    warmup_timer = QTimer()
    warmup_timer.timeout.connect(_warm_up_in_background)
    warmup_timer.start(WARMUP_INTERVAL_MS)

    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    sys.exit(main())
