"""Descarga los retratos oficiales de los 31 personajes de SF6 desde la
web publica de streetfighter.com (Capcom) - Fase 3, ver SPECS.md.

Es contenido publico servido normal, sin login ni proteccion anti-bot de
por medio (a diferencia de Buckler's Boot Camp) - mismo criterio de
"no automatizar evasion de sistemas anti-bot de terceros" que se aplico
en el CFN tracker de tdf-edeportes, aca no aplica porque no hay nada que
evadir (el 403 inicial era un bloqueo de CDN por User-Agent, no un
desafio interactivo).

Genera DOS tamanos por personaje, de la misma descarga:
- Chico (WebP, ~500px): para los slots de baneo, que se ven muchos a la
  vez y no necesitan resolucion alta.
- Grande (PNG, ~2400px): para el panel dramatico full-height del HUD
  (checkpoint HUD-5), donde una sola imagen ocupa gran parte de la
  pantalla y la calidad se nota - PNG en vez de WebP comprimido, a
  pedido explicito de Seba tras ver el HUD real (ver tasks/lessons.md).

Uso: python -m backend.scripts.download_portraits
Requiere Pillow (ver requirements-dev.txt).
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import requests
from PIL import Image

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

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "overlay_app" / "public"
OUTPUT_DIR = PUBLIC_DIR / "portraits"
LARGE_OUTPUT_DIR = PUBLIC_DIR / "portraits-large"
BASE_URL = "https://www.streetfighter.com/6/assets/images/character"
PAGE_BASE_URL = "https://www.streetfighter.com/6/es-us/character"
REQUEST_DELAY_SECONDS = 1.0  # no golpear el sitio de Capcom sin pausas entre pedidos
MAX_DIMENSION_PX = (
    500  # de sobra para un grid de baneo, ni cerca de la resolucion original
)
LARGE_MAX_DIMENSION_PX = 2400  # panel dramatico full-height - se nota la calidad
WEBP_QUALITY = 85

# El CDN de Capcom devuelve 403 a la firma por defecto de requests
# ("python-requests/x.y") - no es un desafio anti-bot interactivo (no hay
# Turnstile ni nada que resolver, a diferencia de Buckler's Boot Camp),
# es un filtro de CDN por User-Agent/Referer que cualquier navegador
# manda solo. Estos headers imitan eso.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}


def site_slug(character_id: str) -> str:
    return SITE_SLUG_OVERRIDES.get(character_id, character_id)


def download_portrait(character_id: str) -> bool:
    slug = site_slug(character_id)
    url = f"{BASE_URL}/{slug}/{slug}.png"
    small_destination = OUTPUT_DIR / f"{character_id}.webp"
    large_destination = LARGE_OUTPUT_DIR / f"{character_id}.png"

    if small_destination.exists() and large_destination.exists():
        print(f"  {character_id}: ya existen ambos tamanos, se salta.")
        return True

    response = requests.get(
        url,
        headers={**REQUEST_HEADERS, "Referer": f"{PAGE_BASE_URL}/{slug}"},
        timeout=10,
    )
    if response.status_code != 200:
        print(f"  {character_id}: FALLO ({response.status_code}) - {url}")
        return False

    original_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    original_kb = len(response.content) // 1024

    if not small_destination.exists():
        small_image = original_image.copy()
        small_image.thumbnail((MAX_DIMENSION_PX, MAX_DIMENSION_PX), Image.LANCZOS)
        small_image.save(small_destination, format="WEBP", quality=WEBP_QUALITY)

    if not large_destination.exists():
        large_image = original_image.copy()
        large_image.thumbnail(
            (LARGE_MAX_DIMENSION_PX, LARGE_MAX_DIMENSION_PX), Image.LANCZOS
        )
        large_image.save(large_destination, format="PNG")

    small_kb = small_destination.stat().st_size // 1024
    large_kb = large_destination.stat().st_size // 1024
    print(
        f"  {character_id}: OK ({original_kb}KB original -> "
        f"chico {small_kb}KB, grande {large_kb}KB)"
    )
    return True


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LARGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando retratos a {OUTPUT_DIR} y {LARGE_OUTPUT_DIR}\n")

    failures = []
    for character_id in CHARACTER_IDS:
        ok = download_portrait(character_id)
        if not ok:
            failures.append(character_id)
        time.sleep(REQUEST_DELAY_SECONDS)

    print(
        f"\nListo: {len(CHARACTER_IDS) - len(failures)}/{len(CHARACTER_IDS)} retratos descargados."
    )
    if failures:
        print(f"Fallaron: {', '.join(failures)}")
        print(
            "Revisa el slug de estos personajes a mano en streetfighter.com/6/es-us/character"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
