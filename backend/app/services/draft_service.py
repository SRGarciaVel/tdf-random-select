from __future__ import annotations

import random

from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import Match, MatchBan, MatchResult


class DraftError(Exception):
    """Base de cualquier violacion de la maquina de estados del draft."""


class InvalidStateError(DraftError):
    """La operacion no es valida en el estado actual del match."""


class OutOfTurnError(DraftError):
    """Se intento banear fuera del turno que corresponde (alternado 1x1)."""


class CharacterAlreadyBannedError(DraftError):
    """El personaje ya fue baneado en este match (pool compartido)."""


class UnknownCharacterError(DraftError):
    """El character_id no existe en el roster de SF6."""


class DraftService:
    """Unico lugar donde vive la logica de negocio del draft (CODESTYLE.md:
    la logica de negocio no va en routers/handlers de Socket.IO ni en
    widgets de PyQt6).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_match(
        self, tournament_id: int, player_a_id: int, player_b_id: int
    ) -> Match:
        match = Match(
            tournament_id=tournament_id,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            status="SETUP",
        )
        self._session.add(match)
        self._session.commit()
        return match

    def start_banning(self, match_id: int, first_banner_player_id: int) -> Match:
        match = self._get_match(match_id)
        if match.status != "SETUP":
            raise InvalidStateError(
                f"No se puede iniciar el baneo desde el estado {match.status}."
            )
        if first_banner_player_id not in (match.player_a_id, match.player_b_id):
            raise DraftError(
                "first_banner_player_id debe ser uno de los dos jugadores del match."
            )
        match.first_banner_player_id = first_banner_player_id
        match.status = "BANNING"
        self._session.commit()
        return match

    def current_turn_player_id(self, match: Match) -> int:
        """A quien le toca banear ahora, alternado 1x1 (SPECS.md paragrafo 4)."""
        bans_count = len(match.bans)
        other_player_id = (
            match.player_b_id
            if match.first_banner_player_id == match.player_a_id
            else match.player_a_id
        )
        return match.first_banner_player_id if bans_count % 2 == 0 else other_player_id

    def ban_character(
        self, match_id: int, character_id: str, banned_by_player_id: int
    ) -> Match:
        match = self._get_match(match_id)
        if match.status != "BANNING":
            raise InvalidStateError(
                f"No se puede banear desde el estado {match.status}."
            )
        if character_id not in CHARACTER_IDS:
            raise UnknownCharacterError(
                f"'{character_id}' no es un personaje valido del roster."
            )

        expected_player_id = self.current_turn_player_id(match)
        if banned_by_player_id != expected_player_id:
            raise OutOfTurnError(
                f"Le toca banear al jugador {expected_player_id}, no a {banned_by_player_id}."
            )
        if any(
            existing_ban.character_id == character_id for existing_ban in match.bans
        ):
            raise CharacterAlreadyBannedError(
                f"'{character_id}' ya fue baneado en este match."
            )

        turn_order = len(match.bans)
        self._session.add(
            MatchBan(
                match_id=match.id,
                character_id=character_id,
                banned_by_player_id=banned_by_player_id,
                turn_order=turn_order,
            )
        )
        self._session.flush()
        self._session.refresh(match)

        total_bans_needed = match.tournament.bans_per_player * 2
        if len(match.bans) >= total_bans_needed:
            match.status = "RANDOMIZING"
        self._session.commit()
        return match

    def roll_random(self, match_id: int) -> list[MatchResult]:
        """Random independiente por jugador, con reposicion (mirror match
        permitido, SPECS.md paragrafo 4)."""
        match = self._get_match(match_id)
        if match.status != "RANDOMIZING":
            raise InvalidStateError(
                f"No se puede randomizar desde el estado {match.status}."
            )

        banned_ids = {ban.character_id for ban in match.bans}
        pool = [
            character_id
            for character_id in CHARACTER_IDS
            if character_id not in banned_ids
        ]
        if not pool:
            raise DraftError("No quedan personajes disponibles tras los baneos.")

        results = []
        for player_id in (match.player_a_id, match.player_b_id):
            assigned_character_id = random.choice(pool)
            result = MatchResult(
                match_id=match.id,
                player_id=player_id,
                assigned_character_id=assigned_character_id,
            )
            self._session.add(result)
            results.append(result)

        match.status = "REVEAL"
        self._session.commit()
        return results

    def complete_reveal(self, match_id: int) -> Match:
        match = self._get_match(match_id)
        if match.status != "REVEAL":
            raise InvalidStateError(
                f"No se puede completar desde el estado {match.status}."
            )
        match.status = "DONE"
        self._session.commit()
        return match

    def _get_match(self, match_id: int) -> Match:
        match = self._session.get(Match, match_id)
        if match is None:
            raise DraftError(f"No existe el match {match_id}.")
        return match
