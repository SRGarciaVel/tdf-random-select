from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import Player, Tournament
from backend.app.services.draft_service import (
    DraftService,
    InvalidStateError,
    build_match_state_payload,
)


def test_auto_ban_bans_on_behalf_of_current_turn_player(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    match = service.auto_ban_random_character(match.id)

    assert len(match.bans) == 1
    assert match.bans[0].banned_by_player_id == player_a.id
    assert match.bans[0].character_id in CHARACTER_IDS
    # el turno avanzo igual que con un baneo manual
    assert service.current_turn_player_id(match) == player_b.id


def test_auto_ban_advances_state_machine_like_a_manual_ban(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    """tournament fixture tiene bans_per_player=2 -> 4 baneos totales."""
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    for _ in range(4):
        match = service.auto_ban_random_character(match.id)

    assert match.status == "RANDOMIZING"
    assert len(match.bans) == 4
    # sin repetidos - cada auto-baneo evito los ya baneados
    assert len({ban.character_id for ban in match.bans}) == 4


def test_auto_ban_never_repeats_an_already_banned_character(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)

    match = service.auto_ban_random_character(match.id)

    banned = [ban.character_id for ban in match.bans]
    assert banned[1] != CHARACTER_IDS[0]


def test_auto_ban_rejected_outside_banning_state(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)

    with pytest.raises(InvalidStateError):
        service.auto_ban_random_character(match.id)


def test_auto_ban_reflected_in_match_state_payload(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    """El overlay no distingue baneo manual de auto-baneo por timeout -
    el payload se ve identico en ambos casos."""
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.auto_ban_random_character(match.id)

    payload = build_match_state_payload(session, match.id)
    assert len(payload["banned_character_ids"]) == 1
    assert payload["current_turn_player_id"] == player_b.id
