from __future__ import annotations

import re

from sqlalchemy.orm import Session

from backend.app.models import BroadcastSettings

VALID_LOGO_CHOICES = ("tdf", "torneo")
# Chequeo laxo, no un parser de CSS completo - alcanza para evitar que se
# guarde texto que no sirve como color (vacio, basura tipeada a mano).
COLOR_PATTERN = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|[a-zA-Z]+)$"
)


def get_broadcast_settings(session: Session) -> BroadcastSettings:
    settings = session.query(BroadcastSettings).first()
    if settings is None:
        settings = BroadcastSettings()
        session.add(settings)
        session.commit()
    return settings


def _validate_color(value: str, field_name: str) -> str:
    value = value.strip()
    if not COLOR_PATTERN.match(value):
        raise ValueError(
            f"'{value}' no parece un color CSS valido para {field_name} "
            f"(usa #hex, rgba(...), hsl(...) o un nombre como 'purple')."
        )
    return value


def update_broadcast_settings(
    session: Session,
    tournament_label: str | None,
    logo_choice: str,
    custom_logo_filename: str | None = None,
    accent_color: str | None = None,
    panel_background_color: str | None = None,
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
    if accent_color is not None:
        settings.accent_color = _validate_color(accent_color, "accent_color")
    if panel_background_color is not None:
        settings.panel_background_color = _validate_color(
            panel_background_color, "panel_background_color"
        )
    session.commit()
    return settings
