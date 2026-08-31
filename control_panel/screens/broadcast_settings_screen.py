from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.services.broadcast_settings_service import (
    get_broadcast_settings,
    update_broadcast_settings,
)

# Mismo criterio que los retratos (download_portraits.py): los assets
# viven en overlay_app/public/, y requieren un "npm run build" despues
# para que el overlay los sirva de verdad.
BRANDING_DIR = (
    Path(__file__).resolve().parents[2] / "overlay_app" / "public" / "branding"
)


class BroadcastSettingsScreen(QWidget):
    """Configuracion del panel central del HUD de baneo (checkpoint
    HUD-2, ver ROADMAP.md) - nombre a mostrar y logo, a eleccion del CEO.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._pending_logo_filename: str | None = None

        self._label_input = QLineEdit()
        self._label_input.setPlaceholderText(
            "Vacío usa el nombre real del torneo activo"
        )

        self._logo_choice_selector = QComboBox()
        self._logo_choice_selector.addItem("Logo de TDF", "tdf")
        self._logo_choice_selector.addItem("Logo del torneo", "torneo")
        self._logo_choice_selector.currentIndexChanged.connect(
            self._on_logo_choice_changed
        )

        self._logo_file_label = QLabel("Sin logo de torneo cargado.")
        self._logo_pick_button = QPushButton("Elegir logo del torneo...")
        self._logo_pick_button.clicked.connect(self._on_pick_logo_clicked)

        save_button = QPushButton("Guardar")
        save_button.clicked.connect(self._on_save_clicked)
        self._status_label = QLabel("")

        form = QFormLayout()
        form.addRow("Nombre a mostrar", self._label_input)
        form.addRow("Logo", self._logo_choice_selector)
        form.addRow(self._logo_pick_button)
        form.addRow(self._logo_file_label)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addWidget(self._status_label)
        layout.addWidget(
            QLabel(
                "Nota: después de cambiar el logo hay que correr\n"
                "'npm run build' en overlay_app para que se vea en el HUD."
            )
        )
        layout.addStretch()
        self.setLayout(layout)

        self._load_current_settings()

    def _load_current_settings(self) -> None:
        with self._session_factory() as session:
            settings = get_broadcast_settings(session)
        self._label_input.setText(settings.tournament_label or "")
        index = self._logo_choice_selector.findData(settings.logo_choice)
        if index >= 0:
            self._logo_choice_selector.setCurrentIndex(index)
        if settings.custom_logo_filename:
            self._logo_file_label.setText(
                f"Archivo actual: {settings.custom_logo_filename}"
            )
        self._on_logo_choice_changed()

    def _on_logo_choice_changed(self) -> None:
        is_torneo = self._logo_choice_selector.currentData() == "torneo"
        self._logo_pick_button.setEnabled(is_torneo)

    def _on_pick_logo_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Elegir logo del torneo",
            "",
            "Imágenes (*.png *.webp *.jpg *.jpeg *.svg)",
        )
        if not file_path:
            return

        source = Path(file_path)
        BRANDING_DIR.mkdir(parents=True, exist_ok=True)
        destination_filename = f"torneo-logo{source.suffix.lower()}"
        destination = BRANDING_DIR / destination_filename
        shutil.copyfile(source, destination)

        self._pending_logo_filename = destination_filename
        self._logo_file_label.setText(
            f"Archivo elegido: {destination_filename} (falta Guardar)"
        )

    def _on_save_clicked(self) -> None:
        try:
            with self._session_factory() as session:
                update_broadcast_settings(
                    session,
                    self._label_input.text(),
                    self._logo_choice_selector.currentData(),
                    self._pending_logo_filename,
                )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))
            return

        self._pending_logo_filename = None
        self._status_label.setText("Guardado.")
        self._load_current_settings()
