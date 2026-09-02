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


def delete_tournament(session: Session, tournament_id: int) -> None:
    """Elimina un torneo y TODOS sus matches (checkpoint UI-3, ver
    ROADMAP.md) - pensado para limpiar torneos de prueba o corregir un
    nombre mal puesto. Cascada real via Tournament.matches (que a su vez
    cascadea a MatchBan/MatchResult), no hace falta borrar nivel por
    nivel a mano. No hace nada si el torneo ya no existe (mismo
    criterio que delete_player)."""
    tournament = session.get(Tournament, tournament_id)
    if tournament is not None:
        session.delete(tournament)
        session.commit()
