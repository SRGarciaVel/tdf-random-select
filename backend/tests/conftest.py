from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from backend.app.models import (
    Player,
    Tournament,
    get_engine,
    get_session_factory,
    init_db,
)


@pytest.fixture()
def session() -> Iterator[Session]:
    """SQLite real en un archivo temporal (no :memory:, no mocks) - se
    verifica el comportamiento real de constraints (UNIQUE, FK)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        engine = get_engine(f"sqlite:///{db_path}")
        init_db(engine)
        session_factory = get_session_factory(engine)
        db_session = session_factory()
        try:
            yield db_session
        finally:
            db_session.close()
            engine.dispose()


@pytest.fixture()
def tournament(session: Session) -> Tournament:
    tournament = Tournament(name="Torneo de prueba", bans_per_player=2)
    session.add(tournament)
    session.commit()
    return tournament


@pytest.fixture()
def player_a(session: Session) -> Player:
    player = Player(display_name="Jugador A")
    session.add(player)
    session.commit()
    return player


@pytest.fixture()
def player_b(session: Session) -> Player:
    player = Player(display_name="Jugador B")
    session.add(player)
    session.commit()
    return player
