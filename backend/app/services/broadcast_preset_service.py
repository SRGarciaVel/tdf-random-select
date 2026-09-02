from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import BroadcastPreset, BroadcastSettings
from backend.app.services.broadcast_settings_service import (
    validate_color,
    get_broadcast_settings,
)


def list_presets(session: Session) -> list[BroadcastPreset]:
    return list(session.query(BroadcastPreset).order_by(BroadcastPreset.name).all())


def save_preset(session: Session, name: str) -> BroadcastPreset:
    """Guarda la configuración ACTUAL de BroadcastSettings como un preset
    nuevo con nombre - checkpoint UI-5, para tener listo un combo armado
    de antemano (ej. "Torneo mensual", "Stream casual") y poder volver a
    él con un clic más adelante. Si ya existe un preset con ese nombre,
    lo pisa (permite "actualizar" un preset guardado)."""
    name = name.strip()
    if not name:
        raise ValueError("El nombre del preset no puede estar vacío.")

    current = get_broadcast_settings(session)
    preset = session.query(BroadcastPreset).filter(BroadcastPreset.name == name).first()
    if preset is None:
        preset = BroadcastPreset(name=name)
        session.add(preset)

    preset.tournament_label = current.tournament_label
    preset.logo_choice = current.logo_choice
    preset.custom_logo_filename = current.custom_logo_filename
    preset.accent_color = current.accent_color
    preset.panel_background_color = current.panel_background_color
    preset.ban_timer_seconds = current.ban_timer_seconds
    preset.sponsor_logo_filename = current.sponsor_logo_filename
    session.commit()
    return preset


def apply_preset(session: Session, preset_id: int) -> BroadcastSettings:
    """Copia los valores de un preset guardado a la fila única de
    BroadcastSettings (la que de verdad lee el overlay)."""
    preset = session.get(BroadcastPreset, preset_id)
    if preset is None:
        raise ValueError(f"No existe el preset {preset_id}.")

    settings = get_broadcast_settings(session)
    settings.tournament_label = preset.tournament_label
    settings.logo_choice = preset.logo_choice
    settings.custom_logo_filename = preset.custom_logo_filename
    settings.accent_color = validate_color(preset.accent_color, "accent_color")
    settings.panel_background_color = validate_color(
        preset.panel_background_color, "panel_background_color"
    )
    settings.ban_timer_seconds = preset.ban_timer_seconds
    settings.sponsor_logo_filename = preset.sponsor_logo_filename
    session.commit()
    return settings


def delete_preset(session: Session, preset_id: int) -> None:
    preset = session.get(BroadcastPreset, preset_id)
    if preset is not None:
        session.delete(preset)
        session.commit()
