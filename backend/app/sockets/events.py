from flask_socketio import emit

from backend.app import socketio


@socketio.on("ping_from_control_panel")
def handle_ping(payload: dict) -> None:
    """Reenvía el ping del panel de control a todos los overlays conectados.

    Heredado del walking skeleton (SPECS.md §7) - se mantiene para
    diagnosticar la conexión sin armar un match real (pestaña
    "Diagnóstico" del panel).
    """
    message = payload.get("message", "")
    emit("ping_broadcast", {"message": message}, broadcast=True)


@socketio.on("match_state_update")
def handle_match_state_update(payload: dict) -> None:
    """Reenvía el estado del match a todos los overlays conectados.

    El panel de control emite esto después de cada acción del draft
    (Fase 3, ver SPECS.md y build_match_state_payload en
    backend/app/services/draft_service.py).
    """
    emit("match_state_update", payload, broadcast=True)
