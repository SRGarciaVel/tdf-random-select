from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import Match, MatchBan, Player
from backend.app.services.draft_service import DraftService
from backend.app.services.tournament_service import (
    create_tournament,
    delete_tournament,
    list_tournaments,
)


def test_create_and_list_tournaments(session: Session) -> None:
    create_tournament(session, "  Torneo B  ", 2)
    create_tournament(session, "Torneo A", 1)

    tournaments = list_tournaments(session)
    assert [t.name for t in tournaments] == ["Torneo A", "Torneo B"]  # orden alfabetico
    torneo_b = next(t for t in tournaments if t.name == "Torneo B")
    assert torneo_b.bans_per_player == 2


def test_create_tournament_with_empty_name_is_rejected(session: Session) -> None:
    with pytest.raises(ValueError):
        create_tournament(session, "   ", 1)


def test_create_tournament_with_invalid_bans_is_rejected(session: Session) -> None:
    with pytest.raises(ValueError):
        create_tournament(session, "Torneo X", 0)


def test_delete_tournament_removes_it(session: Session) -> None:
    tournament = create_tournament(session, "A borrar", 1)
    delete_tournament(session, tournament.id)
    assert list_tournaments(session) == []


def test_delete_nonexistent_tournament_does_not_raise(session: Session) -> None:
    delete_tournament(session, 9999)  # no debe reventar


def test_delete_tournament_cascades_to_matches_and_bans(session: Session) -> None:
    """El caso real que motivo este checkpoint: Seba tenia 28 partidas de
    prueba acumuladas bajo un torneo - hay que poder borrar el torneo
    entero sin dejar matches/bans huerfanos en la base."""
    tournament = create_tournament(session, "Torneo con partidas", 1)
    player_a = Player(display_name="A")
    player_b = Player(display_name="B")
    session.add_all([player_a, player_b])
    session.commit()

    match = DraftService(session).create_match(tournament.id, player_a.id, player_b.id)
    DraftService(session).start_banning(match.id, player_a.id)
    DraftService(session).ban_character(match.id, CHARACTER_IDS[0], player_a.id)

    match_id = match.id
    assert session.query(MatchBan).filter(MatchBan.match_id == match_id).count() == 1

    delete_tournament(session, tournament.id)

    assert list_tournaments(session) == []
    assert session.get(Match, match_id) is None
    assert session.query(MatchBan).filter(MatchBan.match_id == match_id).count() == 0
