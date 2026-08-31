from __future__ import annotations

import logging

import socketio as socketio_client

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:5001"


class OverlayBridge:
    """Único lugar donde las pantallas del panel hablan con el backend
    Socket.IO para empujar estado al overlay (CODESTYLE.md: una
    responsabilidad por módulo, evita duplicar la lógica de conexión que
    ya usa DiagnosticsScreen).
    """

    def __init__(self) -> None:
        self._sio = socketio_client.Client()

    def emit_match_state(self, payload: dict) -> None:
        try:
            if not self._sio.connected:
                # wait_timeout default de la libreria es 1s, insuficiente
                # bajo carga (ver tasks/lessons.md).
                self._sio.connect(BACKEND_URL, wait_timeout=10)
            self._sio.emit("match_state_update", payload)
        except Exception:
            # El overlay es secundario al draft en si - si el backend no
            # esta arriba, el panel debe seguir funcionando igual (mismo
            # criterio de modo degradado que ObsService, ver CODESTYLE.md).
            logger.warning("No se pudo empujar el estado al overlay.", exc_info=True)

    def emit_ban_candidate_preview(
        self, character_id: str | None, player_id: int | None
    ) -> None:
        """Avisa al overlay que personaje tiene seleccionado (sin
        confirmar) el staff en el panel - checkpoint HUD-4. Mismo modo
        degradado que emit_match_state si el backend no esta arriba.
        """
        try:
            if not self._sio.connected:
                self._sio.connect(BACKEND_URL, wait_timeout=10)
            self._sio.emit(
                "ban_candidate_preview",
                {"character_id": character_id, "player_id": player_id},
            )
        except Exception:
            logger.warning("No se pudo empujar el preview al overlay.", exc_info=True)
