from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget
from sqlalchemy.orm import sessionmaker

from control_panel.screens.banning_screen import BanningScreen
from control_panel.screens.broadcast_settings_screen import BroadcastSettingsScreen
from control_panel.screens.diagnostics_screen import DiagnosticsScreen
from control_panel.screens.obs_settings_screen import ObsSettingsScreen
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
        # 720x480 quedo chico desde que Baneo creció (panel de CFN,
        # grilla de personajes con retratos reales) - Seba lo vio real
        # al abrir la app sobre OBS y quedar apretada (checkpoint UI-4).
        self.resize(1050, 850)

        tabs = QTabWidget()
        tabs.addTab(PlayersScreen(session_factory), "Jugadores")
        tabs.addTab(SetupScreen(session_factory), "Setup")
        tabs.addTab(BanningScreen(session_factory), "Baneo")
        tabs.addTab(BroadcastSettingsScreen(session_factory), "Transmisión")
        tabs.addTab(ObsSettingsScreen(session_factory), "OBS")
        tabs.addTab(DiagnosticsScreen(session_factory), "Diagnóstico")
        self.setCentralWidget(tabs)
