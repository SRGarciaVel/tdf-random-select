from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.tournament_service import create_tournament, list_tournaments


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
