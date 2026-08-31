from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import CharacterTag


def add_character_tag(
    session: Session, player_id: int, character_id: str, note: str | None = None
) -> CharacterTag:
    if character_id not in CHARACTER_IDS:
        raise ValueError(f"'{character_id}' no es un personaje valido del roster.")
    tag = CharacterTag(
        player_id=player_id,
        character_id=character_id,
        note=(note or "").strip() or None,
    )
    session.add(tag)
    session.commit()
    return tag


def list_character_tags(session: Session, player_id: int) -> list[CharacterTag]:
    return list(session.query(CharacterTag).filter_by(player_id=player_id).all())


def delete_character_tag(session: Session, tag_id: int) -> None:
    tag = session.get(CharacterTag, tag_id)
    if tag is not None:
        session.delete(tag)
        session.commit()
