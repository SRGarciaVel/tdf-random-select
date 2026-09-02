from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.broadcast_preset_service import (
    apply_preset,
    delete_preset,
    list_presets,
    save_preset,
)
from backend.app.services.broadcast_settings_service import (
    get_broadcast_settings,
    update_broadcast_settings,
)


def test_save_preset_captures_current_settings(session: Session) -> None:
    update_broadcast_settings(
        session,
        "Torneo Mensual",
        "tdf",
        accent_color="#ff0000",
        ban_timer_seconds=45,
    )
    preset = save_preset(session, "Mensual")

    assert preset.tournament_label == "Torneo Mensual"
    assert preset.accent_color == "#ff0000"
    assert preset.ban_timer_seconds == 45


def test_save_preset_with_same_name_overwrites(session: Session) -> None:
    update_broadcast_settings(session, "Version 1", "tdf")
    save_preset(session, "Mi Preset")

    update_broadcast_settings(session, "Version 2", "tdf")
    save_preset(session, "Mi Preset")

    presets = list_presets(session)
    assert len(presets) == 1  # no duplico, piso el existente
    assert presets[0].tournament_label == "Version 2"


def test_save_preset_rejects_empty_name(session: Session) -> None:
    with pytest.raises(ValueError):
        save_preset(session, "   ")


def test_apply_preset_copies_into_live_settings(session: Session) -> None:
    update_broadcast_settings(
        session, "Torneo Casual", "tdf", accent_color="#00ff00", ban_timer_seconds=20
    )
    preset = save_preset(session, "Casual")

    # cambiar la config actual a otra cosa completamente distinta
    update_broadcast_settings(
        session, "Otro nombre", "tdf", accent_color="#0000ff", ban_timer_seconds=60
    )

    applied = apply_preset(session, preset.id)
    assert applied.tournament_label == "Torneo Casual"
    assert applied.accent_color == "#00ff00"
    assert applied.ban_timer_seconds == 20

    # confirmar que de verdad quedo en la fila real, no solo en el valor devuelto
    live = get_broadcast_settings(session)
    assert live.tournament_label == "Torneo Casual"


def test_apply_nonexistent_preset_raises(session: Session) -> None:
    with pytest.raises(ValueError):
        apply_preset(session, 9999)


def test_delete_preset_removes_it(session: Session) -> None:
    update_broadcast_settings(session, "X", "tdf")
    preset = save_preset(session, "A borrar")
    delete_preset(session, preset.id)
    assert list_presets(session) == []


def test_delete_nonexistent_preset_does_not_raise(session: Session) -> None:
    delete_preset(session, 9999)  # no debe reventar


def test_list_presets_ordered_by_name(session: Session) -> None:
    update_broadcast_settings(session, "X", "tdf")
    save_preset(session, "Zeta")
    save_preset(session, "Alfa")

    names = [p.name for p in list_presets(session)]
    assert names == ["Alfa", "Zeta"]
