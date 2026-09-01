from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

# Backend publico de tdf-edeportes (otro proyecto, ver
# github.com/SRGarciaVel/tdf-edeportes) - ahi vive el tracker real de
# CFN (checkpoint HUD-10). tdf-random-select nunca escribe ahi, solo lee
# el endpoint publico de win rate por personaje.
TDF_EDEPORTES_BASE_URL = "https://tdf-edeportes-backend.onrender.com"

# Timeout corto para la consulta real (el staff esta esperando en vivo,
# mejor fallar rapido y mostrar "sin datos" que colgar el draft), y uno
# mas generoso para la precarga (fire-and-forget, a nadie le importa
# cuanto tarde esa).
STATS_TIMEOUT_SECONDS = 6
WARMUP_TIMEOUT_SECONDS = 20


class CharacterStatsUnavailable(Exception):
    """El jugador no tiene CFN ID cargado, o la consulta a tdf-edeportes
    falló (red, timeout, o el jugador no existe en su roster) - en
    cualquiera de estos casos el HUD debe seguir funcionando igual sin
    esto, nunca tumbar el draft por un servicio externo caído (mismo
    criterio de modo degradado que ObsService, ver CODESTYLE.md)."""


def fetch_character_stats(cfn_id: str, character_display_name: str) -> dict:
    """Win rate total del jugador con ese personaje, leído del cache de
    tdf-edeportes (que a su vez lo saca de Buckler's Boot Camp). Nunca
    dispara un scrape en vivo - lee lo que ya está cacheado ahí.

    Devuelve dict con character_name/matches_played/win_rate/ever_played
    (mismo shape que CFNCharacterStatsRead del otro proyecto). Lanza
    CharacterStatsUnavailable si no se pudo consultar - el llamador
    decide qué mostrar en ese caso (nunca deja el HUD colgado).
    """
    url = (
        f"{TDF_EDEPORTES_BASE_URL}/cfn/players/{cfn_id}/character-stats/"
        f"{character_display_name}"
    )
    try:
        response = requests.get(url, timeout=STATS_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise CharacterStatsUnavailable(
            f"No se pudo conectar con tdf-edeportes: {exc}"
        ) from exc

    if response.status_code == 404:
        raise CharacterStatsUnavailable(
            f"El jugador {cfn_id} no existe en el roster de tdf-edeportes"
        )
    if response.status_code != 200:
        raise CharacterStatsUnavailable(
            f"tdf-edeportes respondió {response.status_code}"
        )
    return response.json()


def warm_up_tdf_edeportes() -> None:
    """Ping liviano para despertar el backend de tdf-edeportes ANTES de
    que el staff necesite de verdad las estadísticas (Render duerme la
    capa gratis a los 15 min sin tráfico, ~1 min de cold start - a
    pedido de Seba: "de modo que cuando se necesite desplegar la
    información las estadísticas ya estén despiertas"). Se llama en
    bucle desde un QTimer (ver main.py), nunca bloqueante para el draft
    en sí - cualquier error se loguea y se ignora, no hay nada que
    hacer distinto si esto falla, el próximo ping lo vuelve a intentar.
    """
    try:
        requests.get(
            f"{TDF_EDEPORTES_BASE_URL}/cfn/players",
            timeout=WARMUP_TIMEOUT_SECONDS,
        )
        logger.info("Precarga de tdf-edeportes OK")
    except requests.RequestException as exc:
        logger.warning(
            "Precarga de tdf-edeportes falló (se reintenta después): %s", exc
        )
