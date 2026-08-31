# ROADMAP.md — TDF Random Select

Hoja de ruta derivada de `SPECS.md`. Cada checkpoint marcado como
completado debe tener un commit correspondiente (`tipo: descripción`) —
ver `CODESTYLE.md`.

## Fase 0 — Walking skeleton

**Objetivo:** validar que las cuatro piezas de integración nuevas
(PyQt6 + `qasync`, Flask-SocketIO embebido, build de Vite servido por
Flask, conexión real a `obsws-python`) funcionan juntas de punta a
punta, antes de construir lógica de negocio. Ver `SPECS.md §7`.

- [x] Bootstrap del repo: `.md`s de estructura, `requirements.txt`,
      `overlay_app` scaffoldeado con Vite + React + TS.
- [x] `main.py` con ventana PyQt6 mínima (botón "Ping") corriendo sobre
      `qasync` sin bloquear el loop de eventos. Verificado: compila,
      importa, y `MainWindow` se instancia y muestra sin errores en modo
      `QT_QPA_PLATFORM=offscreen` (sin display real, ver `tasks/lessons.md`).
      Pendiente de validar en Windows con display real: que el layout se
      vea bien.
- [x] Backend Flask-SocketIO embebido, levantado en un thread aparte,
      sirviendo en `localhost:5001`. Verificado con curl real: `/health`
      responde 200, `/` sirve el `index.html` del build de Vite.
- [x] Evento `ping_from_control_panel` -> `ping_broadcast` probado de
      punta a punta con dos clientes Socket.IO reales (uno simulando el
      panel, otro el overlay) — el mensaje llega intacto.
- [x] `overlay_app` mínimo conectado por `socket.io-client`, escuchando
      `ping_broadcast`. Build real (`npm run build`) verificado, servido
      correctamente por Flask.
- [x] `ObsService`: conexión real intentada contra `localhost:4455` sin
      OBS corriendo en el sandbox, confirma que el error se captura y se
      re-lanza como `ObsConnectionError` (modo degradado, no crashea).
      **Pendiente de validar en la máquina de Seba:** conexión real
      contra una instancia de OBS corriendo, listar escenas reales, y
      `SetCurrentProgramScene` real.
- [ ] Validación combinada de las 5 piezas corriendo juntas en un solo
      proceso (`python main.py` completo, con click real del botón) en
      la máquina de Seba con display real y OBS corriendo — el sandbox
      no tiene ninguna de las dos cosas, así que cada pieza se verificó
      por separado pero falta la corrida integrada real.

## Fase 1 — Modelo de datos y lógica del draft

**Objetivo:** el backend sabe ejecutar un draft completo (aunque el
panel y el overlay todavía sean mínimos).

- [ ] Modelos SQLAlchemy + migraciones para `players`, `character_tags`,
      `tournaments`, `matches`, `match_bans`, `match_results`,
      `obs_settings` (ver `SPECS.md §6`).
- [ ] Roster completo de los 31 personajes de SF6 (id, nombre, ruta al
      retrato oficial) como dato semilla, no hardcodeado en lógica.
- [ ] Máquina de estados del match (`SETUP → BANNING → RANDOMIZING →
      REVEAL → DONE`) en `backend/app/services/`, con validación de
      turnos (no se puede banear fuera de orden, no se puede repetir un
      personaje ya baneado).
- [ ] Lógica de random con reposición (mirror match permitido) sobre el
      pool restante.
- [ ] Tests contra SQLite real cubriendo un draft completo de punta a
      punta, incluyendo el caso de baneo inválido (fuera de turno,
      personaje repetido).

## Fase 2 — Panel de control real (PyQt6)

- [ ] Pantalla de setup: elegir jugadores, cantidad de baneos, cargar
      `character_tags` por jugador.
- [ ] Pantalla de baneo en vivo: grilla de personajes, resalta el
      personaje si está en `character_tags` del rival, indica de quién
      es el turno.
- [ ] Pantalla de configuración de OBS (host, puerto, password, nombre
      de la escena de draft) persistida en `obs_settings`.
- [ ] Botones "Iniciar Baneo" y override manual de "Volver a escena
      anterior", disparando `obs_service` en paralelo al evento de
      Socket.IO.

## Fase 3 — Overlay real (React + Framer Motion)

- [ ] Grilla de 31 personajes con retratos oficiales de Capcom.
- [ ] Animación de baneo (personaje tachado/oscurecido en el momento que
      llega el evento).
- [ ] Animación de reveal tipo LoL para el personaje asignado a cada
      jugador.
- [ ] Verificación de que el overlay se ve bien dentro de un Browser
      Source real de OBS (dimensiones, fondo transparente donde
      corresponda).

## Fase 4 — Automatización completa de OBS

- [ ] `obs_service` guarda la escena activa antes de `SetCurrentProgramScene`
      hacia la escena de draft.
- [ ] Vuelta automática a la escena guardada al terminar `REVEAL`, con
      el override manual del panel funcionando en cualquier momento.
- [ ] Manejo de error explícito si OBS no está corriendo o la conexión
      falla (modo degradado, ver `CODESTYLE.md`).

## Fase 5 — Empaquetado

- [ ] `.exe` con PyInstaller (`--onefile`), estáticos de `overlay_app`
      empaquetados adentro (`--add-data`), sin depender de carpetas
      externas.
- [ ] Probado en una máquina Windows limpia (sin Python ni Node
      instalados) antes de entregar al CEO.
- [ ] Definir si se firma el ejecutable o se vive con el warning de
      SmartScreen (ver `SPECS.md §8`).

## Notas de proceso

- Cualquier bullet que se descubra necesario a mitad de camino se agrega
  aquí antes de implementarlo, no después.
- Las piezas que dependen de hardware/software que solo existe en la
  máquina de Seba (OBS real, ejecución con display real en Windows)
  quedan marcadas explícitamente como pendientes de validación local
  aunque el resto del checkpoint esté verificado en el sandbox.
