from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import Player, Tournament
from backend.app.services.draft_service import DraftService, build_match_state_payload


def test_payload_with_no_match_selected(session: Session) -> None:
    assert build_match_state_payload(session, None) == {"match_id": None}


def test_payload_for_nonexistent_match(session: Session) -> None:
    assert build_match_state_payload(session, 9999) == {"match_id": None}


def test_payload_in_setup_state(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)

    payload = build_match_state_payload(session, match.id)
    assert payload["match_id"] == match.id
    assert payload["status"] == "SETUP"
    assert payload["player_a"] == {"id": player_a.id, "display_name": "Jugador A"}
    assert payload["player_b"] == {"id": player_b.id, "display_name": "Jugador B"}
    assert payload["banned_character_ids"] == []
    assert payload["current_turn_player_id"] is None
    assert payload["results"] is None


def test_payload_in_banning_state_tracks_turn_and_bans(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    payload = build_match_state_payload(session, match.id)
    assert payload["status"] == "BANNING"
    assert payload["current_turn_player_id"] == player_a.id
    assert payload["banned_character_ids"] == []

    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)
    payload = build_match_state_payload(session, match.id)
    assert payload["banned_character_ids"] == [CHARACTER_IDS[0]]
    assert payload["current_turn_player_id"] == player_b.id  # se alterno el turno


def test_payload_in_reveal_state_includes_results(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[1], player_b.id)
    service.ban_character(match.id, CHARACTER_IDS[2], player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[3], player_b.id)
    service.roll_random(match.id)

    payload = build_match_state_payload(session, match.id)
    assert payload["status"] == "REVEAL"
    assert payload["current_turn_player_id"] is None  # ya no hay turno de baneo
    assert set(payload["results"].keys()) == {str(player_a.id), str(player_b.id)}
    for character_id in payload["results"].values():
        assert character_id in CHARACTER_IDS
        assert character_id not in payload["banned_character_ids"]
