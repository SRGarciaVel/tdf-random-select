from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import sessionmaker

from backend.app.services.player_service import add_player, delete_player, list_players


class PlayersScreen(QWidget):
    """CRUD simple de jugadores - base para elegir Jugador A/B en el setup
    del draft (Fase 2, ver ROADMAP.md)."""

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self._session_factory = session_factory

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nombre del jugador")
        self._cfn_input = QLineEdit()
        self._cfn_input.setPlaceholderText("CFN ID (opcional)")
        add_button = QPushButton("Agregar jugador")
        add_button.clicked.connect(self._on_add_clicked)

        form_row = QHBoxLayout()
        form_row.addWidget(self._name_input)
        form_row.addWidget(self._cfn_input)
        form_row.addWidget(add_button)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["ID", "Nombre", "CFN ID"])
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        delete_button = QPushButton("Eliminar jugador seleccionado")
        delete_button.clicked.connect(self._on_delete_clicked)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Jugadores"))
        layout.addLayout(form_row)
        layout.addWidget(self._table)
        layout.addWidget(delete_button)
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        with self._session_factory() as session:
            players = list_players(session)

        self._table.setRowCount(len(players))
        for row, player in enumerate(players):
            self._table.setItem(row, 0, QTableWidgetItem(str(player.id)))
            self._table.setItem(row, 1, QTableWidgetItem(player.display_name))
            self._table.setItem(row, 2, QTableWidgetItem(player.cfn_id or ""))

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

    def _on_delete_clicked(self) -> None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(
                self, "Nada seleccionado", "Selecciona un jugador de la tabla primero."
            )
            return

        row = selected_rows[0].row()
        player_id = int(self._table.item(row, 0).text())
        with self._session_factory() as session:
            delete_player(session, player_id)
        self.refresh()
