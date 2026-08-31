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


@socketio.on("ban_candidate_preview")
def handle_ban_candidate_preview(payload: dict) -> None:
    """Reenvía el personaje que el staff tiene seleccionado (pero no
    confirmado) en el panel - estado efimero de UI, no toca la base
    (checkpoint HUD-4: seleccionar + "Bloquear", ver ROADMAP.md).
    payload: {"character_id": str | None, "player_id": int | None}
    """
    emit("ban_candidate_preview", payload, broadcast=True)
