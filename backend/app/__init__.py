from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO
from sqlalchemy.orm import sessionmaker

# El build de Vite se sirve como estático directo desde Flask, sin
# depender de un servidor de archivos aparte (ver SPECS.md §7).
OVERLAY_BUILD_DIR = Path(__file__).resolve().parents[2] / "overlay_app" / "build"

socketio = SocketIO(cors_allowed_origins="*")


def create_app(session_factory: sessionmaker | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(OVERLAY_BUILD_DIR),
        static_url_path="",
    )
    app.config["SECRET_KEY"] = "dev-only-not-used-for-auth"

    if session_factory is None:
        # Fallback para tests/scripts que no le pasan uno explicito -
        # main.py siempre pasa el session_factory real, compartido con
        # el resto de la app, para no abrir un engine nuevo por request.
        from backend.app.models import get_engine, get_session_factory

        session_factory = get_session_factory(get_engine())
    app.config["SESSION_FACTORY"] = session_factory

    from backend.app.sockets import events  # noqa: F401  (registra los handlers)

    socketio.init_app(app)

    @app.get("/api/roster")
    def get_roster():
        from flask import jsonify

        from backend.app.data.sf6_roster import SF6_ROSTER

        return jsonify(SF6_ROSTER)

    @app.get("/api/broadcast-settings")
    def get_broadcast_settings_endpoint():
        from flask import jsonify

        from backend.app.services.broadcast_settings_service import (
            get_broadcast_settings,
        )

        with app.config["SESSION_FACTORY"]() as session:
            settings = get_broadcast_settings(session)
            logo_url = None
            if settings.logo_choice == "tdf":
                logo_url = "/branding/tdf-logo.webp"
            elif settings.custom_logo_filename:
                logo_url = f"/branding/{settings.custom_logo_filename}"

            return jsonify(
                {
                    "tournament_label": settings.tournament_label,
                    "logo_choice": settings.logo_choice,
                    "logo_url": logo_url,
                }
            )

    @app.get("/health")
    def health() -> tuple[str, int]:
        return "ok", 200

    @app.get("/")
    def serve_overlay_index():
        # Flask no mapea "/" a index.html automaticamente aunque
        # static_folder este configurado - hay que exponerlo a mano.
        return app.send_static_file("index.html")

    return app
