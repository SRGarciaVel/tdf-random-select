from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class BroadcastSettings(Base):
    """Fila unica con la config del panel central del HUD de baneo
    (checkpoint HUD-2) - nombre del torneo a mostrar y que logo usar.
    Configurable por el CEO, no depende de que torneo/match este activo.
    """

    __tablename__ = "broadcast_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Texto libre para el panel central - si esta vacio, el overlay cae
    # al nombre real del Tournament activo (ver build_broadcast_payload).
    tournament_label: Mapped[str | None] = mapped_column(String, nullable=True)
    # "tdf" (logo por defecto del club) | "torneo" (logo custom subido)
    logo_choice: Mapped[str] = mapped_column(String, nullable=False, default="tdf")
    # Nombre de archivo dentro de overlay_app/public/branding/ - solo se
    # usa cuando logo_choice == "torneo". Requiere un "npm run build"
    # despues de cambiarlo para que el overlay lo sirva (mismo criterio
    # que los retratos de download_portraits.py).
    custom_logo_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    # Personalizacion visual del HUD (checkpoint HUD-5) - colores CSS
    # validos (hex u otro formato CSS), aplicados via custom properties
    # en el overlay. Defaults = la paleta magenta/violeta actual del club.
    accent_color: Mapped[str] = mapped_column(String, nullable=False, default="#c400ff")
    panel_background_color: Mapped[str] = mapped_column(
        String, nullable=False, default="rgba(10, 5, 15, 0.35)"
    )
