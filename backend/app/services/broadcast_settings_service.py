from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import BroadcastSettings

VALID_LOGO_CHOICES = ("tdf", "torneo")


def get_broadcast_settings(session: Session) -> BroadcastSettings:
    settings = session.query(BroadcastSettings).first()
    if settings is None:
        settings = BroadcastSettings()
        session.add(settings)
        session.commit()
    return settings


def update_broadcast_settings(
    session: Session,
    tournament_label: str | None,
    logo_choice: str,
    custom_logo_filename: str | None = None,
) -> BroadcastSettings:
    if logo_choice not in VALID_LOGO_CHOICES:
        raise ValueError(
            f"logo_choice debe ser uno de {VALID_LOGO_CHOICES}, no '{logo_choice}'."
        )
    settings = get_broadcast_settings(session)
    settings.tournament_label = (tournament_label or "").strip() or None
    settings.logo_choice = logo_choice
    if custom_logo_filename is not None:
        settings.custom_logo_filename = custom_logo_filename
    session.commit()
    return settings
