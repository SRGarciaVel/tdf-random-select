from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    cfn_id: Mapped[str | None] = mapped_column(String, nullable=True)

    character_tags: Mapped[list[CharacterTag]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class CharacterTag(Base):
    """ "Personaje fuerte conocido" de un jugador (SPECS.md paragrafo 4).

    Es solo referencia visual durante el baneo, nunca filtra la grilla.
    """

    __tablename__ = "character_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    character_id: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    player: Mapped[Player] = relationship(back_populates="character_tags")
