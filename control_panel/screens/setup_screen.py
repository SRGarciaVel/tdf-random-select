from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from control_panel.theme import mark_as_primary_action

from backend.app.data.sf6_roster import SF6_ROSTER
from backend.app.models import Tournament
from backend.app.services.character_tag_service import (
    add_character_tag,
    delete_character_tag,
    list_character_tags,
)
from backend.app.services.draft_service import DraftService
from backend.app.services.player_service import list_players
from backend.app.services.tournament_service import (
    create_tournament,
    delete_tournament,
    list_tournaments,
)

# Valor centinela en el QComboBox de torneos para la opcion "crear nuevo".
NEW_TOURNAMENT_SENTINEL = "__new__"


class PlayerTagsPanel(QWidget):
    """ "Personajes fuertes conocidos" de un jugador (SPECS.md paragrafo 4) -
    solo referencia visual durante el baneo, nunca filtra la grilla."""

    def __init__(self, session_factory: sessionmaker, title: str) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._player_id: int | None = None

        self._character_selector = QComboBox()
        # El desplegable de este combo (31 personajes) se abria sin
        # limite, extendiendose fuera de la ventana en vez de mostrar
        # una barra de scroll propia - Seba lo encontro real al probar
        # (checkpoint UI-3, distinto del QListWidget de ya agregados,
        # que ya tenia su propio fix de alto). setMaxVisibleItems() le
        # pone techo al popup y Qt agrega scroll propio para el resto.
        self._character_selector.setMaxVisibleItems(10)
        for entry in SF6_ROSTER:
            self._character_selector.addItem(entry["display_name"], entry["id"])
        add_button = QPushButton("Agregar")
        add_button.clicked.connect(self._on_add_clicked)

        add_row = QHBoxLayout()
        add_row.addWidget(self._character_selector)
        add_row.addWidget(add_button)

        self._tags_list = QListWidget()
        self._tags_list.itemDoubleClicked.connect(self._on_remove_clicked)
        # Antes esta lista crecia sin limite y habia que agrandar toda
        # la ventana para ver una lista larga completa - con un maximo
        # fijo, QListWidget muestra su propia barra de scroll interna en
        # vez de empujar el resto del layout (checkpoint UI-3, a pedido
        # de Seba).
        self._tags_list.setMaximumHeight(140)

        layout = QVBoxLayout()
        layout.addWidget(
            QLabel(f"Personajes fuertes de {title} (doble clic para quitar)")
        )
        layout.addLayout(add_row)
        layout.addWidget(self._tags_list)
        self.setLayout(layout)

    def set_player(self, player_id: int | None) -> None:
        self._player_id = player_id
        self.refresh()

    def refresh(self) -> None:
        self._tags_list.clear()
        if self._player_id is None:
            return
        with self._session_factory() as session:
            tags = list_character_tags(session, self._player_id)
        for tag in tags:
            display_name = next(
                (
                    entry["display_name"]
                    for entry in SF6_ROSTER
                    if entry["id"] == tag.character_id
                ),
                tag.character_id,
            )
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, tag.id)
            self._tags_list.addItem(item)

    def _on_add_clicked(self) -> None:
        if self._player_id is None:
            QMessageBox.information(
                self,
                "Elige un jugador",
                "Selecciona el jugador arriba antes de agregar personajes.",
            )
            return
        character_id = self._character_selector.currentData()
        with self._session_factory() as session:
            add_character_tag(session, self._player_id, character_id)
        self.refresh()

    def _on_remove_clicked(self, item: QListWidgetItem) -> None:
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        with self._session_factory() as session:
            delete_character_tag(session, tag_id)
        self.refresh()


class SetupScreen(QWidget):
    """Arma un match nuevo: elige/crea torneo, elige Jugador A/B, carga
    personajes fuertes por jugador (Fase 2 checkpoint 2, ver ROADMAP.md).
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory

        self._tournament_selector = QComboBox()
        self._tournament_selector.currentIndexChanged.connect(
            self._on_tournament_selection_changed
        )
        self._delete_tournament_button = QPushButton("Eliminar torneo")
        self._delete_tournament_button.clicked.connect(
            self._on_delete_tournament_clicked
        )
        self._new_tournament_name = QLineEdit()
        self._new_tournament_name.setPlaceholderText("Nombre del torneo nuevo")
        self._new_tournament_bans = QSpinBox()
        self._new_tournament_bans.setRange(1, 10)
        self._new_tournament_bans.setValue(1)
        self._new_tournament_timeout_behavior = QComboBox()
        self._new_tournament_timeout_behavior.addItem("Banear al azar", "auto_ban")
        self._new_tournament_timeout_behavior.addItem("Saltar el turno", "skip")

        tournament_selector_row = QHBoxLayout()
        tournament_selector_row.addWidget(self._tournament_selector)
        tournament_selector_row.addWidget(self._delete_tournament_button)

        tournament_form = QFormLayout()
        tournament_form.addRow("Torneo", tournament_selector_row)
        tournament_form.addRow("Nombre torneo nuevo", self._new_tournament_name)
        tournament_form.addRow("Baneos por jugador", self._new_tournament_bans)
        tournament_form.addRow(
            "Si se agota el timer de 30s", self._new_tournament_timeout_behavior
        )
        tournament_box = QGroupBox("Torneo")
        tournament_box.setLayout(tournament_form)

        self._player_a_selector = QComboBox()
        self._player_b_selector = QComboBox()
        self._player_a_selector.currentIndexChanged.connect(self._on_player_a_changed)
        self._player_b_selector.currentIndexChanged.connect(self._on_player_b_changed)
        refresh_players_button = QPushButton("Refrescar jugadores")
        refresh_players_button.clicked.connect(self._reload_players)

        players_form = QFormLayout()
        players_form.addRow("Jugador A", self._player_a_selector)
        players_form.addRow("Jugador B", self._player_b_selector)
        players_form.addRow(refresh_players_button)
        players_box = QGroupBox("Jugadores")
        players_box.setLayout(players_form)

        self._tags_a = PlayerTagsPanel(session_factory, "Jugador A")
        self._tags_b = PlayerTagsPanel(session_factory, "Jugador B")
        tags_row = QHBoxLayout()
        tags_row.addWidget(self._tags_a)
        tags_row.addWidget(self._tags_b)

        create_button = QPushButton("Crear match")
        create_button.clicked.connect(self._on_create_match_clicked)
        mark_as_primary_action(create_button)
        self._result_label = QLabel("")

        layout = QVBoxLayout()
        layout.addWidget(tournament_box)
        layout.addWidget(players_box)
        layout.addLayout(tags_row)
        layout.addWidget(create_button)
        layout.addWidget(self._result_label)
        layout.addStretch()
        self.setLayout(layout)

        self._reload_tournaments()
        self._reload_players()

    def _reload_tournaments(self) -> None:
        self._tournament_selector.blockSignals(True)
        self._tournament_selector.clear()
        self._tournament_selector.addItem(
            "-- Crear nuevo torneo --", NEW_TOURNAMENT_SENTINEL
        )
        with self._session_factory() as session:
            for tournament in list_tournaments(session):
                label = f"{tournament.name} (baneos x jugador: {tournament.bans_per_player})"
                self._tournament_selector.addItem(label, tournament.id)
        self._tournament_selector.blockSignals(False)
        self._on_tournament_selection_changed()

    def _on_tournament_selection_changed(self) -> None:
        is_new = self._tournament_selector.currentData() == NEW_TOURNAMENT_SENTINEL
        self._new_tournament_name.setEnabled(is_new)
        self._new_tournament_bans.setEnabled(is_new)
        self._new_tournament_timeout_behavior.setEnabled(is_new)
        self._delete_tournament_button.setEnabled(not is_new)

    def _on_delete_tournament_clicked(self) -> None:
        tournament_id = self._tournament_selector.currentData()
        if tournament_id == NEW_TOURNAMENT_SENTINEL or tournament_id is None:
            return
        tournament_name = self._tournament_selector.currentText()
        with self._session_factory() as session:
            match_count = len(session.get(Tournament, tournament_id).matches)
        confirm = QMessageBox.question(
            self,
            "Eliminar torneo",
            f"¿Eliminar '{tournament_name}'? Esto borra también sus "
            f"{match_count} partida(s) (baneos y resultados incluidos). "
            "Esta acción no se puede deshacer.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        with self._session_factory() as session:
            delete_tournament(session, tournament_id)
        self._reload_tournaments()

    def _reload_players(self) -> None:
        with self._session_factory() as session:
            players = list_players(session)
        for selector in (self._player_a_selector, self._player_b_selector):
            previous_id = selector.currentData()
            selector.blockSignals(True)
            selector.clear()
            for player in players:
                selector.addItem(player.display_name, player.id)
            restored_index = selector.findData(previous_id)
            if restored_index >= 0:
                selector.setCurrentIndex(restored_index)
            selector.blockSignals(False)
        self._on_player_a_changed()
        self._on_player_b_changed()

    def _on_player_a_changed(self) -> None:
        self._tags_a.set_player(self._player_a_selector.currentData())

    def _on_player_b_changed(self) -> None:
        self._tags_b.set_player(self._player_b_selector.currentData())

    def _on_create_match_clicked(self) -> None:
        player_a_id = self._player_a_selector.currentData()
        player_b_id = self._player_b_selector.currentData()
        if player_a_id is None or player_b_id is None:
            QMessageBox.warning(
                self,
                "Faltan jugadores",
                "Carga al menos dos jugadores en la pestaña Jugadores primero.",
            )
            return
        if player_a_id == player_b_id:
            QMessageBox.warning(
                self,
                "Jugadores repetidos",
                "Jugador A y Jugador B deben ser distintos.",
            )
            return

        try:
            with self._session_factory() as session:
                if self._tournament_selector.currentData() == NEW_TOURNAMENT_SENTINEL:
                    tournament = create_tournament(
                        session,
                        self._new_tournament_name.text(),
                        self._new_tournament_bans.value(),
                        self._new_tournament_timeout_behavior.currentData(),
                    )
                    tournament_id = tournament.id
                else:
                    tournament_id = self._tournament_selector.currentData()

                match = DraftService(session).create_match(
                    tournament_id, player_a_id, player_b_id
                )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo crear el match", str(exc))
            return

        self._result_label.setText(
            f"Match #{match.id} creado en estado {match.status}."
        )
        self._reload_tournaments()
