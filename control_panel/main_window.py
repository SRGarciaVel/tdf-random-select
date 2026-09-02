from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QMainWindow, QTabWidget, QVBoxLayout
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

    Orden y estructura de pestañas reorganizados en el checkpoint UX-1
    (ver ROADMAP.md) tras una conversación sobre qué tan comprensible es
    el flujo para un streamer no técnico: antes el orden era arbitrario
    (Jugadores, Setup, Baneo, Transmisión, OBS, Diagnóstico) mezclando
    "cosas que se configuran una vez" con "lo que se usa todos los
    días" sin ningún criterio. Ahora: primero lo que se configura una
    sola vez antes del primer torneo (OBS, Transmisión), después lo que
    se usa en cada evento (Jugadores, Setup) y por último lo que se usa
    constantemente en vivo (Baneo). "Diagnóstico" (herramienta de
    desarrollo, Ping/Test OBS, sin valor para el streamer en el día a
    día) salió de la barra de pestañas y pasó a un menú "Herramientas".
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        super().__init__()
        self.setWindowTitle("TDF Random Select")
        # 720x480 quedo chico desde que Baneo creció (panel de CFN,
        # grilla de personajes con retratos reales) - Seba lo vio real
        # al abrir la app sobre OBS y quedar apretada (checkpoint UI-4).
        self.resize(1050, 850)

        self._obs_screen = ObsSettingsScreen(session_factory)
        self._broadcast_screen = BroadcastSettingsScreen(session_factory)
        self._players_screen = PlayersScreen(session_factory)
        self._setup_screen = SetupScreen(session_factory)
        self._banning_screen = BanningScreen(session_factory)

        tabs = QTabWidget()
        tabs.addTab(self._obs_screen, "OBS")
        tabs.addTab(self._broadcast_screen, "Transmisión")
        tabs.addTab(self._players_screen, "Jugadores")
        tabs.addTab(self._setup_screen, "Setup")
        tabs.addTab(self._banning_screen, "Baneo")
        tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(tabs)

        self._diagnostics_screen = DiagnosticsScreen(session_factory)
        tools_menu = self.menuBar().addMenu("Herramientas")
        diagnostics_action = tools_menu.addAction("Diagnóstico...")
        diagnostics_action.triggered.connect(self._open_diagnostics)

    def _on_tab_changed(self, index: int) -> None:
        # Setup muestra el valor real del timer de baneo (checkpoint
        # UX-1) - si se cambió en Transmisión mientras tanto, esto lo
        # refresca cada vez que se vuelve a esta pestaña, no solo al
        # abrir la app.
        current_widget = self.centralWidget().widget(index)
        if current_widget is self._setup_screen:
            self._setup_screen.refresh_timer_label()

    def _open_diagnostics(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Diagnóstico")
        layout = QVBoxLayout()
        layout.addWidget(self._diagnostics_screen)
        dialog.setLayout(layout)
        dialog.resize(420, 240)
        dialog.exec()
