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


def delete_player(session: Session, player_id: int) -> None:
    player = session.get(Player, player_id)
    if player is not None:
        session.delete(player)
        session.commit()
