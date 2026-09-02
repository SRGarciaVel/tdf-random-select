from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class BroadcastPreset(Base):
    """Combo guardado de configuracion de Transmision (checkpoint UI-5,
    ver ROADMAP.md) - pensado para tener listo un preset armado con
    anticipacion (ej. "Torneo mensual", "Stream casual") y cambiar de
    uno a otro con un clic en vez de retocar cada campo a mano cada vez.

    Espeja los mismos campos configurables de BroadcastSettings, pero
    como filas independientes con nombre - "aplicar" un preset copia
    estos valores a la fila unica de BroadcastSettings.
    """

    __tablename__ = "broadcast_presets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    tournament_label: Mapped[str | None] = mapped_column(String, nullable=True)
    logo_choice: Mapped[str] = mapped_column(String, nullable=False, default="tdf")
    custom_logo_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    accent_color: Mapped[str] = mapped_column(String, nullable=False, default="#c400ff")
    panel_background_color: Mapped[str] = mapped_column(
        String, nullable=False, default="rgba(10, 5, 15, 0.35)"
    )
    ban_timer_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
