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

    match = service.resolve_ban_timeout(match.id)

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
        match = service.resolve_ban_timeout(match.id)

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

    match = service.resolve_ban_timeout(match.id)

    banned = [ban.character_id for ban in match.bans]
    assert banned[1] != CHARACTER_IDS[0]


def test_auto_ban_rejected_outside_banning_state(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)

    with pytest.raises(InvalidStateError):
        service.resolve_ban_timeout(match.id)


def test_auto_ban_reflected_in_match_state_payload(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    """El overlay no distingue baneo manual de auto-baneo por timeout -
    el payload se ve identico en ambos casos."""
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.resolve_ban_timeout(match.id)

    payload = build_match_state_payload(session, match.id)
    assert len(payload["banned_character_ids"]) == 1
    assert payload["current_turn_player_id"] == player_b.id


def test_timeout_with_skip_behavior_consumes_turn_without_banning(
    session: Session, player_a: Player, player_b: Player
) -> None:
    skip_tournament = Tournament(
        name="Torneo skip", bans_per_player=2, timeout_behavior="skip"
    )
    session.add(skip_tournament)
    session.commit()

    service = DraftService(session)
    match = service.create_match(skip_tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    match = service.resolve_ban_timeout(match.id)

    assert len(match.bans) == 1
    assert match.bans[0].character_id is None
    assert match.bans[0].was_timeout is True
    assert match.bans[0].banned_by_player_id == player_a.id
    # el turno igual avanzo al otro jugador, aunque no se baneo nada
    assert service.current_turn_player_id(match) == player_b.id


def test_timeout_skip_does_not_remove_any_character_from_pool(
    session: Session, player_a: Player, player_b: Player
) -> None:
    skip_tournament = Tournament(
        name="Torneo skip 2", bans_per_player=1, timeout_behavior="skip"
    )
    session.add(skip_tournament)
    session.commit()

    service = DraftService(session)
    match = service.create_match(skip_tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.resolve_ban_timeout(match.id)
    match = service.resolve_ban_timeout(match.id)

    assert match.status == "RANDOMIZING"
    payload = build_match_state_payload(session, match.id)
    assert payload["banned_character_ids"] == []  # nada real fue baneado


def test_manual_ban_is_not_marked_as_timeout(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    match = service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)

    assert match.bans[0].was_timeout is False

    payload = build_match_state_payload(session, match.id)
    assert payload["bans"][0]["was_timeout"] is False
    assert payload["bans"][0]["character_id"] == CHARACTER_IDS[0]


def test_auto_ban_timeout_is_reflected_in_payload_bans_list(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.resolve_ban_timeout(match.id)

    payload = build_match_state_payload(session, match.id)
    assert payload["bans"][0]["was_timeout"] is True
    assert payload["bans"][0]["character_id"] in CHARACTER_IDS
