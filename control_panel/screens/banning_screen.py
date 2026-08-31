from __future__ import annotations

import datetime as dt

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.data.sf6_roster import SF6_ROSTER
from backend.app.models import Match
from backend.app.services.character_tag_service import list_character_tags
from backend.app.services.draft_service import (
    DraftError,
    DraftService,
    build_match_state_payload,
    list_open_matches,
)
from backend.app.services.player_service import get_player
from control_panel.overlay_bridge import OverlayBridge

CHARACTER_DISPLAY_NAMES = {entry["id"]: entry["display_name"] for entry in SF6_ROSTER}
GRID_COLUMNS = 6
BAN_TIMER_MS = 30_000  # 30s por baneo (HUD) - parametro para poder acortarlo en tests


class BanningScreen(QWidget):
    """Baneo en vivo del match elegido: SETUP -> BANNING -> RANDOMIZING ->
    REVEAL -> DONE (Fase 2 checkpoint 3, ver ROADMAP.md).

    Empuja el estado al overlay via Socket.IO despues de cada accion
    (Fase 3 checkpoint A) - todavia no dispara obs_service, eso llega en
    la Fase 4 junto con la pantalla real de configuracion de OBS.
    """

    def __init__(
        self, session_factory: sessionmaker, timer_ms: int = BAN_TIMER_MS
    ) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._match_id: int | None = None
        self._character_buttons: dict[str, QPushButton] = {}
        self._overlay_bridge = OverlayBridge()

        self._timer_ms = timer_ms
        self._ban_timer = QTimer(self)
        self._ban_timer.setSingleShot(True)
        self._ban_timer.timeout.connect(self._on_ban_timeout)
        self._current_turn_key: tuple[int, int] | None = None  # (match_id, player_id)
        self._turn_deadline: dt.datetime | None = None

        self._match_selector = QComboBox()
        self._match_selector.currentIndexChanged.connect(self._on_match_selected)
        refresh_button = QPushButton("Refrescar partidas")
        refresh_button.clicked.connect(self._reload_matches)
        match_row = QHBoxLayout()
        match_row.addWidget(self._match_selector)
        match_row.addWidget(refresh_button)

        self._first_banner_selector = QComboBox()
        self._start_button = QPushButton("Iniciar baneo")
        self._start_button.clicked.connect(self._on_start_banning_clicked)
        start_row = QHBoxLayout()
        start_row.addWidget(QLabel("Banea primero:"))
        start_row.addWidget(self._first_banner_selector)
        start_row.addWidget(self._start_button)

        self._status_label = QLabel("Elige una partida.")

        grid_box = QGroupBox("Personajes (★ = personaje fuerte del rival)")
        grid = QGridLayout()
        for index, entry in enumerate(SF6_ROSTER):
            button = QPushButton(entry["display_name"])
            button.clicked.connect(
                lambda _checked, cid=entry["id"]: self._on_character_clicked(cid)
            )
            self._character_buttons[entry["id"]] = button
            grid.addWidget(button, index // GRID_COLUMNS, index % GRID_COLUMNS)
        grid_box.setLayout(grid)

        self._randomize_button = QPushButton("Randomizar")
        self._randomize_button.clicked.connect(self._on_randomize_clicked)
        self._results_label = QLabel("")
        self._complete_button = QPushButton("Completar reveal")
        self._complete_button.clicked.connect(self._on_complete_clicked)

        layout = QVBoxLayout()
        layout.addLayout(match_row)
        layout.addLayout(start_row)
        layout.addWidget(self._status_label)
        layout.addWidget(grid_box)
        layout.addWidget(self._randomize_button)
        layout.addWidget(self._results_label)
        layout.addWidget(self._complete_button)
        self.setLayout(layout)

        self._reload_matches()

    def _reload_matches(self) -> None:
        with self._session_factory() as session:
            entries = []
            for match in list_open_matches(session):
                player_a = get_player(session, match.player_a_id)
                player_b = get_player(session, match.player_b_id)
                label = f"#{match.id}: {player_a.display_name} vs {player_b.display_name} ({match.status})"
                entries.append((label, match.id))

        previous_id = self._match_selector.currentData()
        self._match_selector.blockSignals(True)
        self._match_selector.clear()
        for label, match_id in entries:
            self._match_selector.addItem(label, match_id)
        restored_index = self._match_selector.findData(previous_id)
        if restored_index >= 0:
            self._match_selector.setCurrentIndex(restored_index)
        self._match_selector.blockSignals(False)
        self._on_match_selected()

    def _on_match_selected(self) -> None:
        self._match_id = self._match_selector.currentData()
        self._refresh_state()

    def _refresh_state(self) -> None:
        if self._match_id is None:
            self._stop_ban_timer()
            self._overlay_bridge.emit_match_state({"match_id": None})
            self._status_label.setText("Elige una partida.")
            for button in self._character_buttons.values():
                button.setEnabled(False)
                button.setStyleSheet("")
            self._randomize_button.setEnabled(False)
            self._complete_button.setEnabled(False)
            self._start_button.setEnabled(False)
            self._first_banner_selector.clear()
            self._results_label.setText("")
            return

        with self._session_factory() as session:
            match = session.get(Match, self._match_id)
            if match is None:
                return
            player_a = get_player(session, match.player_a_id)
            player_b = get_player(session, match.player_b_id)
            tags_a = {
                tag.character_id
                for tag in list_character_tags(session, match.player_a_id)
            }
            tags_b = {
                tag.character_id
                for tag in list_character_tags(session, match.player_b_id)
            }
            banned_ids = {ban.character_id for ban in match.bans}
            status = match.status
            results = {
                result.player_id: result.assigned_character_id
                for result in match.results
            }

            current_turn_id = None
            if status == "BANNING":
                current_turn_id = DraftService(session).current_turn_player_id(match)

            state_payload = build_match_state_payload(session, self._match_id)

        self._sync_ban_timer(status, current_turn_id)
        if self._turn_deadline is not None:
            state_payload["turn_deadline_ms"] = int(
                self._turn_deadline.timestamp() * 1000
            )
        self._overlay_bridge.emit_match_state(state_payload)

        self._first_banner_selector.blockSignals(True)
        self._first_banner_selector.clear()
        self._first_banner_selector.addItem(player_a.display_name, player_a.id)
        self._first_banner_selector.addItem(player_b.display_name, player_b.id)
        self._first_banner_selector.blockSignals(False)
        self._start_button.setEnabled(status == "SETUP")
        self._first_banner_selector.setEnabled(status == "SETUP")

        opponent_tags: set[str] = set()
        if current_turn_id is not None:
            opponent_tags = tags_b if current_turn_id == player_a.id else tags_a

        for character_id, button in self._character_buttons.items():
            display_name = CHARACTER_DISPLAY_NAMES[character_id]
            is_banned = character_id in banned_ids
            label = (
                f"★ {display_name}" if character_id in opponent_tags else display_name
            )
            button.setText(label)
            button.setEnabled(status == "BANNING" and not is_banned)
            button.setStyleSheet(
                "color: gray; text-decoration: line-through;" if is_banned else ""
            )

        status_messages = {
            "SETUP": f"Match #{match.id}: {player_a.display_name} vs {player_b.display_name}. Listo para iniciar el baneo.",
            "RANDOMIZING": "Baneo completo. Lista para randomizar.",
            "REVEAL": "Reveal listo.",
            "DONE": "Match completo.",
        }
        if status == "BANNING":
            turn_name = (
                player_a.display_name
                if current_turn_id == player_a.id
                else player_b.display_name
            )
            self._status_label.setText(
                f"Turno de banear: {turn_name} ({len(banned_ids)} baneados)"
            )
        else:
            self._status_label.setText(status_messages.get(status, status))

        self._randomize_button.setEnabled(status == "RANDOMIZING")
        self._complete_button.setEnabled(status == "REVEAL")

        if results:
            lines = []
            for player_id, character_id in results.items():
                player_name = (
                    player_a.display_name
                    if player_id == player_a.id
                    else player_b.display_name
                )
                lines.append(f"{player_name}: {CHARACTER_DISPLAY_NAMES[character_id]}")
            self._results_label.setText("\n".join(lines))
        else:
            self._results_label.setText("")

    def _on_start_banning_clicked(self) -> None:
        first_banner_id = self._first_banner_selector.currentData()
        try:
            with self._session_factory() as session:
                DraftService(session).start_banning(self._match_id, first_banner_id)
        except DraftError as exc:
            QMessageBox.warning(self, "No se pudo iniciar el baneo", str(exc))
            return
        self._reload_matches()

    def _on_character_clicked(self, character_id: str) -> None:
        if self._match_id is None:
            return
        try:
            with self._session_factory() as session:
                match = session.get(Match, self._match_id)
                service = DraftService(session)
                current_turn_id = service.current_turn_player_id(match)
                service.ban_character(self._match_id, character_id, current_turn_id)
        except DraftError as exc:
            QMessageBox.warning(self, "Baneo inválido", str(exc))
            return
        self._reload_matches()

    def _on_randomize_clicked(self) -> None:
        try:
            with self._session_factory() as session:
                DraftService(session).roll_random(self._match_id)
        except DraftError as exc:
            QMessageBox.warning(self, "No se pudo randomizar", str(exc))
            return
        self._reload_matches()

    def _on_complete_clicked(self) -> None:
        completed_match_id = self._match_id
        try:
            with self._session_factory() as session:
                DraftService(session).complete_reveal(completed_match_id)
                final_payload = build_match_state_payload(session, completed_match_id)
        except DraftError as exc:
            QMessageBox.warning(self, "No se pudo completar", str(exc))
            return

        # Se emite antes de _reload_matches(): al pasar a DONE, el match
        # sale de list_open_matches() y el selector queda sin nada
        # seleccionado - sin este emit explicito, el overlay nunca ve el
        # estado final, solo ve el match desaparecer (ver tasks/lessons.md).
        self._overlay_bridge.emit_match_state(final_payload)
        self._reload_matches()

    def _sync_ban_timer(self, status: str, current_turn_id: int | None) -> None:
        """Arranca el timer de 30s solo cuando el turno realmente cambio -
        evita reiniciarlo en cada _refresh_state() sin motivo (ej. click
        en "Refrescar partidas" sin haber baneado nada nuevo)."""
        if status != "BANNING" or current_turn_id is None:
            self._stop_ban_timer()
            return

        turn_key = (self._match_id, current_turn_id)
        if turn_key == self._current_turn_key:
            return  # mismo turno de antes, no reiniciar la cuenta regresiva

        self._current_turn_key = turn_key
        self._turn_deadline = dt.datetime.now(dt.UTC) + dt.timedelta(
            milliseconds=self._timer_ms
        )
        self._ban_timer.start(self._timer_ms)

    def _stop_ban_timer(self) -> None:
        self._ban_timer.stop()
        self._current_turn_key = None
        self._turn_deadline = None

    def _on_ban_timeout(self) -> None:
        """Se agotaron los 30s sin baneo manual - banea al azar en nombre
        del jugador que tenia el turno (HUD de baneo)."""
        if self._match_id is None:
            return
        try:
            with self._session_factory() as session:
                DraftService(session).resolve_ban_timeout(self._match_id)
        except DraftError:
            # el estado pudo haber cambiado entre que arranco el timer y
            # que disparo (ej. el staff ya baneo a mano justo antes) - no
            # es un error real, solo se ignora y se refresca el estado.
            pass
        self._reload_matches()
