from __future__ import annotations

import socketio as socketio_client
from PyQt6.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from backend.app.services.obs_service import ObsConnectionError, ObsService

BACKEND_URL = "http://localhost:5001"


class MainWindow(QMainWindow):
    """Ventana mínima del walking skeleton (SPECS.md §7).

    Se reemplaza por las pantallas reales de setup/baneo/config de OBS
    en la Fase 2 del ROADMAP.md.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TDF Random Select — walking skeleton")
        self.resize(420, 220)

        self._sio = socketio_client.Client()
        self._obs = ObsService()

        self._status_label = QLabel("Sin conexión al backend todavía.")
        ping_button = QPushButton("Ping")
        ping_button.clicked.connect(self._on_ping_clicked)

        obs_button = QPushButton("Test OBS")
        obs_button.clicked.connect(self._on_test_obs_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self._status_label)
        layout.addWidget(ping_button)
        layout.addWidget(obs_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _ensure_socket_connected(self) -> None:
        if not self._sio.connected:
            self._sio.connect(BACKEND_URL, wait_timeout=10)

    def _on_ping_clicked(self) -> None:
        try:
            self._ensure_socket_connected()
            self._sio.emit("ping_from_control_panel", {"message": "ping desde el panel"})
            self._status_label.setText("Ping enviado al backend.")
        except Exception as exc:
            self._status_label.setText(f"Error de conexión al backend: {exc}")

    def _on_test_obs_clicked(self) -> None:
        try:
            self._obs.connect()
            scenes = self._obs.list_scenes()
            QMessageBox.information(self, "Escenas de OBS", "\n".join(scenes) or "Sin escenas.")
        except ObsConnectionError as exc:
            QMessageBox.warning(self, "No se pudo conectar a OBS", str(exc))
