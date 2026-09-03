# -*- mode: python ; coding: utf-8 -*-
"""Spec de PyInstaller para TDF Random Select (Fase 5, ver ROADMAP.md).

Genera un .exe de un solo archivo (--onefile). Corre en la MISMA
maquina donde se compila - Windows produce un .exe de Windows, Linux
produce un binario de Linux, no hay cross-compilation. Seba tiene que
correr esto desde Windows real (no WSL2) para el .exe de verdad.

Que va DENTRO del .exe (solo lectura, se re-extrae en cada arranque a
una carpeta temporal que despues se borra):
- El build de Vite (overlay_app/build) - HTML/JS/CSS ya compilados.

Que NO va dentro del .exe (tiene que vivir en una carpeta real al lado
del .exe, sobrevive entre arranques, Seba lo sigue pudiendo actualizar
sin re-empaquetar nada):
- overlay_app/public/portraits, portraits-large, branding
- tdf_random_select.db (la base de datos real)
Ver backend/app/paths.py para el detalle de como se resuelve cada ruta
segun este empaquetado o no.

Uso (desde una consola de Windows real, no WSL2, con el venv activado):
    pyinstaller tdf_random_select.spec

El resultado queda en dist/TDF Random Select.exe - antes de compartirlo,
copiar la carpeta overlay_app/public/ (con portraits/, portraits-large/,
y branding/ si existen) al lado de ese .exe, preservando la misma
estructura relativa que ya tiene el proyecto.

Icono: assets/icon.ico (recorte cuadrado de la cara de la mascota de
TDF, fondo removido con flood-fill desde los bordes - no un umbral
global, para no perforar agujeros si el personaje tenía algún detalle
claro propio). Generado con 7 resoluciones (16 a 256px) en el mismo
.ico, como corresponde para que Windows lo use bien tanto chico en la
barra de tareas como grande en el escritorio.
"""

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("overlay_app/build", "overlay_app/build"),
    ],
    hiddenimports=[
        # Flask-SocketIO/Engine.IO a veces no detectan el driver async
        # elegido en tiempo de ejecucion via analisis estatico -
        # requirements.txt no trae eventlet/gevent, asi que el modo
        # real es "threading" (Werkzeug + simple-websocket).
        "engineio.async_drivers.threading",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TDF Random Select",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # console=False: confirmado en Windows real (01-09-2026) que la app
    # arranca bien empaquetada - la ventana de consola de la primera
    # prueba ya cumplio su proposito (ver ROADMAP.md, Fase 5). Si algo
    # falla mas adelante y hace falta ver el error, cambiar esto a
    # True de nuevo temporalmente.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
