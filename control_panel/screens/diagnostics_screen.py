from __future__ import annotations

import os

import socketio as socketio_client
from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from backend.app.services.obs_service import ObsConnectionError, ObsService

BACKEND_URL = "http://localhost:5001"


class DiagnosticsScreen(QWidget):
    """Ping al backend + Test OBS, heredado del walking skeleton (SPECS.md
    §7). Se mantiene como pantalla propia porque sigue siendo util para
    diagnosticar problemas de conexion sin tener que armar un match real.
    """

    def __init__(self) -> None:
        super().__init__()

        self._sio = socketio_client.Client()
        # Configurable por env var mientras no existe la pantalla de
        # configuracion de OBS real (obs_settings, ver ROADMAP.md Fase 2).
        # Necesario para probar desde WSL2 en modo NAT, donde "localhost"
        # no apunta al Windows host real (ver tasks/lessons.md).
        obs_host = os.environ.get("OBS_HOST", "localhost")
        obs_port = int(os.environ.get("OBS_PORT", "4455"))
        obs_password = os.environ.get("OBS_PASSWORD", "")
        self._obs = ObsService(host=obs_host, port=obs_port, password=obs_password)

        self._status_label = QLabel("Sin conexión al backend todavía.")
        ping_button = QPushButton("Ping")
        ping_button.clicked.connect(self._on_ping_clicked)

        obs_button = QPushButton("Test OBS")
        obs_button.clicked.connect(self._on_test_obs_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self._status_label)
        layout.addWidget(ping_button)
        layout.addWidget(obs_button)
        layout.addStretch()
        self.setLayout(layout)

    def _ensure_socket_connected(self) -> None:
        if not self._sio.connected:
            # wait_timeout default de la libreria es 1s - insuficiente cuando
            # el proceso esta bajo carga de renderizado por software (ver
            # tasks/lessons.md, caso WSLg sin GPU passthrough).
            self._sio.connect(BACKEND_URL, wait_timeout=10)

    def _on_ping_clicked(self) -> None:
        try:
            self._ensure_socket_connected()
            self._sio.emit(
                "ping_from_control_panel", {"message": "ping desde el panel"}
            )
            self._status_label.setText("Ping enviado al backend.")
        except Exception as exc:
            self._status_label.setText(f"Error de conexión al backend: {exc}")

    def _on_test_obs_clicked(self) -> None:
        try:
            self._obs.connect()
            scenes = self._obs.list_scenes()
            QMessageBox.information(
                self, "Escenas de OBS", "\n".join(scenes) or "Sin escenas."
            )
        except ObsConnectionError as exc:
            QMessageBox.warning(self, "No se pudo conectar a OBS", str(exc))
