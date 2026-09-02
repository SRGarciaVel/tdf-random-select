from pathlib import Path

from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from sqlalchemy.orm import sessionmaker

# El build de Vite se sirve como estático directo desde Flask, sin
# depender de un servidor de archivos aparte (ver SPECS.md §7).
OVERLAY_BUILD_DIR = Path(__file__).resolve().parents[2] / "overlay_app" / "build"

# Retratos y branding se sirven DIRECTO desde overlay_app/public/, no
# desde el build de Vite (fix real, checkpoint UX-2 - ver ROADMAP.md).
# Antes estos archivos solo se veian despues de correr "npm run build"
# (Vite copia el contenido de public/ tal cual al build, sin transformar
# nada - confirmado corriendo un build real) - funcionaba bien cuando
# Seba es quien arma todo a mano en WSL2 con una terminal, pero una vez
# empaquetado en .exe, el CEO/streamer no tiene Node ni una terminal
# para correr eso. Sirviendo directo desde public/, copiar un archivo
# nuevo ahi (que es exactamente lo que ya hace el panel al elegir un
# logo, o download_portraits.py al bajar un retrato) alcanza solo - cero
# pasos extra para el usuario final.
OVERLAY_PUBLIC_DIR = Path(__file__).resolve().parents[2] / "overlay_app" / "public"
PORTRAITS_DIR = OVERLAY_PUBLIC_DIR / "portraits"
PORTRAITS_LARGE_DIR = OVERLAY_PUBLIC_DIR / "portraits-large"
BRANDING_DIR = OVERLAY_PUBLIC_DIR / "branding"

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

            sponsor_logo_url = None
            if settings.sponsor_logo_filename:
                sponsor_logo_url = f"/branding/{settings.sponsor_logo_filename}"

            return jsonify(
                {
                    "tournament_label": settings.tournament_label,
                    "logo_choice": settings.logo_choice,
                    "logo_url": logo_url,
                    "accent_color": settings.accent_color,
                    "panel_background_color": settings.panel_background_color,
                    "sponsor_logo_url": sponsor_logo_url,
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
