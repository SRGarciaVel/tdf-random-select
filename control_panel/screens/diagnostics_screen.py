from __future__ import annotations

import socketio as socketio_client
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget
from sqlalchemy.orm import sessionmaker

from backend.app.services.obs_service import ObsConnectionError, ObsService
from backend.app.services.obs_settings_service import get_obs_settings

BACKEND_URL = "http://localhost:5001"


class DiagnosticsScreen(QWidget):
    """Ping al backend + Test OBS, heredado del walking skeleton (SPECS.md
    §7). Se mantiene como pantalla propia porque sigue siendo util para
    diagnosticar problemas de conexion sin tener que armar un match real.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory

        self._sio = socketio_client.Client()

        self._status_label = QLabel("Sin conexión al backend todavía.")
        ping_button = QPushButton("Ping")
        ping_button.clicked.connect(self._on_ping_clicked)
        ping_button.setMaximumWidth(320)

        obs_button = QPushButton("Test OBS")
        obs_button.clicked.connect(self._on_test_obs_clicked)
        obs_button.setMaximumWidth(320)

        layout = QVBoxLayout()
        layout.addWidget(self._status_label)
        layout.addWidget(ping_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(obs_button, alignment=Qt.AlignmentFlag.AlignHCenter)
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
        # Lee la config real de la pestaña OBS (checkpoint Fase 4) - antes
        # este boton usaba variables de entorno sueltas, heredadas del
        # walking skeleton de antes de que existiera esa pestaña, y
        # quedaban desactualizadas frente a lo que el staff configura de
        # verdad en la app.
        with self._session_factory() as session:
            settings = get_obs_settings(session)
        obs = ObsService(
            host=settings.host, port=settings.port, password=settings.password or ""
        )
        try:
            obs.connect()
            scenes = obs.list_scenes()
            QMessageBox.information(
                self, "Escenas de OBS", "\n".join(scenes) or "Sin escenas."
            )
        except ObsConnectionError as exc:
            QMessageBox.warning(self, "No se pudo conectar a OBS", str(exc))
