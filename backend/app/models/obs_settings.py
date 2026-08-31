from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ObsSettings(Base):
    """Fila unica con la config de conexion a OBS (ver SPECS.md paragrafo 5).

    Reemplaza a las variables de entorno OBS_HOST/OBS_PORT/OBS_PASSWORD
    del walking skeleton una vez que exista la pantalla de configuracion
    real (Fase 2 del ROADMAP).
    """

    __tablename__ = "obs_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    host: Mapped[str] = mapped_column(String, nullable=False, default="localhost")
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=4455)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    draft_scene_name: Mapped[str | None] = mapped_column(String, nullable=True)
