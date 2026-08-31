"""Descarga los retratos oficiales de los 31 personajes de SF6 desde la
web publica de streetfighter.com (Capcom) - Fase 3, ver SPECS.md.

Es contenido publico servido normal, sin login ni proteccion anti-bot de
por medio (a diferencia de Buckler's Boot Camp) - mismo criterio de
"no automatizar evasion de sistemas anti-bot de terceros" que se aplico
en el CFN tracker de tdf-edeportes, aca no aplica porque no hay nada que
evadir.

Uso: python -m backend.scripts.download_portraits
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

from backend.app.data.sf6_roster import CHARACTER_IDS

# El "id" interno (usado en toda la logica del draft) no siempre coincide
# con el slug real que usa streetfighter.com en sus URLs - solo se listan
# aca las excepciones, todo lo demas usa el id tal cual.
SITE_SLUG_OVERRIDES: dict[str, str] = {
    "chun_li": "chunli",
    "dee_jay": "deejay",
    "e_honda": "ehonda",
    "a_k_i": "aki",
    "akuma": "gouki_akuma",
    "m_bison": "vega_mbison",
    "c_viper": "cviper",
}

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "overlay_app" / "public" / "portraits"
BASE_URL = "https://www.streetfighter.com/6/assets/images/character"
REQUEST_DELAY_SECONDS = 1.0  # no golpear el sitio de Capcom sin pausas entre pedidos


def site_slug(character_id: str) -> str:
    return SITE_SLUG_OVERRIDES.get(character_id, character_id)


def download_portrait(character_id: str) -> bool:
    slug = site_slug(character_id)
    url = f"{BASE_URL}/{slug}/{slug}.png"
    destination = OUTPUT_DIR / f"{character_id}.png"

    if destination.exists():
        print(f"  {character_id}: ya existe, se salta.")
        return True

    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print(f"  {character_id}: FALLO ({response.status_code}) - {url}")
        return False

    destination.write_bytes(response.content)
    print(f"  {character_id}: OK ({len(response.content)} bytes)")
    return True


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando retratos a {OUTPUT_DIR}\n")

    failures = []
    for character_id in CHARACTER_IDS:
        ok = download_portrait(character_id)
        if not ok:
            failures.append(character_id)
        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nListo: {len(CHARACTER_IDS) - len(failures)}/{len(CHARACTER_IDS)} retratos descargados.")
    if failures:
        print(f"Fallaron: {', '.join(failures)}")
        print("Revisa el slug de estos personajes a mano en streetfighter.com/6/es-us/character")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
