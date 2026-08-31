from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    bans_per_player: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # "auto_ban" (default, banea al azar) | "skip" (el turno se pierde
    # sin banear nada) - que pasa si se agota el timer de 30s sin que el
    # staff haya baneado a mano. Se elige al crear el torneo (SetupScreen).
    timeout_behavior: Mapped[str] = mapped_column(
        String, nullable=False, default="auto_ban"
    )

    matches: Mapped[list[Match]] = relationship(back_populates="tournament")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id"), nullable=False
    )
    player_a_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player_b_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    # SETUP | BANNING | RANDOMIZING | REVEAL | DONE - ver DraftService.
    status: Mapped[str] = mapped_column(String, nullable=False, default="SETUP")
    # Se fija recien al arrancar el baneo (start_banning), no en la creacion.
    first_banner_player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.UTC), nullable=False
    )

    tournament: Mapped[Tournament] = relationship(back_populates="matches")
    bans: Mapped[list[MatchBan]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchBan.turn_order",
    )
    results: Mapped[list[MatchResult]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


class MatchBan(Base):
    __tablename__ = "match_bans"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    # None = este turno se salto (timeout + timeout_behavior="skip") - no
    # se banea ningun personaje, pero el turno se consume igual.
    character_id: Mapped[str | None] = mapped_column(String, nullable=True)
    banned_by_player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"), nullable=False
    )
    turn_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # True si este registro salio por agotar el timer de 30s (aplica
    # tanto a un auto-baneo random como a un turno saltado) - el HUD lo
    # usa para mostrar el icono de timeout, sin importar si hubo o no
    # personaje baneado.
    was_timeout: Mapped[bool] = mapped_column(nullable=False, default=False)

    match: Mapped[Match] = relationship(back_populates="bans")

    __table_args__ = (
        # Un mismo personaje no puede banearse dos veces en el mismo match
        # (pool compartido, ver SPECS.md paragrafo 4) - reforzado a nivel de
        # constraint ademas de la validacion en DraftService.
        UniqueConstraint("match_id", "character_id", name="uq_match_character_ban"),
    )


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    assigned_character_id: Mapped[str] = mapped_column(String, nullable=False)

    match: Mapped[Match] = relationship(back_populates="results")
