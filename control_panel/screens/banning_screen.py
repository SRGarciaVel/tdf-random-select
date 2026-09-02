from __future__ import annotations

import datetime as dt
import threading
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.data.sf6_roster import SF6_ROSTER
from backend.app.models import Match
from backend.app.services.character_stats_service import (
    CharacterStatsUnavailable,
    fetch_character_stats,
)
from backend.app.services.character_tag_service import list_character_tags
from backend.app.services.draft_service import (
    DraftError,
    DraftService,
    build_match_state_payload,
    delete_all_matches,
    delete_match,
    list_all_matches,
    list_open_matches,
)
from backend.app.services.obs_service import ObsConnectionError, ObsService
from backend.app.services.obs_settings_service import get_obs_settings
from backend.app.services.player_profile_service import (
    PlayerProfileUnavailable,
    fetch_player_profile,
)
from backend.app.services.player_service import get_player
from control_panel.overlay_bridge import OverlayBridge
from control_panel.theme import mark_as_primary_action

CHARACTER_DISPLAY_NAMES = {entry["id"]: entry["display_name"] for entry in SF6_ROSTER}
GRID_COLUMNS = 6
BAN_TIMER_MS = 30_000  # 30s por baneo (HUD) - parametro para poder acortarlo en tests

# Mismos retratos chicos que ya usa el overlay (checkpoint UI-4, ver
# ROADMAP.md) - QPixmap carga .webp sin problema (confirmado con un
# test real antes de construir esto), no hace falta un tercer set de
# imagenes para la grilla del panel.
PORTRAITS_DIR = (
    Path(__file__).resolve().parents[2] / "overlay_app" / "public" / "portraits"
)
CHARACTER_ICON_SIZE = QSize(56, 56)


def _portrait_path(character_id: str) -> str:
    return str(PORTRAITS_DIR / f"{character_id}.webp")


class CharacterButton(QToolButton):
    """Carita del personaje + nombre abajo, al estilo de la seleccion de
    campeon de League of Legends (checkpoint UI-4, a pedido de Seba) -
    reemplaza los QPushButton de solo texto que tenia la grilla antes.
    """

    def __init__(self, character_id: str, display_name: str) -> None:
        super().__init__()
        self.character_id = character_id
        self._display_name = display_name
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(CHARACTER_ICON_SIZE)
        self.setFixedSize(80, 92)
        pixmap = QPixmap(_portrait_path(character_id))
        if not pixmap.isNull():
            self.setIcon(QIcon(pixmap))
        self.set_marker(is_strong=False, is_banned=False)

    def set_marker(self, is_strong: bool, is_banned: bool) -> None:
        """★ = personaje fuerte del rival, ✕ = ya baneado - prefijos de
        texto en vez de tachado real: los QToolButton de Qt no soportan
        text-decoration de forma confiable via QSS, un glifo se
        renderiza siempre igual sin importar el estilo."""
        prefix = "✕ " if is_banned else ("★ " if is_strong else "")
        self.setText(f"{prefix}{self._display_name}")

    def set_selected(self, selected: bool) -> None:
        self.setProperty("state", "selected" if selected else "")
        self.style().unpolish(self)
        self.style().polish(self)


class BanningScreen(QWidget):
    """Baneo en vivo del match elegido: SETUP -> BANNING -> RANDOMIZING ->
    REVEAL -> DONE (Fase 2 checkpoint 3, ver ROADMAP.md).

    Empuja el estado al overlay via Socket.IO despues de cada accion
    (Fase 3 checkpoint A) - todavia no dispara obs_service, eso llega en
    la Fase 4 junto con la pantalla real de configuracion de OBS.
    """

    # Se emite desde un thread de fondo (fetch_character_stats bloquea
    # hasta 6s por la red) - Qt lo entrega en el thread de la UI solo,
    # asi la consulta a tdf-edeportes nunca traba el panel (checkpoint
    # HUD-10, ver ROADMAP.md).
    _character_stats_fetched = pyqtSignal(object)
    # Mismo patron para el panel de CFN de ambos jugadores (rango/MR/
    # personaje actual) - checkpoint UI-4, ver ROADMAP.md.
    _cfn_profile_fetched = pyqtSignal(object)

    def __init__(
        self, session_factory: sessionmaker, timer_ms: int = BAN_TIMER_MS
    ) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._match_id: int | None = None
        self._character_buttons: dict[str, CharacterButton] = {}
        self._overlay_bridge = OverlayBridge()

        self._timer_ms = timer_ms
        self._ban_timer = QTimer(self)
        self._ban_timer.setSingleShot(True)
        self._ban_timer.timeout.connect(self._on_ban_timeout)
        self._current_turn_key: tuple[int, int] | None = None  # (match_id, player_id)
        self._turn_deadline: dt.datetime | None = None
        # Personaje elegido pero todavia sin confirmar (checkpoint HUD-4:
        # clic selecciona, "Bloquear" confirma - evita baneos accidentales
        # y le da tiempo al overlay a mostrar el preview grande).
        self._selected_character_id: str | None = None
        # Estadisticas de CFN sobre el ultimo baneo confirmado
        # (checkpoint HUD-10) - toggle manual, nunca automatico.
        self._stats_visible = False
        self._character_stats_fetched.connect(self._on_character_stats_fetched)
        self._cfn_profile_fetched.connect(self._on_cfn_profile_fetched)
        # Se crea al arrancar el baneo, se reusa para volver a la escena
        # original al completar el reveal (Fase 4, ver ROADMAP.md) - la
        # instancia guarda la escena previa internamente.
        self._obs: ObsService | None = None

        self._match_selector = QComboBox()
        self._match_selector.currentIndexChanged.connect(self._on_match_selected)
        refresh_button = QPushButton("Refrescar partidas")
        refresh_button.clicked.connect(self._reload_matches)
        self._delete_match_button = QPushButton("Eliminar esta partida")
        self._delete_match_button.clicked.connect(self._on_delete_match_clicked)
        clear_all_button = QPushButton("Limpiar TODAS las partidas")
        clear_all_button.clicked.connect(self._on_clear_all_matches_clicked)
        match_row = QHBoxLayout()
        match_row.addWidget(self._match_selector)
        match_row.addWidget(refresh_button)
        match_row.addWidget(self._delete_match_button)
        match_row.addWidget(clear_all_button)

        self._first_banner_selector = QComboBox()
        self._start_button = QPushButton("Iniciar baneo")
        self._start_button.clicked.connect(self._on_start_banning_clicked)
        mark_as_primary_action(self._start_button)
        start_row = QHBoxLayout()
        start_row.addWidget(QLabel("Banea primero:"))
        start_row.addWidget(self._first_banner_selector)
        start_row.addWidget(self._start_button)

        self._status_label = QLabel("Elige una partida.")

        # Panel de CFN de ambos jugadores (rango/MR/personaje actual) -
        # checkpoint UI-4, mismo tracker que ya usa Jugadores (UI-2) y
        # HUD-10. Se decidio dejar afuera el "top de campeones" (Seba:
        # el picante del baneo se decide charlando con el rival en vivo,
        # no hace falta que la app lo sugiera).
        self._cfn_label_a = QLabel("")
        self._cfn_label_b = QLabel("")
        for label in (self._cfn_label_a, self._cfn_label_b):
            label.setProperty("secondary", "true")
            label.setWordWrap(True)
        cfn_box_a = QGroupBox("CFN — Jugador A")
        cfn_layout_a = QVBoxLayout()
        cfn_layout_a.addWidget(self._cfn_label_a)
        cfn_box_a.setLayout(cfn_layout_a)
        cfn_box_b = QGroupBox("CFN — Jugador B")
        cfn_layout_b = QVBoxLayout()
        cfn_layout_b.addWidget(self._cfn_label_b)
        cfn_box_b.setLayout(cfn_layout_b)
        cfn_row = QHBoxLayout()
        cfn_row.addWidget(cfn_box_a)
        cfn_row.addWidget(cfn_box_b)

        self._character_search = QLineEdit()
        self._character_search.setPlaceholderText("Buscar personaje...")
        self._character_search.textChanged.connect(self._on_character_search_changed)

        grid_box = QGroupBox("Personajes (★ = fuerte del rival, ✕ = ya baneado)")
        grid = QGridLayout()
        for index, entry in enumerate(SF6_ROSTER):
            button = CharacterButton(entry["id"], entry["display_name"])
            button.clicked.connect(
                lambda _checked, cid=entry["id"]: self._on_character_selected(cid)
            )
            self._character_buttons[entry["id"]] = button
            grid.addWidget(button, index // GRID_COLUMNS, index % GRID_COLUMNS)
        grid_box_layout = QVBoxLayout()
        grid_box_layout.addWidget(self._character_search)
        grid_box_layout.addLayout(grid)
        grid_box.setLayout(grid_box_layout)

        self._lock_in_button = QPushButton("Bloquear")
        self._lock_in_button.setEnabled(False)
        self._lock_in_button.clicked.connect(self._on_lock_in_clicked)
        mark_as_primary_action(self._lock_in_button)

        self._randomize_button = QPushButton("Randomizar")
        self._randomize_button.clicked.connect(self._on_randomize_clicked)
        self._results_label = QLabel("")
        self._complete_button = QPushButton("Completar reveal")
        self._complete_button.clicked.connect(self._on_complete_clicked)
        mark_as_primary_action(self._complete_button)

        # Estadisticas de CFN del ultimo baneo confirmado (checkpoint
        # HUD-10) - deshabilitado hasta que haya al menos un baneo real.
        self._show_stats_button = QPushButton("Mostrar estadísticas")
        self._show_stats_button.setEnabled(False)
        self._show_stats_button.clicked.connect(self._on_toggle_stats_clicked)
        self._stats_label = QLabel("")

        layout = QVBoxLayout()
        layout.addLayout(match_row)
        layout.addLayout(start_row)
        layout.addWidget(self._status_label)
        layout.addLayout(cfn_row)
        layout.addWidget(grid_box)
        layout.addWidget(self._lock_in_button)
        layout.addWidget(self._randomize_button)
        layout.addWidget(self._results_label)
        layout.addWidget(self._complete_button)
        layout.addWidget(self._show_stats_button)
        layout.addWidget(self._stats_label)
        self._obs_status_label = QLabel("")
        layout.addWidget(self._obs_status_label)
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
        self._refresh_cfn_panels()

    def _refresh_state(self) -> None:
        if self._match_id is None:
            self._stop_ban_timer()
            self._overlay_bridge.emit_match_state({"match_id": None})
            self._status_label.setText("Elige una partida.")
            for button in self._character_buttons.values():
                button.setEnabled(False)
                button.set_marker(is_strong=False, is_banned=False)
                button.set_selected(False)
            self._randomize_button.setEnabled(False)
            self._complete_button.setEnabled(False)
            self._start_button.setEnabled(False)
            self._lock_in_button.setEnabled(False)
            self._delete_match_button.setEnabled(False)
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
        self._delete_match_button.setEnabled(True)

        opponent_tags: set[str] = set()
        if current_turn_id is not None:
            opponent_tags = tags_b if current_turn_id == player_a.id else tags_a

        for character_id, button in self._character_buttons.items():
            is_banned = character_id in banned_ids
            is_strong = character_id in opponent_tags
            button.set_marker(is_strong=is_strong, is_banned=is_banned)
            button.setEnabled(status == "BANNING" and not is_banned)
            button.set_selected(character_id == self._selected_character_id)

        self._lock_in_button.setEnabled(
            status == "BANNING" and self._selected_character_id is not None
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
        # al menos un baneo real confirmado (no solo turnos saltados) -
        # checkpoint HUD-10.
        has_real_ban = any(cid is not None for cid in banned_ids)
        self._show_stats_button.setEnabled(has_real_ban)

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
        self._switch_to_draft_scene()
        self._reload_matches()

    def _switch_to_draft_scene(self) -> None:
        """Guarda la escena activa de OBS y cambia a la escena de baneo
        configurada en la pestaña "OBS" (Fase 4, ver ROADMAP.md). Si OBS
        no está prendido o no hay escena configurada, no bloquea nada -
        el draft sigue funcionando igual (modo degradado, ver
        CODESTYLE.md)."""
        with self._session_factory() as session:
            obs_settings = get_obs_settings(session)
        if not obs_settings.draft_scene_name:
            return
        self._obs = ObsService(
            host=obs_settings.host,
            port=obs_settings.port,
            password=obs_settings.password or "",
        )
        try:
            self._obs.connect()
            self._obs.switch_to_draft_scene(obs_settings.draft_scene_name)
            self._obs_status_label.setText(
                f"OBS: cambiado a '{obs_settings.draft_scene_name}'."
            )
        except ObsConnectionError as exc:
            self._obs_status_label.setText(
                f"OBS no disponible (el draft sigue igual): {exc}"
            )

    def _restore_obs_scene(self) -> None:
        """Vuelve a la escena que estaba activa antes de _switch_to_draft_scene
        - mismo modo degradado, un fallo acá no debe impedir terminar el
        reveal."""
        if self._obs is None:
            return
        try:
            self._obs.restore_previous_scene()
            self._obs_status_label.setText("OBS: escena original restaurada.")
        except ObsConnectionError as exc:
            self._obs_status_label.setText(
                f"No se pudo restaurar la escena de OBS: {exc}"
            )
        finally:
            self._obs = None

    def _on_character_search_changed(self, text: str) -> None:
        query = text.strip().lower()
        for character_id, button in self._character_buttons.items():
            display_name = CHARACTER_DISPLAY_NAMES[character_id].lower()
            button.setVisible(query in display_name)

    def _on_character_selected(self, character_id: str) -> None:
        if self._match_id is None or self._current_turn_key is None:
            return
        # No llama a _refresh_state() a proposito: eso re-emite
        # match_state_update, y en el overlay CUALQUIER match_state_update
        # borra el preview del candidato (para limpiar restos viejos
        # despues de una accion real). Seleccionar no es una accion real
        # todavia - si reemitieramos el estado ahi, el preview que
        # acabamos de mandar se borraria solo medio segundo despues (bug
        # real encontrado por Seba, ver tasks/lessons.md).
        previous_selection = self._selected_character_id
        self._selected_character_id = character_id
        if (
            previous_selection is not None
            and previous_selection in self._character_buttons
        ):
            self._character_buttons[previous_selection].set_selected(False)
        self._character_buttons[character_id].set_selected(True)
        self._lock_in_button.setEnabled(True)

        _, current_turn_player_id = self._current_turn_key
        self._overlay_bridge.emit_ban_candidate_preview(
            character_id, current_turn_player_id
        )

    def _on_lock_in_clicked(self) -> None:
        if self._match_id is None or self._selected_character_id is None:
            return
        character_id = self._selected_character_id
        try:
            with self._session_factory() as session:
                match = session.get(Match, self._match_id)
                service = DraftService(session)
                current_turn_id = service.current_turn_player_id(match)
                service.ban_character(self._match_id, character_id, current_turn_id)
        except DraftError as exc:
            QMessageBox.warning(self, "Baneo inválido", str(exc))
            return
        self._selected_character_id = None
        # el "ultimo baneo confirmado" cambio - cualquier estadistica
        # mostrada quedo obsoleta (checkpoint HUD-10).
        self._reset_stats_display()
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
        self._restore_obs_scene()
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
        self._clear_selection()

    def _clear_selection(self) -> None:
        if self._selected_character_id is not None:
            self._selected_character_id = None
            self._overlay_bridge.emit_ban_candidate_preview(None, None)

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
        self._reset_stats_display()
        self._reload_matches()

    def _reset_stats_display(self) -> None:
        """Vuelve el toggle a su estado apagado y borra las estadisticas
        del overlay - se llama cada vez que "el ultimo baneo confirmado"
        cambia, para no dejar datos obsoletos mostrados por accidente
        (checkpoint HUD-10)."""
        if self._stats_visible:
            self._overlay_bridge.emit_character_stats({"visible": False})
        self._stats_visible = False
        self._show_stats_button.setText("Mostrar estadísticas")
        self._stats_label.setText("")

    def _on_toggle_stats_clicked(self) -> None:
        if self._stats_visible:
            self._reset_stats_display()
            return

        if self._match_id is None:
            return
        with self._session_factory() as session:
            match = session.get(Match, self._match_id)
            if match is None or not match.bans:
                return
            last_ban = max(match.bans, key=lambda ban: ban.turn_order)
            if last_ban.character_id is None:
                self._stats_label.setText(
                    "El último turno se saltó - no hay personaje que consultar."
                )
                return
            player = get_player(session, last_ban.banned_by_player_id)
            character_id = last_ban.character_id
            player_id = last_ban.banned_by_player_id
            player_display_name = player.display_name if player else "?"
            cfn_id = player.cfn_id if player else None

        if not cfn_id:
            self._stats_label.setText(
                f"{player_display_name} no tiene CFN ID cargado en Jugadores."
            )
            return

        character_display_name = CHARACTER_DISPLAY_NAMES.get(character_id, character_id)
        self._stats_label.setText("Consultando tdf-edeportes...")
        self._show_stats_button.setEnabled(False)

        def worker() -> None:
            try:
                data = fetch_character_stats(cfn_id, character_display_name)
                self._character_stats_fetched.emit(
                    {
                        "ok": True,
                        "data": data,
                        "player_id": player_id,
                        "player_display_name": player_display_name,
                        "character_id": character_id,
                    }
                )
            except CharacterStatsUnavailable as exc:
                self._character_stats_fetched.emit(
                    {
                        "ok": False,
                        "error": str(exc),
                        "player_display_name": player_display_name,
                    }
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_character_stats_fetched(self, result: dict) -> None:
        self._show_stats_button.setEnabled(True)
        if not result["ok"]:
            self._stats_label.setText(
                f"No se pudo consultar tdf-edeportes: {result['error']}"
            )
            return

        data = result["data"]
        player_name = result["player_display_name"]
        if not data.get("ever_played"):
            self._stats_label.setText(f"{player_name}: nunca jugó este personaje.")
        else:
            win_rate_pct = (data.get("win_rate") or 0) * 100
            matches_played = data.get("matches_played")
            self._stats_label.setText(
                f"{player_name}: {win_rate_pct:.1f}% de victorias "
                f"({matches_played} partidas totales) - visible en el HUD."
            )

        self._stats_visible = True
        self._show_stats_button.setText("Ocultar estadísticas")
        self._overlay_bridge.emit_character_stats(
            {
                "visible": True,
                "player_id": result["player_id"],
                "character_id": result["character_id"],
                "ever_played": data.get("ever_played", False),
                "matches_played": data.get("matches_played"),
                "win_rate": data.get("win_rate"),
            }
        )

    def _refresh_cfn_panels(self) -> None:
        """Rango/MR/personaje actual de ambos jugadores del match elegido
        (checkpoint UI-4) - se consulta en threads de fondo, igual
        criterio que Jugadores (UI-2) y las estadisticas de HUD-10:
        nunca debe trabar el panel mientras carga."""
        if self._match_id is None:
            self._cfn_label_a.setText("")
            self._cfn_label_b.setText("")
            return

        with self._session_factory() as session:
            match = session.get(Match, self._match_id)
            if match is None:
                return
            player_a = get_player(session, match.player_a_id)
            player_b = get_player(session, match.player_b_id)

        self._fetch_cfn_profile_in_background("a", player_a)
        self._fetch_cfn_profile_in_background("b", player_b)

    def _fetch_cfn_profile_in_background(self, side: str, player) -> None:
        label = self._cfn_label_a if side == "a" else self._cfn_label_b
        if player is None:
            label.setText("")
            return
        if not player.cfn_id:
            label.setText(f"{player.display_name}\nSin CFN ID cargado.")
            return

        label.setText(f"{player.display_name}\nConsultando...")
        player_display_name = player.display_name
        cfn_id = player.cfn_id

        def worker() -> None:
            try:
                profile = fetch_player_profile(cfn_id)
                self._cfn_profile_fetched.emit(
                    {
                        "side": side,
                        "ok": True,
                        "profile": profile,
                        "player_name": player_display_name,
                    }
                )
            except PlayerProfileUnavailable as exc:
                self._cfn_profile_fetched.emit(
                    {
                        "side": side,
                        "ok": False,
                        "error": str(exc),
                        "player_name": player_display_name,
                    }
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_cfn_profile_fetched(self, result: dict) -> None:
        label = self._cfn_label_a if result["side"] == "a" else self._cfn_label_b
        player_name = result["player_name"]
        if not result["ok"]:
            label.setText(f"{player_name}\nSin datos de tdf-edeportes.")
            return

        profile = result["profile"]
        rank = profile.get("league_rank")
        mr = profile.get("master_rating")
        character = profile.get("character_name")

        lines = [player_name]
        if mr:
            lines.append(f"{rank or 'Master'} · {mr} MR")
        elif rank:
            lines.append(rank)
        else:
            lines.append("Sin rango disponible")
        if character:
            lines.append(f"Personaje actual: {character}")
        label.setText("\n".join(lines))

    def _on_delete_match_clicked(self) -> None:
        if self._match_id is None:
            return
        match_label = self._match_selector.currentText()
        confirm = QMessageBox.question(
            self,
            "Eliminar partida",
            f"¿Eliminar '{match_label}'? Esta acción no se puede deshacer.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        with self._session_factory() as session:
            delete_match(session, self._match_id)
        self._reload_matches()

    def _on_clear_all_matches_clicked(self) -> None:
        with self._session_factory() as session:
            total = len(list_all_matches(session))
        if total == 0:
            QMessageBox.information(
                self, "Nada que limpiar", "No hay partidas guardadas todavía."
            )
            return
        confirm = QMessageBox.question(
            self,
            "Limpiar TODAS las partidas",
            f"¿Eliminar las {total} partida(s) guardadas (de cualquier estado)? "
            "Esta acción no se puede deshacer.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        with self._session_factory() as session:
            deleted = delete_all_matches(session)
        QMessageBox.information(self, "Listo", f"Se eliminaron {deleted} partida(s).")
        self._reload_matches()
