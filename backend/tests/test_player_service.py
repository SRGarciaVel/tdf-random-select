from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.player_service import add_player, delete_player, list_players


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
