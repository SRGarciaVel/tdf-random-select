"""Resolución de rutas consciente de PyInstaller (Fase 5, ver ROADMAP.md).

Con `--onefile`, PyInstaller descomprime todo el contenido empaquetado
en una carpeta TEMPORAL nueva en cada arranque (`sys._MEIPASS`) que se
borra al cerrar la app - perfecta para archivos de solo lectura que
nunca cambian sin una actualización de código (el build de Vite), pero
un desastre para cualquier cosa que tenga que sobrevivir entre
corridas: la base de datos, los retratos, los logos. Si esos vivieran
ahí adentro, cada reinicio de la app arrancaría con todo vacío.

Por eso hay DOS funciones, no una:

- `get_bundle_dir()`: para leer assets de solo lectura empaquetados
  adentro del .exe (el build de Vite). Apunta a la carpeta temporal de
  extracción cuando está empaquetado.
- `get_external_data_dir()`: para todo lo que tiene que persistir y que
  Seba pueda seguir actualizando sin re-empaquetar (retratos nuevos con
  `download_portraits.py`, logos elegidos desde el panel, la base de
  datos real). Apunta a la carpeta real donde vive el .exe, NUNCA a la
  temporal.

En modo desarrollo (corriendo desde el código fuente, sin empaquetar)
las dos devuelven lo mismo: la raíz del proyecto - mismo comportamiento
que tenía el código antes de este checkpoint, nada cambia para el flujo
de trabajo habitual de Seba en WSL2.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller expone la carpeta temporal de extraccion en
        # sys._MEIPASS (atributo que solo existe cuando esta
        # empaquetado - por eso el getattr de arriba, no un import
        # directo).
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def get_external_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


# --- Rutas concretas que usa el resto de la app - un solo lugar para
# calcularlas, en vez de que cada pantalla/modulo las repita a mano
# (antes habia 3 copias del mismo calculo: aca, en banning_screen.py y
# en broadcast_settings_screen.py - riesgo real de que se corrija en un
# lugar y se olvide en otro). ---

OVERLAY_BUILD_DIR = get_bundle_dir() / "overlay_app" / "build"

OVERLAY_PUBLIC_DIR = get_external_data_dir() / "overlay_app" / "public"
PORTRAITS_DIR = OVERLAY_PUBLIC_DIR / "portraits"
PORTRAITS_LARGE_DIR = OVERLAY_PUBLIC_DIR / "portraits-large"
BRANDING_DIR = OVERLAY_PUBLIC_DIR / "branding"

DEFAULT_DB_PATH = get_external_data_dir() / "tdf_random_select.db"
