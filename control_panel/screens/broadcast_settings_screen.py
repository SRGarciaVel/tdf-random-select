from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.paths import BRANDING_DIR
from backend.app.services.broadcast_preset_service import (
    apply_preset,
    delete_preset,
    list_presets,
    save_preset,
)
from backend.app.services.broadcast_settings_service import (
    get_broadcast_settings,
    update_broadcast_settings,
)
from control_panel.theme import icon, icon_danger, mark_as_primary_action


class BroadcastSettingsScreen(QWidget):
    """Configuracion de la transmision (checkpoint HUD-2 + UI-5, ver
    ROADMAP.md) - nombre/logo del panel central del HUD, colores,
    logo de auspiciador, timer de baneo, presets guardados, y una vista
    previa en vivo. Reorganizada por completo en el checkpoint UI-5 -
    antes era solo nombre/logo/colores y quedaba subutilizada, a pedido
    explicito de Seba de "repensar el enfoque de esta pestaña".
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._pending_logo_filename: str | None = None

        # --- Nombre y logo del torneo ---
        self._label_input = QLineEdit()
        self._label_input.setPlaceholderText(
            "Vacío usa el nombre real del torneo activo"
        )
        self._label_input.textChanged.connect(self._update_preview)

        self._logo_choice_selector = QComboBox()
        self._logo_choice_selector.addItem("Logo de TDF", "tdf")
        self._logo_choice_selector.addItem("Logo del torneo", "torneo")
        self._logo_choice_selector.currentIndexChanged.connect(
            self._on_logo_choice_changed
        )

        self._logo_file_label = QLabel("Sin logo de torneo cargado.")
        self._logo_pick_button = QPushButton(
            icon("fa5s.image"), "Elegir logo del torneo..."
        )
        self._logo_pick_button.clicked.connect(self._on_pick_logo_clicked)

        name_form = QFormLayout()
        name_form.addRow("Nombre a mostrar", self._label_input)
        name_form.addRow("Logo", self._logo_choice_selector)
        name_form.addRow(self._logo_pick_button)
        name_form.addRow(self._logo_file_label)
        name_box = QGroupBox("Torneo")
        name_box.setLayout(name_form)

        # --- Colores del HUD (checkpoint HUD-5) ---
        self._accent_color = "#c400ff"
        self._panel_background_color = "rgba(5, 5, 6, 0.85)"

        self._accent_color_button = QPushButton(
            icon("fa5s.palette"), "Elegir color de acento..."
        )
        self._accent_color_button.clicked.connect(self._on_pick_accent_color)
        self._accent_color_swatch = QLabel()
        self._accent_color_swatch.setFixedSize(28, 20)
        accent_row = QHBoxLayout()
        accent_row.addWidget(self._accent_color_button)
        accent_row.addWidget(self._accent_color_swatch)

        self._panel_bg_button = QPushButton(
            icon("fa5s.fill-drip"), "Elegir fondo de paneles..."
        )
        self._panel_bg_button.clicked.connect(self._on_pick_panel_background)
        self._panel_bg_swatch = QLabel()
        self._panel_bg_swatch.setFixedSize(28, 20)
        panel_bg_row = QHBoxLayout()
        panel_bg_row.addWidget(self._panel_bg_button)
        panel_bg_row.addWidget(self._panel_bg_swatch)

        colors_form = QFormLayout()
        colors_form.addRow("Color de acento", accent_row)
        colors_form.addRow("Fondo de paneles", panel_bg_row)
        colors_box = QGroupBox("Colores del HUD")
        colors_box.setLayout(colors_form)

        # --- Timer de baneo (checkpoint UI-5) - antes era una constante
        # fija en el codigo (BAN_TIMER_MS en banning_screen.py), ahora
        # configurable acá sin tocar nada.
        self._ban_timer_input = QSpinBox()
        self._ban_timer_input.setRange(5, 300)
        self._ban_timer_input.setSuffix(" s")
        timer_form = QFormLayout()
        timer_form.addRow("Timer de baneo", self._ban_timer_input)
        timer_box = QGroupBox("Timer")
        timer_box.setLayout(timer_form)

        # --- Vista previa en vivo (checkpoint UI-5) - se actualiza sola
        # mientras se tocan los campos, sin tener que guardar primero e
        # ir a mirar OBS/el navegador cada vez.
        self._preview_frame = QFrame()
        self._preview_frame.setFixedHeight(84)
        self._preview_logo_label = QLabel()
        self._preview_logo_label.setFixedSize(48, 48)
        self._preview_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_text_label = QLabel("")
        self._preview_text_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        preview_inner = QHBoxLayout()
        preview_inner.addWidget(self._preview_logo_label)
        preview_inner.addWidget(self._preview_text_label, stretch=1)
        self._preview_frame.setLayout(preview_inner)
        preview_box = QGroupBox("Vista previa")
        preview_box_layout = QVBoxLayout()
        preview_box_layout.addWidget(self._preview_frame)
        preview_box.setLayout(preview_box_layout)

        # --- Presets guardados (checkpoint UI-5) ---
        self._preset_selector = QComboBox()
        apply_preset_button = QPushButton(icon("fa5s.check"), "Aplicar")
        apply_preset_button.clicked.connect(self._on_apply_preset_clicked)
        delete_preset_button = QPushButton(icon_danger("fa5s.trash"), "Eliminar")
        delete_preset_button.clicked.connect(self._on_delete_preset_clicked)
        preset_apply_row = QHBoxLayout()
        preset_apply_row.addWidget(self._preset_selector, stretch=1)
        preset_apply_row.addWidget(apply_preset_button)
        preset_apply_row.addWidget(delete_preset_button)

        save_preset_button = QPushButton(
            icon("fa5s.bookmark"), "Guardar configuración actual como preset..."
        )
        save_preset_button.clicked.connect(self._on_save_preset_clicked)

        presets_layout = QVBoxLayout()
        presets_layout.addLayout(preset_apply_row)
        presets_layout.addWidget(save_preset_button)
        presets_box = QGroupBox("Presets")
        presets_box.setLayout(presets_layout)

        # --- Guardar ---
        save_button = QPushButton(icon("fa5s.save", primary=True), "Guardar")
        save_button.clicked.connect(self._on_save_clicked)
        mark_as_primary_action(save_button)
        save_button.setMaximumWidth(320)
        self._status_label = QLabel("")

        # --- Checklist "antes de salir al aire" (checkpoint UI-5) -
        # recordatorio estatico, no interactivo, apuntando a cosas que
        # viven en otras pestañas.
        checklist_label = QLabel(
            "Antes de salir al aire:\n"
            "• Escena de baneo configurada en la pestaña OBS\n"
            "• Torneo y jugadores correctos elegidos en Setup\n"
            "• Partidas de prueba viejas limpiadas en Baneo\n"
            "• Timer de baneo (arriba) es el que querés usar hoy"
        )
        checklist_label.setProperty("secondary", "true")
        checklist_box = QGroupBox("Antes de salir al aire")
        checklist_layout = QVBoxLayout()
        checklist_layout.addWidget(checklist_label)
        checklist_box.setLayout(checklist_layout)

        layout = QVBoxLayout()
        layout.addWidget(name_box)
        layout.addWidget(colors_box)
        layout.addWidget(timer_box)
        layout.addWidget(preview_box)
        layout.addWidget(presets_box)
        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._status_label)
        layout.addWidget(
            QLabel(
                "Nota: si ya tenés el HUD abierto en OBS, hace falta "
                "actualizar esa fuente de navegador para ver los cambios\n"
                "(clic derecho sobre la fuente → Actualizar)."
            )
        )
        layout.addWidget(checklist_box)
        layout.addStretch()
        self.setLayout(layout)

        self._load_current_settings()
        self._reload_presets()

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
        self._accent_color = settings.accent_color
        self._panel_background_color = settings.panel_background_color
        self._ban_timer_input.setValue(settings.ban_timer_seconds)
        self._update_color_swatches()
        self._on_logo_choice_changed()
        self._update_preview()

    def _on_logo_choice_changed(self) -> None:
        is_torneo = self._logo_choice_selector.currentData() == "torneo"
        self._logo_pick_button.setEnabled(is_torneo)
        self._update_preview()

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
        self._update_preview()

    def _on_pick_accent_color(self) -> None:
        color = QColorDialog.getColor(
            QColor(self._accent_color), self, "Color de acento"
        )
        if color.isValid():
            self._accent_color = color.name()  # "#rrggbb"
            self._update_color_swatches()
            self._update_preview()

    def _on_pick_panel_background(self) -> None:
        color = QColorDialog.getColor(
            QColor(0, 0, 0),
            self,
            "Fondo de paneles",
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self._panel_background_color = (
                f"rgba({color.red()}, {color.green()}, {color.blue()}, "
                f"{color.alphaF():.2f})"
            )
            self._update_color_swatches()
            self._update_preview()

    def _update_color_swatches(self) -> None:
        self._accent_color_swatch.setStyleSheet(
            f"background-color: {self._accent_color}; border: 1px solid #666;"
        )
        self._panel_bg_swatch.setStyleSheet(
            f"background-color: {self._panel_background_color}; border: 1px solid #666;"
        )

    def _update_preview(self) -> None:
        """Se llama cada vez que se toca un campo relevante - checkpoint
        UI-5, vista previa en vivo sin tener que guardar primero."""
        label_text = self._label_input.text().strip() or "Nombre del torneo activo"
        self._preview_text_label.setText(label_text)
        self._preview_frame.setStyleSheet(
            f"background-color: {self._panel_background_color}; "
            f"border: 2px solid {self._accent_color}; border-radius: 6px;"
        )
        self._preview_text_label.setStyleSheet(
            f"color: {self._accent_color}; font-weight: 700; font-size: 13pt; "
            "border: none; background: transparent;"
        )

        self._preview_logo_label.clear()
        if self._logo_choice_selector.currentData() == "torneo":
            filename = self._current_logo_filename()
            if filename:
                path = BRANDING_DIR / filename
                if path.exists():
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        self._preview_logo_label.setPixmap(
                            pixmap.scaled(
                                48,
                                48,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )

    def _current_logo_filename(self) -> str:
        if self._pending_logo_filename:
            return self._pending_logo_filename
        with self._session_factory() as session:
            settings = get_broadcast_settings(session)
        return settings.custom_logo_filename or ""

    def _reload_presets(self) -> None:
        with self._session_factory() as session:
            presets = list_presets(session)
        self._preset_selector.clear()
        for preset in presets:
            self._preset_selector.addItem(preset.name, preset.id)

    def _on_save_preset_clicked(self) -> None:
        name, ok = QInputDialog.getText(self, "Guardar preset", "Nombre del preset:")
        if not ok:
            return
        # guarda lo que ya esta en la base - primero pisa/actualiza la
        # fila real con lo que hay tipeado en pantalla, despues clona
        # eso a un preset con nombre.
        self._on_save_clicked(show_status=False)
        try:
            with self._session_factory() as session:
                save_preset(session, name)
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar el preset", str(exc))
            return
        self._reload_presets()
        self._status_label.setText(f"Preset '{name.strip()}' guardado.")

    def _on_apply_preset_clicked(self) -> None:
        preset_id = self._preset_selector.currentData()
        if preset_id is None:
            return
        with self._session_factory() as session:
            apply_preset(session, preset_id)
        self._pending_logo_filename = None
        self._load_current_settings()
        self._status_label.setText(
            f"Preset '{self._preset_selector.currentText()}' aplicado."
        )

    def _on_delete_preset_clicked(self) -> None:
        preset_id = self._preset_selector.currentData()
        if preset_id is None:
            return
        preset_name = self._preset_selector.currentText()
        confirm = QMessageBox.question(
            self, "Eliminar preset", f"¿Eliminar el preset '{preset_name}'?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        with self._session_factory() as session:
            delete_preset(session, preset_id)
        self._reload_presets()
        self._status_label.setText(f"Preset '{preset_name}' eliminado.")

    def _on_save_clicked(self, show_status: bool = True) -> None:
        try:
            with self._session_factory() as session:
                update_broadcast_settings(
                    session,
                    self._label_input.text(),
                    self._logo_choice_selector.currentData(),
                    self._pending_logo_filename,
                    accent_color=self._accent_color,
                    panel_background_color=self._panel_background_color,
                    ban_timer_seconds=self._ban_timer_input.value(),
                )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))
            return

        self._pending_logo_filename = None
        if show_status:
            self._status_label.setText("Guardado.")
        self._load_current_settings()
