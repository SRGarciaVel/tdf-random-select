from flask_socketio import emit

from backend.app import socketio


@socketio.on("ping_from_control_panel")
def handle_ping(payload: dict) -> None:
    """Reenvía el ping del panel de control a todos los overlays conectados.

    Solo existe para validar el camino completo del walking skeleton
    (ver SPECS.md §7): panel -> backend -> overlay. Se reemplaza por los
    eventos reales del draft (ban_started, character_banned, reveal, etc.)
    en la Fase 1.
    """
    message = payload.get("message", "")
    emit("ping_broadcast", {"message": message}, broadcast=True)
