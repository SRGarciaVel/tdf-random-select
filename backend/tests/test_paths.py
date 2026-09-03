from __future__ import annotations

import importlib
import sys


def test_dev_mode_uses_project_root() -> None:
    import backend.app.paths as paths

    importlib.reload(paths)
    assert paths.DEFAULT_DB_PATH.name == "tdf_random_select.db"
    assert paths.PORTRAITS_DIR.parts[-3:] == ("overlay_app", "public", "portraits")
    assert paths.OVERLAY_BUILD_DIR.parts[-2:] == ("overlay_app", "build")
    assert paths.ICON_PATH.parts[-2:] == ("assets", "icon.ico")


def test_frozen_mode_keeps_persistent_data_next_to_exe() -> None:
    """Con PyInstaller --onefile, sys._MEIPASS es una carpeta temporal
    que se borra al cerrar la app - la base de datos, los retratos y
    los logos NUNCA pueden vivir ahi, tienen que quedar al lado del
    .exe real (Fase 5, ver ROADMAP.md)."""
    import backend.app.paths as paths

    sys.frozen = True  # type: ignore[attr-defined]
    sys.executable = "/fake/dist/TDF Random Select.exe"
    sys._MEIPASS = "/tmp/_MEI_test_fake"  # type: ignore[attr-defined]
    try:
        importlib.reload(paths)
        assert str(paths.DEFAULT_DB_PATH).startswith("/fake/dist")
        assert "_MEI" not in str(paths.DEFAULT_DB_PATH)
        assert str(paths.PORTRAITS_DIR).startswith("/fake/dist")
        assert "_MEI" not in str(paths.PORTRAITS_DIR)
        assert str(paths.BRANDING_DIR).startswith("/fake/dist")
        assert "_MEI" not in str(paths.BRANDING_DIR)
    finally:
        del sys.frozen  # type: ignore[attr-defined]
        del sys.executable
        del sys._MEIPASS  # type: ignore[attr-defined]
        importlib.reload(paths)  # dejar el modulo en modo dev otra vez


def test_frozen_mode_reads_bundled_overlay_build_from_temp_extraction() -> None:
    """El build de Vite es de solo lectura y no cambia sin una
    actualizacion de codigo - va empaquetado adentro del .exe (se
    extrae a sys._MEIPASS en cada arranque), a diferencia de los datos
    persistentes."""
    import backend.app.paths as paths

    sys.frozen = True  # type: ignore[attr-defined]
    sys.executable = "/fake/dist/TDF Random Select.exe"
    sys._MEIPASS = "/tmp/_MEI_test_fake"  # type: ignore[attr-defined]
    try:
        importlib.reload(paths)
        assert str(paths.OVERLAY_BUILD_DIR).startswith("/tmp/_MEI_test_fake")
        assert str(paths.ICON_PATH).startswith("/tmp/_MEI_test_fake")
    finally:
        del sys.frozen  # type: ignore[attr-defined]
        del sys.executable
        del sys._MEIPASS  # type: ignore[attr-defined]
        importlib.reload(paths)
