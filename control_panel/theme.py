"""Tema oscuro global del panel de control (checkpoint UI-1, ver
ROADMAP.md) - identidad visual de TDF (morado/magenta), la misma paleta
que ya usa el HUD por defecto.

PyQt6 no se ve "de Windows" solo por correr en Windows - sin estilo
propio usa el estilo Fusion/genérico de Qt, que se ve plano en cualquier
sistema operativo. En vez de perseguir el look nativo de Windows 11
literal (requeriría una librería de terceros tipo PyQt6-Fluent-Widgets),
se optó por un tema propio con la marca de TDF - mismo criterio que
usan apps profesionales como Discord o VS Code (Seba lo aprobó
explícitamente en el chat antes de programar esto).
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

# Paleta - misma familia de colores que el HUD (--hud-accent-color por
# defecto es #c400ff), pero fija acá: el tema del panel es una decisión
# de UI del staff, no algo que deba cambiar cuando alguien personaliza
# el color del HUD para el público en la pestaña Transmisión (son dos
# audiencias distintas).
BG_DARKEST = "#0f0c14"
BG_BASE = "#171220"
BG_SURFACE = "#1e1826"
BG_SURFACE_HOVER = "#28202f"
BORDER = "#3a3145"
BORDER_STRONG = "#4a3f57"
ACCENT = "#c400ff"
ACCENT_HOVER = "#d633ff"
ACCENT_PRESSED = "#a300d9"
TEXT_PRIMARY = "#f0eef2"
TEXT_SECONDARY = "#a8a0b0"
TEXT_DISABLED = "#5c5566"

DARK_THEME_QSS = f"""
QWidget {{
    background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
    font-size: 10pt;
}}

QMainWindow {{
    background-color: {BG_DARKEST};
}}

/* --- Pestañas --- */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background-color: {BG_BASE};
    border-radius: 4px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    padding: 8px 18px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background-color: {BG_SURFACE_HOVER};
    color: {TEXT_PRIMARY};
}}

/* --- Botones --- */
QPushButton {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
    border-radius: 5px;
    padding: 7px 14px;
}}

QPushButton:hover {{
    background-color: {BG_SURFACE_HOVER};
    border-color: {ACCENT};
}}

QPushButton:pressed {{
    background-color: {ACCENT_PRESSED};
    border-color: {ACCENT_PRESSED};
    color: white;
}}

QPushButton:disabled {{
    background-color: {BG_BASE};
    color: {TEXT_DISABLED};
    border-color: {BORDER};
}}

/* Botones de acción principal (Bloquear, Guardar, Iniciar...) llevan la
 * propiedad dinámica "accent" seteada desde Python para destacarse del
 * resto - ver theme.py::mark_as_primary_action(). */
QPushButton[accent="true"] {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: white;
    font-weight: 600;
}}

QPushButton[accent="true"]:hover {{
    background-color: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}

QPushButton[accent="true"]:disabled {{
    background-color: {BG_SURFACE};
    border-color: {BORDER};
    color: {TEXT_DISABLED};
}}

/* --- Campos de entrada --- */
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}

QLineEdit:disabled, QComboBox:disabled {{
    color: {TEXT_DISABLED};
    background-color: {BG_BASE};
}}

QComboBox::drop-down {{
    border: none;
    width: 22px;
}}

/* combobox-popup:0 fuerza el modo de popup "clasico" de Qt en vez del
 * nativo - con un QSS propio en QAbstractItemView, el modo nativo a
 * veces ignora la altura maxima real seteada en el codigo y deja un
 * hueco en blanco arriba de la lista (bug real encontrado por Seba,
 * ver tasks/lessons.md) - el modo clasico es el unico que respeta
 * setMaxVisibleItems()/setMaximumHeight() de forma confiable. */
QComboBox {{
    combobox-popup: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: none;
}}

/* --- Grupos y etiquetas --- */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {TEXT_SECONDARY};
}}

QLabel {{
    background-color: transparent;
}}

QLabel[secondary="true"] {{
    color: {TEXT_SECONDARY};
}}

/* --- Tablas y listas --- */
QTableWidget, QListWidget, QTreeWidget {{
    background-color: {BG_SURFACE};
    alternate-background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
}}

QHeaderView::section {{
    background-color: {BG_DARKEST};
    color: {TEXT_SECONDARY};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
}}

QTableWidget::item:selected, QListWidget::item:selected {{
    background-color: {ACCENT};
    color: white;
}}

/* --- Scrollbars finos --- */
QScrollBar:vertical {{
    background: {BG_BASE};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {BG_BASE};
    height: 10px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER_STRONG};
    border-radius: 5px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}

/* --- Checkboxes (personajes fuertes, etc.) --- */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {BORDER_STRONG};
    border-radius: 3px;
    background-color: {BG_SURFACE};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

/* --- Menús contextuales (clic derecho) --- */
QMenu {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background-color: {ACCENT};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

/* --- Cuadros de diálogo --- */
QMessageBox {{
    background-color: {BG_BASE};
}}

QToolTip {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_STRONG};
    padding: 4px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Aplica el tema oscuro global y la tipografía - se llama una sola
    vez en main.py antes de crear la ventana principal."""
    app.setStyleSheet(DARK_THEME_QSS)
    # Segoe UI es la tipografía nativa de Windows - ayuda a que la app
    # se sienta de verdad de ese sistema, no solo el color de fondo. Si
    # no está instalada (ej. corriendo en Linux/WSL para desarrollo),
    # Qt cae solo a la siguiente fuente disponible sin romper nada.
    app.setFont(QFont("Segoe UI", 10))


def mark_as_primary_action(button) -> None:
    """Marca un botón como la acción principal de su pantalla (Guardar,
    Bloquear, Iniciar baneo...) para que se destaque con el color de
    acento en vez del gris neutro - ver la regla QPushButton[accent] en
    DARK_THEME_QSS. Hay que re-aplicar el estilo del widget después de
    setProperty() para que el cambio se note al toque, Qt no lo hace
    solo."""
    button.setProperty("accent", "true")
    button.style().unpolish(button)
    button.style().polish(button)
