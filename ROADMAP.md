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
