from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget
from sqlalchemy.orm import sessionmaker

from control_panel.screens.banning_screen import BanningScreen
from control_panel.screens.diagnostics_screen import DiagnosticsScreen
from control_panel.screens.players_screen import PlayersScreen
from control_panel.screens.setup_screen import SetupScreen


class MainWindow(QMainWindow):
    """Shell de navegacion del panel de control (Fase 2, ver ROADMAP.md).

    Cada pestana es una pantalla independiente (control_panel/screens/),
    reciben lo que necesitan (session_factory, etc.) por constructor en
    vez de ir a buscarlo global - mismo criterio que los servicios del
    backend (CODESTYLE.md).
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self.setWindowTitle("TDF Random Select")
        self.resize(720, 480)

        tabs = QTabWidget()
        tabs.addTab(PlayersScreen(session_factory), "Jugadores")
        tabs.addTab(SetupScreen(session_factory), "Setup")
        tabs.addTab(BanningScreen(session_factory), "Baneo")
        tabs.addTab(DiagnosticsScreen(), "Diagnóstico")
        self.setCentralWidget(tabs)
