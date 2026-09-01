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


@socketio.on("character_stats_update")
def handle_character_stats_update(payload: dict) -> None:
    """Reenvía las estadisticas de CFN del ultimo baneo confirmado -
    activado a mano por el staff con "Mostrar estadisticas" (checkpoint
    HUD-10, ver ROADMAP.md). payload siempre trae "visible": bool -
    visible=False esconde las estadisticas en el overlay (vuelve la
    carta a mostrar el retrato normal).
    """
    emit("character_stats_update", payload, broadcast=True)
