#!/usr/bin/env python3
import asyncio
import sys
import threading

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from backend.app import create_app, socketio
from backend.app.models import get_engine, get_session_factory, init_db
from control_panel.main_window import MainWindow

BACKEND_HOST = "localhost"
BACKEND_PORT = 5001


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

    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    sys.exit(main())
