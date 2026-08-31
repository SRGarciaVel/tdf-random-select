from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import Player
from backend.app.services.character_tag_service import (
    add_character_tag,
    delete_character_tag,
    list_character_tags,
)


def test_add_and_list_character_tags(session: Session, player_a: Player) -> None:
    add_character_tag(session, player_a.id, CHARACTER_IDS[0])
    add_character_tag(session, player_a.id, CHARACTER_IDS[1], note="secundario")

    tags = list_character_tags(session, player_a.id)
    assert {tag.character_id for tag in tags} == {CHARACTER_IDS[0], CHARACTER_IDS[1]}


def test_add_unknown_character_is_rejected(session: Session, player_a: Player) -> None:
    with pytest.raises(ValueError):
        add_character_tag(session, player_a.id, "personaje_que_no_existe")


def test_delete_character_tag(session: Session, player_a: Player) -> None:
    tag = add_character_tag(session, player_a.id, CHARACTER_IDS[0])
    delete_character_tag(session, tag.id)
    assert list_character_tags(session, player_a.id) == []


def test_tags_are_scoped_per_player(
    session: Session, player_a: Player, player_b: Player
) -> None:
    add_character_tag(session, player_a.id, CHARACTER_IDS[0])
    add_character_tag(session, player_b.id, CHARACTER_IDS[1])

    assert [tag.character_id for tag in list_character_tags(session, player_a.id)] == [
        CHARACTER_IDS[0]
    ]
    assert [tag.character_id for tag in list_character_tags(session, player_b.id)] == [
        CHARACTER_IDS[1]
    ]
