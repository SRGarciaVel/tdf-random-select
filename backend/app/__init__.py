from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from sqlalchemy.orm import sessionmaker

from backend.app.paths import (
    BRANDING_DIR,
    OVERLAY_BUILD_DIR,
    PORTRAITS_DIR,
    PORTRAITS_LARGE_DIR,
)

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

    # Rutas explicitas para retratos/branding - Flask las resuelve antes
    # que la ruta estatica generica (static_url_path=""), asi que no
    # compiten con el resto de los archivos que si vienen del build.
    @app.get("/portraits/<path:filename>")
    def serve_portrait(filename: str):
        return send_from_directory(PORTRAITS_DIR, filename)

    @app.get("/portraits-large/<path:filename>")
    def serve_portrait_large(filename: str):
        return send_from_directory(PORTRAITS_LARGE_DIR, filename)

    @app.get("/branding/<path:filename>")
    def serve_branding(filename: str):
        return send_from_directory(BRANDING_DIR, filename)

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
                    "accent_color": settings.accent_color,
                    "panel_background_color": settings.panel_background_color,
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
