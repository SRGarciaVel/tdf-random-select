from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.player_service import (
    add_player,
    delete_player,
    list_players,
    update_player,
)


def test_add_and_list_players(session: Session) -> None:
    add_player(session, "  Sirxtias  ", cfn_id=" 2844671427 ")
    add_player(session, "Drachen")

    players = list_players(session)
    assert [p.display_name for p in players] == [
        "Drachen",
        "Sirxtias",
    ]  # orden alfabetico
    sirxtias = next(p for p in players if p.display_name == "Sirxtias")
    assert sirxtias.cfn_id == "2844671427"  # se limpio el espacio


def test_add_player_with_empty_name_is_rejected(session: Session) -> None:
    with pytest.raises(ValueError):
        add_player(session, "   ")


def test_add_player_without_cfn_id_stores_none(session: Session) -> None:
    player = add_player(session, "Jugador sin CFN")
    assert player.cfn_id is None


def test_delete_player(session: Session) -> None:
    player = add_player(session, "A borrar")
    delete_player(session, player.id)
    assert list_players(session) == []


def test_delete_nonexistent_player_does_not_raise(session: Session) -> None:
    delete_player(session, 9999)  # no debe reventar


def test_update_player_renames(session: Session) -> None:
    player = add_player(session, "Nombre viejo")
    updated = update_player(session, player.id, display_name="Nombre nuevo")
    assert updated.display_name == "Nombre nuevo"


def test_update_player_sets_cfn_id(session: Session) -> None:
    player = add_player(session, "Jugador")
    updated = update_player(session, player.id, cfn_id="1733837998")
    assert updated.cfn_id == "1733837998"


def test_update_player_clears_cfn_id_with_empty_string(session: Session) -> None:
    player = add_player(session, "Jugador", cfn_id="123")
    updated = update_player(session, player.id, cfn_id="")
    assert updated.cfn_id is None


def test_update_player_none_leaves_field_untouched(session: Session) -> None:
    player = add_player(session, "Jugador", cfn_id="123")
    updated = update_player(session, player.id, display_name="Renombrado")
    assert updated.cfn_id == "123"  # no se toco porque cfn_id=None (default)


def test_update_player_rejects_empty_name(session: Session) -> None:
    player = add_player(session, "Jugador")
    with pytest.raises(ValueError):
        update_player(session, player.id, display_name="   ")


def test_update_nonexistent_player_raises(session: Session) -> None:
    with pytest.raises(ValueError):
        update_player(session, 9999, display_name="Nadie")
