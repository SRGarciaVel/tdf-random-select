#!/usr/bin/env python3
import asyncio
import sys
import threading

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from backend.app import create_app, socketio
from control_panel.main_window import MainWindow

BACKEND_HOST = "localhost"
BACKEND_PORT = 5001


def _run_backend() -> None:
    # allow_unsafe_werkzeug: el server de desarrollo de Flask-SocketIO no
    # está pensado para correr fuera del thread principal por defecto.
    # Es intencional acá porque el thread principal lo ocupa Qt (ver
    # SPECS.md §7) — no es apto para producción expuesta a internet, pero
    # esto solo escucha en localhost para el Browser Source de OBS.
    app = create_app()
    socketio.run(
        app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


def main() -> int:
    backend_thread = threading.Thread(target=_run_backend, daemon=True)
    backend_thread.start()

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    sys.exit(main())
