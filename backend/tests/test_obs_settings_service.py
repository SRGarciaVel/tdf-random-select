import pytest
from sqlalchemy.orm import Session

from backend.app.services.obs_settings_service import (
    get_obs_settings,
    update_obs_settings,
)


def test_get_creates_default_row_if_none_exists(session: Session) -> None:
    settings = get_obs_settings(session)
    assert settings.host == "localhost"
    assert settings.port == 4455
    assert settings.password is None
    assert settings.draft_scene_name is None


def test_update_sets_all_fields(session: Session) -> None:
    settings = update_obs_settings(
        session, "192.168.1.50", 4456, "secreto", "Escena Draft"
    )
    assert settings.host == "192.168.1.50"
    assert settings.port == 4456
    assert settings.password == "secreto"
    assert settings.draft_scene_name == "Escena Draft"


def test_update_empty_password_stores_none(session: Session) -> None:
    settings = update_obs_settings(session, "localhost", 4455, "", "Escena")
    assert settings.password is None


def test_update_empty_scene_name_strips_to_none(session: Session) -> None:
    settings = update_obs_settings(session, "localhost", 4455, None, "   ")
    assert settings.draft_scene_name is None


def test_update_rejects_empty_host(session: Session) -> None:
    with pytest.raises(ValueError):
        update_obs_settings(session, "   ", 4455, None, None)


def test_update_rejects_invalid_port(session: Session) -> None:
    with pytest.raises(ValueError):
        update_obs_settings(session, "localhost", 0, None, None)
    with pytest.raises(ValueError):
        update_obs_settings(session, "localhost", 70000, None, None)


def test_update_persists_across_gets(session: Session) -> None:
    update_obs_settings(session, "10.0.0.5", 4455, "pw", "Draft")
    settings = get_obs_settings(session)
    assert settings.host == "10.0.0.5"
    assert settings.draft_scene_name == "Draft"
