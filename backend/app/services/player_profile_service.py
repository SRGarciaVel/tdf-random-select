from __future__ import annotations

import logging

import requests

from backend.app.services.character_stats_service import TDF_EDEPORTES_BASE_URL

logger = logging.getLogger(__name__)

PROFILE_TIMEOUT_SECONDS = 6


class PlayerProfileUnavailable(Exception):
    """El jugador no está registrado en tdf-edeportes, o la consulta
    falló (red, timeout) - checkpoint UI-2, ver ROADMAP.md. Mismo
    criterio de modo degradado que character_stats_service: la pantalla
    de Jugadores tiene que poder mostrarse igual aunque esto falle."""


def fetch_player_profile(cfn_id: str) -> dict:
    """Rango/MR/LP/personaje actual del jugador, leído del cache de
    tdf-edeportes (GET /cfn/players/{cfn_id}) - mismo shape que
    CFNPlayerRead del otro proyecto, acá solo se usan los campos de
    estado actual (liga, MR, LP, personaje), el resto (avatar, bio,
    redes, etc.) no aplica en este contexto.

    Lanza PlayerProfileUnavailable si no se pudo consultar - el
    llamador decide qué mostrar en ese caso (nunca deja la pantalla
    colgada ni rompe por un servicio externo caído).
    """
    url = f"{TDF_EDEPORTES_BASE_URL}/cfn/players/{cfn_id}"
    try:
        response = requests.get(url, timeout=PROFILE_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise PlayerProfileUnavailable(
            f"No se pudo conectar con tdf-edeportes: {exc}"
        ) from exc

    if response.status_code == 404:
        raise PlayerProfileUnavailable(
            f"El jugador {cfn_id} no está registrado en tdf-edeportes"
        )
    if response.status_code != 200:
        raise PlayerProfileUnavailable(
            f"tdf-edeportes respondió {response.status_code}"
        )
    return response.json()
