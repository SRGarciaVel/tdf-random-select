from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Tournament


def list_tournaments(session: Session) -> list[Tournament]:
    return list(session.query(Tournament).order_by(Tournament.name).all())


def create_tournament(session: Session, name: str, bans_per_player: int) -> Tournament:
    name = name.strip()
    if not name:
        raise ValueError("El nombre del torneo no puede estar vacio.")
    if bans_per_player < 1:
        raise ValueError("bans_per_player debe ser al menos 1.")
    tournament = Tournament(name=name, bans_per_player=bans_per_player)
    session.add(tournament)
    session.commit()
    return tournament
