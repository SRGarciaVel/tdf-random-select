from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Player


def get_player(session: Session, player_id: int) -> Player | None:
    return session.get(Player, player_id)


def add_player(
    session: Session, display_name: str, cfn_id: str | None = None
) -> Player:
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("display_name no puede estar vacio.")
    player = Player(display_name=display_name, cfn_id=(cfn_id or "").strip() or None)
    session.add(player)
    session.commit()
    return player


def list_players(session: Session) -> list[Player]:
    return list(session.query(Player).order_by(Player.display_name).all())


def update_player(
    session: Session,
    player_id: int,
    display_name: str | None = None,
    cfn_id: str | None = None,
) -> Player:
    """Renombrar/editar el CFN ID de un jugador ya existente - checkpoint
    UI-2, clic derecho > Renombrar en la pantalla de Jugadores.
    display_name/cfn_id en None significa "no tocar ese campo", no
    "vaciarlo" - para vaciar el CFN ID a propósito, pasar cadena vacía
    explícita."""
    player = session.get(Player, player_id)
    if player is None:
        raise ValueError(f"No existe el jugador {player_id}.")
    if display_name is not None:
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("display_name no puede estar vacio.")
        player.display_name = display_name
    if cfn_id is not None:
        player.cfn_id = cfn_id.strip() or None
    session.commit()
    return player


def delete_player(session: Session, player_id: int) -> None:
    player = session.get(Player, player_id)
    if player is not None:
        session.delete(player)
        session.commit()
