from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.broadcast_settings_service import (
    get_broadcast_settings,
    update_broadcast_settings,
)


def test_get_creates_default_row_if_none_exists(session: Session) -> None:
    settings = get_broadcast_settings(session)
    assert settings.logo_choice == "tdf"
    assert settings.tournament_label is None

    # segunda llamada no crea una fila nueva
    settings_again = get_broadcast_settings(session)
    assert settings_again.id == settings.id


def test_update_sets_tournament_label_and_logo_choice(session: Session) -> None:
    settings = update_broadcast_settings(
        session, "Randomizer TDF 2026", "torneo", "logo.png"
    )
    assert settings.tournament_label == "Randomizer TDF 2026"
    assert settings.logo_choice == "torneo"
    assert settings.custom_logo_filename == "logo.png"


def test_update_strips_and_empties_blank_label_to_none(session: Session) -> None:
    settings = update_broadcast_settings(session, "   ", "tdf")
    assert settings.tournament_label is None


def test_update_rejects_invalid_logo_choice(session: Session) -> None:
    with pytest.raises(ValueError):
        update_broadcast_settings(session, "Torneo", "otra_cosa")


def test_update_without_new_logo_filename_keeps_previous(session: Session) -> None:
    update_broadcast_settings(session, "Torneo", "torneo", "logo.png")
    settings = update_broadcast_settings(
        session, "Torneo", "torneo"
    )  # sin filename nuevo
    assert settings.custom_logo_filename == "logo.png"
