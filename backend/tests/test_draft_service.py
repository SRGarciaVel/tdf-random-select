from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.data.sf6_roster import CHARACTER_IDS
from backend.app.models import MatchBan, Player, Tournament
from backend.app.services.draft_service import (
    CharacterAlreadyBannedError,
    DraftService,
    InvalidStateError,
    OutOfTurnError,
    UnknownCharacterError,
)


def test_full_draft_happy_path(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    assert match.status == "SETUP"

    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    assert match.status == "BANNING"

    # tournament.bans_per_player = 2 -> 4 baneos totales, alternado A,B,A,B
    assert service.current_turn_player_id(match) == player_a.id
    match = service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)
    assert service.current_turn_player_id(match) == player_b.id
    match = service.ban_character(match.id, CHARACTER_IDS[1], player_b.id)
    match = service.ban_character(match.id, CHARACTER_IDS[2], player_a.id)
    match = service.ban_character(match.id, CHARACTER_IDS[3], player_b.id)

    assert match.status == "RANDOMIZING"
    assert len(match.bans) == 4

    results = service.roll_random(match.id)
    assert len(results) == 2
    banned_ids = {
        CHARACTER_IDS[0],
        CHARACTER_IDS[1],
        CHARACTER_IDS[2],
        CHARACTER_IDS[3],
    }
    for result in results:
        assert result.assigned_character_id not in banned_ids
        assert result.assigned_character_id in CHARACTER_IDS

    match = service.complete_reveal(match.id)
    assert match.status == "DONE"


def test_mirror_match_allowed_with_reposicion(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    """Con pool_size=1 (25 de los 26 personajes baneados), el random le
    asigna deterministicamente el mismo personaje a ambos jugadores -
    confirma que hay reposicion real (SPECS.md paragrafo 4: mirror match
    permitido). El estado se arma directo porque bans_per_player*2 siempre
    da un total par y 25 es impar - no es alcanzable vía el flujo normal
    de ban_character, pero roll_random no depende de bans_per_player, solo
    de match.bans y match.status."""
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    banned_ids = CHARACTER_IDS[:-1]  # deja 1 solo personaje sin banear
    for turn_order, character_id in enumerate(banned_ids):
        banned_by = player_a.id if turn_order % 2 == 0 else player_b.id
        session.add(
            MatchBan(
                match_id=match.id,
                character_id=character_id,
                banned_by_player_id=banned_by,
                turn_order=turn_order,
            )
        )
    match.status = "RANDOMIZING"
    session.commit()
    session.refresh(match)
    assert len(match.bans) == len(CHARACTER_IDS) - 1

    results = service.roll_random(match.id)
    assigned = {result.assigned_character_id for result in results}
    assert assigned == {CHARACTER_IDS[-1]}  # el unico personaje restante, para ambos


def test_ban_out_of_turn_is_rejected(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    with pytest.raises(OutOfTurnError):
        service.ban_character(match.id, CHARACTER_IDS[0], player_b.id)


def test_ban_repeated_character_is_rejected(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)

    with pytest.raises(CharacterAlreadyBannedError):
        service.ban_character(match.id, CHARACTER_IDS[0], player_b.id)


def test_ban_unknown_character_is_rejected(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)

    with pytest.raises(UnknownCharacterError):
        service.ban_character(match.id, "personaje_que_no_existe", player_a.id)


def test_cannot_ban_before_start_banning(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)

    with pytest.raises(InvalidStateError):
        service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)


def test_cannot_roll_random_before_bans_complete(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)  # falta 1

    with pytest.raises(InvalidStateError):
        service.roll_random(match.id)


def test_cannot_complete_reveal_before_reveal_state(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)

    with pytest.raises(InvalidStateError):
        service.complete_reveal(match.id)


def test_unique_constraint_blocks_duplicate_ban_at_db_level(
    session: Session, tournament: Tournament, player_a: Player, player_b: Player
) -> None:
    """La constraint UNIQUE(match_id, character_id) es una segunda capa de
    defensa ademas de la validacion de DraftService (CODESTYLE.md: nunca
    confiar solo en la validacion de aplicacion para invariantes de datos)."""
    from sqlalchemy.exc import IntegrityError

    service = DraftService(session)
    match = service.create_match(tournament.id, player_a.id, player_b.id)
    match = service.start_banning(match.id, first_banner_player_id=player_a.id)
    service.ban_character(match.id, CHARACTER_IDS[0], player_a.id)

    # Insercion directa saltandose DraftService, para probar la constraint
    # de la base de datos en si, no la validacion de Python.
    session.add(
        MatchBan(
            match_id=match.id,
            character_id=CHARACTER_IDS[0],
            banned_by_player_id=player_b.id,
            turn_order=99,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
