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
      `qasync` sin bloquear el loop de eventos. Validado en la máquina de
      Seba (WSL2 con WSLg, sin GPU passthrough real — solo warnings de
      `libEGL`/`ZINK`, no bloqueantes): la ventana abre y renderiza bien.
- [x] Backend Flask-SocketIO embebido, levantado en un thread aparte,
      sirviendo en `localhost:5001`. Verificado con curl real: `/health`
      responde 200, `/` sirve el `index.html` del build de Vite.
- [x] Evento `ping_from_control_panel` -> `ping_broadcast` probado de
      punta a punta con dos clientes Socket.IO reales (uno simulando el
      panel, otro el overlay) — el mensaje llega intacto. Validado además
      en la máquina de Seba con el botón real del panel (requirió subir
      `wait_timeout` de 1s a 10s, ver `tasks/lessons.md`).
- [x] `overlay_app` mínimo conectado por `socket.io-client`, escuchando
      `ping_broadcast`. Build real (`npm run build`) verificado, servido
      correctamente por Flask.
- [x] `ObsService`: validado en la máquina de Seba contra una instancia
      real de OBS 32.2.2 con WebSocket Server habilitado y password —
      `list_scenes()` devolvió la escena real ("Escena"). Requirió sumar
      `OBS_HOST`/`OBS_PORT`/`OBS_PASSWORD` como env vars (ver
      `tasks/lessons.md`, WSL2 en modo NAT no comparte `localhost` con
      Windows). `SetCurrentProgramScene` real (cambio de escena de
      verdad) queda para la Fase 4, cuando se construya el flujo
      completo de baneo — acá solo se validó la conexión y el listado.
- [ ] Confirmación visual pendiente: que el overlay (`localhost:5001` en
      un navegador) efectivamente muestre el mensaje del Ping en pantalla,
      no solo que el panel diga "enviado".
- [x] Las piezas del walking skeleton corriendo juntas en un solo
      proceso (`python main.py`) en la máquina real de Seba (WSL2 +
      WSLg + OBS real en Windows): ventana abre, backend levanta, Ping
      conecta, Test OBS lista escenas reales. Falta únicamente la
      confirmación visual del overlay (ítem de arriba) para cerrar la
      fase por completo y pasar a la Fase 1.

## Fase 1 — Modelo de datos y lógica del draft

**Objetivo:** el backend sabe ejecutar un draft completo (aunque el
panel y el overlay todavía sean mínimos).

- [x] Modelos SQLAlchemy + migraciones para `players`, `character_tags`,
      `tournaments`, `matches`, `match_bans`, `match_results`,
      `obs_settings` (ver `SPECS.md §6`). Sin Alembic todavía — con
      `Base.metadata.create_all()` alcanza mientras el schema no está
      estable; se agrega Alembic si hace falta versionar una migración
      real más adelante.
- [x] Roster completo de los 26 personajes de SF6 que tengo registrados
      (id, nombre, campo para retrato pendiente) como dato semilla en
      `backend/app/data/sf6_roster.py`, no hardcodeado en lógica.
      **Pendiente: confirmar contra el roster oficial vigente** antes de
      la Fase 3 — la lista de SF6 crece con cada season pass.
- [x] Máquina de estados del match (`SETUP → BANNING → RANDOMIZING →
      REVEAL → DONE`) en `backend/app/services/draft_service.py`, con
      validación de turnos y de personajes repetidos.
- [x] Lógica de random con reposición (mirror match permitido) sobre el
      pool restante.
- [x] Tests contra SQLite real (archivo temporal, no `:memory:`, no
      mocks) cubriendo un draft completo de punta a punta, los casos de
      baneo inválido (fuera de turno, personaje repetido, personaje
      inexistente, transiciones de estado inválidas), el mirror match
      determinístico, y la constraint UNIQUE a nivel de base de datos
      como segunda capa de defensa. **9/9 tests pasan.**

## Fase 2 — Panel de control real (PyQt6)

- [x] Shell de navegación (`QTabWidget`) reemplazando la ventana única
      del walking skeleton. `MainWindow` recibe `session_factory` por
      constructor (engine/schema se crean una sola vez en `main.py`) y
      se lo pasa a cada pestaña — nada de estado global.
- [x] Pantalla "Jugadores": alta/listado/baja contra SQLite real
      (`backend/app/services/player_service.py`, con tests). Base para
      elegir Jugador A/B en el setup del match.
- [x] Pantalla "Diagnóstico": el Ping + Test OBS del walking skeleton,
      migrado a su propia pestaña — se mantiene porque sigue sirviendo
      para diagnosticar conexión sin armar un match real.
- [x] Pantalla de setup del match: pestaña "Setup" — elegir un torneo
      existente o crear uno nuevo (nombre + `bans_per_player`), elegir
      Jugador A/B desde la lista de jugadores, cargar `character_tags`
      por jugador (agregar/quitar con doble clic), y crear el `Match`
      (queda en estado `SETUP`, listo para la pantalla de baneo).
      Servicios nuevos con tests: `tournament_service.py`,
      `character_tag_service.py`. Probado con una simulación completa de
      la UI real (crear 2 jugadores, torneo nuevo, tags, match) contra
      SQLite real — no solo los servicios por separado.
- [x] Pantalla de baneo en vivo: pestaña "Baneo" — selector de partidas
      abiertas, elegir quién banea primero, grilla de 26 personajes con
      ★ marcando los personajes fuertes del rival (`character_tags`),
      turno indicado en pantalla, clic para banear (avanza sola por
      `SETUP → BANNING → RANDOMIZING` al completar los baneos), botón
      "Randomizar" y "Completar reveal" hasta `DONE`. Probado con clics
      reales sobre los botones de la grilla, de punta a punta, contra
      SQLite real (no simulando las llamadas al servicio directo, sino
      el click real de cada botón). **Confirmado funcionando en la
      máquina de Seba** (match real AckermanFG vs BazthyFreeman, de
      SETUP a DONE).

Fase 2 completa — lo que falta de OBS (pantalla de configuración real y
el disparo de `obs_service` desde "Iniciar Baneo") se movió a la Fase 4,
donde tiene más sentido junto con el resto de la automatización de OBS.

## Fase 3 — Overlay real (React + Framer Motion)

- [x] Retratos oficiales de los 31 personajes descargados y optimizados
      (`backend/scripts/download_portraits.py` — WebP, ~50-120KB c/u,
      bajados de 500KB-4MB originales). No se versionan en git (se
      regeneran con el script).
- [x] **Checkpoint A: contrato de eventos panel → overlay.**
      `build_match_state_payload()` en `draft_service.py` arma el estado
      completo del match (status, jugadores, baneados, turno actual,
      resultados) — función pura, testeada contra SQLite real en cada
      estado del draft. `OverlayBridge` (panel) lo empuja via Socket.IO
      (`match_state_update`), con el mismo modo degradado que
      `ObsService` si el backend no está arriba. `BanningScreen` lo
      dispara después de cada acción. **Bug real encontrado y corregido
      en el proceso**: al completar el reveal, el match sale de
      `list_open_matches()` y el selector se limpia — sin emitir el
      estado `DONE` *antes* de refrescar la lista, el overlay nunca veía
      el reveal final, solo el match desapareciendo (ver
      `tasks/lessons.md`). Probado de punta a punta: backend real +
      `BanningScreen` real (clics) + cliente Socket.IO simulando el
      overlay, confirmando que llegan los 6 estados
      (`SETUP → BANNING → BANNING → RANDOMIZING → REVEAL → DONE`) con
      los datos correctos en cada uno.
- [ ] Grilla de 31 personajes con retratos oficiales de Capcom en React.
- [ ] Animación de baneo (personaje tachado/oscurecido en el momento que
      llega el evento).
- [ ] Animación de reveal tipo LoL para el personaje asignado a cada
      jugador.
- [ ] Verificación de que el overlay se ve bien dentro de un Browser
      Source real de OBS (dimensiones, fondo transparente donde
      corresponda).

## Fase 4 — Automatización completa de OBS

- [ ] Pantalla de configuración de OBS en el panel: reemplaza las env
      vars `OBS_HOST`/`OBS_PORT`/`OBS_PASSWORD` del walking skeleton por
      la tabla `obs_settings` real (host, puerto, password, nombre de la
      escena de draft).
- [ ] Botón "Iniciar Baneo" dispara en paralelo el evento de Socket.IO
      hacia el overlay (Fase 3) y `obs_service.switch_to_draft_scene()`.
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
