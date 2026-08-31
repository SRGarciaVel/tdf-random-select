from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO

# El build de Vite se sirve como estático directo desde Flask, sin
# depender de un servidor de archivos aparte (ver SPECS.md §7).
OVERLAY_BUILD_DIR = Path(__file__).resolve().parents[2] / "overlay_app" / "build"

socketio = SocketIO(cors_allowed_origins="*")


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(OVERLAY_BUILD_DIR),
        static_url_path="",
    )
    app.config["SECRET_KEY"] = "dev-only-not-used-for-auth"

    from backend.app.sockets import events  # noqa: F401  (registra los handlers)

    socketio.init_app(app)

    @app.get("/api/roster")
    def get_roster():
        from flask import jsonify

        from backend.app.data.sf6_roster import SF6_ROSTER

        return jsonify(SF6_ROSTER)

    @app.get("/health")
    def health() -> tuple[str, int]:
        return "ok", 200

    @app.get("/")
    def serve_overlay_index():
        # Flask no mapea "/" a index.html automaticamente aunque
        # static_folder este configurado - hay que exponerlo a mano.
        return app.send_static_file("index.html")

    return app
