from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from control_panel.theme import mark_as_primary_action

from backend.app.services.obs_settings_service import (
    get_obs_settings,
    update_obs_settings,
)
from backend.app.services.obs_service import ObsConnectionError, ObsService


class ObsSettingsScreen(QWidget):
    """Configuración de conexión a OBS (Fase 4, ver ROADMAP.md) -
    reemplaza las variables de entorno OBS_HOST/OBS_PORT/OBS_PASSWORD
    del walking skeleton (ver DiagnosticsScreen, que las seguía usando
    directo) por una fila real en la base, igual criterio que
    BroadcastSettingsScreen.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory

        self._host_input = QLineEdit()
        self._port_input = QLineEdit()
        self._port_input.setPlaceholderText("4455")
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Editable=True: no hace falta que OBS este prendido para
        # guardar un nombre de escena a mano, pero "Probar conexion" lo
        # completa solo con las escenas reales si OBS SI esta arriba.
        self._draft_scene_selector = QComboBox()
        self._draft_scene_selector.setEditable(True)

        test_button = QPushButton("Probar conexión")
        test_button.clicked.connect(self._on_test_connection_clicked)
        self._test_status_label = QLabel("")

        save_button = QPushButton("Guardar")
        save_button.clicked.connect(self._on_save_clicked)
        mark_as_primary_action(save_button)
        self._save_status_label = QLabel("")

        form = QFormLayout()
        form.addRow("Host", self._host_input)
        form.addRow("Puerto", self._port_input)
        form.addRow("Contraseña", self._password_input)
        form.addRow("Escena de baneo", self._draft_scene_selector)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(test_button)
        layout.addWidget(self._test_status_label)
        layout.addWidget(save_button)
        layout.addWidget(self._save_status_label)
        layout.addWidget(
            QLabel(
                "Al apretar 'Iniciar baneo' el panel guarda la escena que\n"
                "esté activa en OBS y cambia a la escena de baneo elegida\n"
                "acá - vuelve sola a la escena original al completar el\n"
                "reveal. Si OBS no está prendido, el draft sigue andando\n"
                "igual (no se bloquea nada)."
            )
        )
        layout.addStretch()
        self.setLayout(layout)

        self._load_current_settings()

    def _load_current_settings(self) -> None:
        with self._session_factory() as session:
            settings = get_obs_settings(session)
        self._host_input.setText(settings.host)
        self._port_input.setText(str(settings.port))
        self._password_input.setText(settings.password or "")
        if settings.draft_scene_name:
            self._draft_scene_selector.setEditText(settings.draft_scene_name)

    def _build_obs_service(self) -> ObsService:
        port_text = self._port_input.text().strip() or "4455"
        try:
            port = int(port_text)
        except ValueError:
            port = 4455
        return ObsService(
            host=self._host_input.text().strip() or "localhost",
            port=port,
            password=self._password_input.text(),
        )

    def _on_test_connection_clicked(self) -> None:
        obs = self._build_obs_service()
        try:
            obs.connect()
            scenes = obs.list_scenes()
        except ObsConnectionError as exc:
            self._test_status_label.setText(f"No se pudo conectar: {exc}")
            return

        current_text = self._draft_scene_selector.currentText()
        self._draft_scene_selector.clear()
        self._draft_scene_selector.addItems(scenes)
        # si lo que ya estaba tipeado/guardado sigue siendo una escena
        # valida, la dejamos seleccionada en vez de perderla.
        index = self._draft_scene_selector.findText(current_text)
        if index >= 0:
            self._draft_scene_selector.setCurrentIndex(index)
        elif current_text:
            self._draft_scene_selector.setEditText(current_text)

        self._test_status_label.setText(
            f"Conectado. {len(scenes)} escena(s) encontrada(s)."
        )

    def _on_save_clicked(self) -> None:
        try:
            port = int(self._port_input.text().strip() or "4455")
        except ValueError:
            QMessageBox.warning(
                self, "No se pudo guardar", "El puerto debe ser un número."
            )
            return

        try:
            with self._session_factory() as session:
                update_obs_settings(
                    session,
                    self._host_input.text(),
                    port,
                    self._password_input.text(),
                    self._draft_scene_selector.currentText(),
                )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))
            return

        self._save_status_label.setText("Guardado.")
