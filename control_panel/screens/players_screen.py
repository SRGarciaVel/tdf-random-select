from __future__ import annotations

import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.services.player_profile_service import (
    PlayerProfileUnavailable,
    fetch_player_profile,
)
from backend.app.services.player_service import (
    add_player,
    delete_player,
    list_players,
    update_player,
)
from control_panel.theme import icon, mark_as_primary_action

# Nombre | CFN ID | Rango/MR | Personaje actual - checkpoint UI-2, ver
# ROADMAP.md. Se sacó la columna ID (no le sirve a nadie verla, el
# jugador nunca elige nada por ese numero) y se sumaron las dos ultimas
# leyendo el perfil real de tdf-edeportes.
COLUMN_NAME = 0
COLUMN_CFN_ID = 1
COLUMN_RANK = 2
COLUMN_CHARACTER = 3


class PlayersScreen(QWidget):
    """CRUD de jugadores - base para elegir Jugador A/B en el setup del
    draft (Fase 2, ver ROADMAP.md). Checkpoint UI-2: clic derecho para
    renombrar/copiar/eliminar, y rango/MR/personaje actual traídos en
    vivo de tdf-edeportes (mismo tracker que ya usa el HUD en HUD-10).
    """

    # Se emite desde threads de fondo (fetch_player_profile bloquea por
    # la red) - Qt lo entrega en el thread de la UI, asi consultar el
    # perfil de cada jugador no traba la pantalla mientras carga.
    _profile_fetched = pyqtSignal(object)

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._row_by_player_id: dict[int, int] = {}
        self._profile_fetched.connect(self._on_profile_fetched)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nombre del jugador")
        self._cfn_input = QLineEdit()
        self._cfn_input.setPlaceholderText("CFN ID (opcional)")
        add_button = QPushButton(
            icon("fa5s.user-plus", primary=True), "Agregar jugador"
        )
        add_button.clicked.connect(self._on_add_clicked)
        mark_as_primary_action(add_button)

        form_row = QHBoxLayout()
        form_row.addWidget(self._name_input)
        form_row.addWidget(self._cfn_input)
        form_row.addWidget(add_button)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Nombre", "CFN ID", "Rango / MR", "Personaje actual"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            COLUMN_NAME, QHeaderView.ResizeMode.Stretch
        )
        for column in (COLUMN_CFN_ID, COLUMN_RANK, COLUMN_CHARACTER):
            self._table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu_requested)
        # Tooltip contextual (checkpoint UX-1) - aparece justo al pasar
        # el mouse sobre la fila, ademas del cartel fijo de abajo. El
        # clic derecho no es un patron obvio para alguien que no viene
        # de herramientas tecnicas, asi que conviene la pista en dos
        # lugares: uno fijo (siempre visible) y uno contextual (justo
        # donde se necesita).
        self._table.setToolTip(
            "Clic derecho para renombrar, editar el CFN ID, copiar datos "
            "o eliminar un jugador."
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Jugadores"))
        layout.addLayout(form_row)
        layout.addWidget(self._table)
        layout.addWidget(
            QLabel(
                "Clic derecho sobre un jugador para renombrar, editar el CFN ID, "
                "copiar datos o eliminarlo."
            ),
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        with self._session_factory() as session:
            players = list_players(session)

        self._row_by_player_id = {}
        self._table.setRowCount(len(players))
        for row, player in enumerate(players):
            self._row_by_player_id[player.id] = row
            self._set_row_item(row, COLUMN_NAME, player.display_name, player.id)
            self._set_row_item(row, COLUMN_CFN_ID, player.cfn_id or "")
            self._set_row_item(row, COLUMN_RANK, "…" if player.cfn_id else "")
            self._set_row_item(row, COLUMN_CHARACTER, "…" if player.cfn_id else "")
            if player.cfn_id:
                self._fetch_profile_in_background(player.id, player.cfn_id)

    def _set_row_item(
        self, row: int, column: int, text: str, player_id: int | None = None
    ) -> None:
        item = QTableWidgetItem(text)
        if player_id is not None:
            # el id del jugador viaja escondido en el item de la columna
            # Nombre (Qt.ItemDataRole.UserRole) - ya no hay una columna
            # ID visible, pero las acciones (renombrar, eliminar, etc.)
            # todavia necesitan saber a que jugador corresponde la fila.
            item.setData(Qt.ItemDataRole.UserRole, player_id)
        self._table.setItem(row, column, item)

    def _fetch_profile_in_background(self, player_id: int, cfn_id: str) -> None:
        def worker() -> None:
            try:
                profile = fetch_player_profile(cfn_id)
                self._profile_fetched.emit(
                    {"player_id": player_id, "ok": True, "profile": profile}
                )
            except PlayerProfileUnavailable as exc:
                self._profile_fetched.emit(
                    {"player_id": player_id, "ok": False, "error": str(exc)}
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_profile_fetched(self, result: dict) -> None:
        row = self._row_by_player_id.get(result["player_id"])
        if row is None or row >= self._table.rowCount():
            return  # la tabla se refrescó de nuevo mientras esto viajaba

        if not result["ok"]:
            self._set_row_item(row, COLUMN_RANK, "Sin datos")
            self._set_row_item(row, COLUMN_CHARACTER, "")
            return

        profile = result["profile"]
        rank = profile.get("league_rank")
        mr = profile.get("master_rating")
        if mr:
            rank_text = f"{rank or 'Master'} · {mr} MR"
        elif rank:
            rank_text = rank
        else:
            rank_text = "Sin datos"
        self._set_row_item(row, COLUMN_RANK, rank_text)
        self._set_row_item(row, COLUMN_CHARACTER, profile.get("character_name") or "")

    def _on_add_clicked(self) -> None:
        name = self._name_input.text()
        cfn_id = self._cfn_input.text()
        try:
            with self._session_factory() as session:
                add_player(session, name, cfn_id)
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo agregar", str(exc))
            return

        self._name_input.clear()
        self._cfn_input.clear()
        self.refresh()

    def _player_id_at_row(self, row: int) -> int | None:
        item = self._table.item(row, COLUMN_NAME)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_context_menu_requested(self, position) -> None:
        row = self._table.rowAt(position.y())
        if row < 0:
            return
        player_id = self._player_id_at_row(row)
        if player_id is None:
            return

        current_name = self._table.item(row, COLUMN_NAME).text()
        current_cfn_id = self._table.item(row, COLUMN_CFN_ID).text()

        menu = QMenu(self)
        rename_action = menu.addAction("Renombrar...")
        edit_cfn_action = menu.addAction("Editar CFN ID...")
        menu.addSeparator()
        copy_name_action = menu.addAction("Copiar nombre")
        copy_cfn_action = menu.addAction("Copiar CFN ID")
        menu.addSeparator()
        delete_action = menu.addAction("Eliminar jugador")

        chosen = menu.exec(self._table.viewport().mapToGlobal(position))
        if chosen is None:
            return

        if chosen == rename_action:
            self._rename_player(player_id, current_name)
        elif chosen == edit_cfn_action:
            self._edit_cfn_id(player_id, current_cfn_id)
        elif chosen == copy_name_action:
            QApplication.clipboard().setText(current_name)
        elif chosen == copy_cfn_action:
            QApplication.clipboard().setText(current_cfn_id)
        elif chosen == delete_action:
            self._delete_player(player_id, current_name)

    def _rename_player(self, player_id: int, current_name: str) -> None:
        new_name, ok = QInputDialog.getText(
            self, "Renombrar jugador", "Nuevo nombre:", text=current_name
        )
        if not ok:
            return
        try:
            with self._session_factory() as session:
                update_player(session, player_id, display_name=new_name)
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo renombrar", str(exc))
            return
        self.refresh()

    def _edit_cfn_id(self, player_id: int, current_cfn_id: str) -> None:
        new_cfn_id, ok = QInputDialog.getText(
            self, "Editar CFN ID", "CFN ID (vacío para quitarlo):", text=current_cfn_id
        )
        if not ok:
            return
        with self._session_factory() as session:
            update_player(session, player_id, cfn_id=new_cfn_id)
        self.refresh()

    def _delete_player(self, player_id: int, current_name: str) -> None:
        confirm = QMessageBox.question(
            self,
            "Eliminar jugador",
            f"¿Eliminar a {current_name}? Esta acción no se puede deshacer.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        with self._session_factory() as session:
            delete_player(session, player_id)
        self.refresh()
