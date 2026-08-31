from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Tournament

VALID_TIMEOUT_BEHAVIORS = ("auto_ban", "skip")


def list_tournaments(session: Session) -> list[Tournament]:
    return list(session.query(Tournament).order_by(Tournament.name).all())


def create_tournament(
    session: Session,
    name: str,
    bans_per_player: int,
    timeout_behavior: str = "auto_ban",
) -> Tournament:
    name = name.strip()
    if not name:
        raise ValueError("El nombre del torneo no puede estar vacio.")
    if bans_per_player < 1:
        raise ValueError("bans_per_player debe ser al menos 1.")
    if timeout_behavior not in VALID_TIMEOUT_BEHAVIORS:
        raise ValueError(
            f"timeout_behavior debe ser uno de {VALID_TIMEOUT_BEHAVIORS}, no '{timeout_behavior}'."
        )
    tournament = Tournament(
        name=name, bans_per_player=bans_per_player, timeout_behavior=timeout_behavior
    )
    session.add(tournament)
    session.commit()
    return tournament
