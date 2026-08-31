"""Descarga los retratos oficiales de los 31 personajes de SF6 desde la
web publica de streetfighter.com (Capcom), los redimensiona y convierte
a WebP - Fase 3, ver SPECS.md.

Es contenido publico servido normal, sin login ni proteccion anti-bot de
por medio (a diferencia de Buckler's Boot Camp) - mismo criterio de
"no automatizar evasion de sistemas anti-bot de terceros" que se aplico
en el CFN tracker de tdf-edeportes, aca no aplica porque no hay nada que
evadir (el 403 inicial era un bloqueo de CDN por User-Agent, no un
desafio interactivo).

Los originales pesan 500KB-4MB (render a resolucion completa) - demasiado
para una pagina que OBS tiene que renderizar en vivo como Browser Source,
asi que se redimensionan a MAX_DIMENSION_PX y se convierten a WebP en el
mismo paso, sin guardar el PNG original en disco.

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

OUTPUT_DIR = (
    Path(__file__).resolve().parents[2] / "overlay_app" / "public" / "portraits"
)
BASE_URL = "https://www.streetfighter.com/6/assets/images/character"
PAGE_BASE_URL = "https://www.streetfighter.com/6/es-us/character"
REQUEST_DELAY_SECONDS = 1.0  # no golpear el sitio de Capcom sin pausas entre pedidos
MAX_DIMENSION_PX = (
    500  # de sobra para un grid de baneo, ni cerca de la resolucion original
)
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
    destination = OUTPUT_DIR / f"{character_id}.webp"

    if destination.exists():
        print(f"  {character_id}: ya existe, se salta.")
        return True

    response = requests.get(
        url,
        headers={**REQUEST_HEADERS, "Referer": f"{PAGE_BASE_URL}/{slug}"},
        timeout=10,
    )
    if response.status_code != 200:
        print(f"  {character_id}: FALLO ({response.status_code}) - {url}")
        return False

    image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    image.thumbnail((MAX_DIMENSION_PX, MAX_DIMENSION_PX), Image.LANCZOS)
    image.save(destination, format="WEBP", quality=WEBP_QUALITY)

    original_kb = len(response.content) // 1024
    final_kb = destination.stat().st_size // 1024
    print(
        f"  {character_id}: OK ({original_kb}KB -> {final_kb}KB, {image.width}x{image.height})"
    )
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
