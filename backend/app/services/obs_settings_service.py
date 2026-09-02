from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import ObsSettings


def get_obs_settings(session: Session) -> ObsSettings:
    """Fila única de configuración de OBS (SPECS.md §5) - se crea con
    los defaults del modelo (localhost:4455, sin password/escena) la
    primera vez que se pide, mismo patrón que broadcast_settings."""
    settings = session.query(ObsSettings).first()
    if settings is None:
        settings = ObsSettings()
        session.add(settings)
        session.commit()
    return settings


def update_obs_settings(
    session: Session,
    host: str,
    port: int,
    password: str | None,
    draft_scene_name: str | None,
) -> ObsSettings:
    host = host.strip()
    if not host:
        raise ValueError("El host de OBS no puede estar vacío.")
    if not (1 <= port <= 65535):
        raise ValueError(f"Puerto inválido: {port} (debe estar entre 1 y 65535).")

    settings = get_obs_settings(session)
    settings.host = host
    settings.port = port
    settings.password = password or None
    settings.draft_scene_name = (draft_scene_name or "").strip() or None
    session.commit()
    return settings
