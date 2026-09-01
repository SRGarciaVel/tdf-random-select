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
- [x] **Checkpoint B: grilla real de React.** `/api/roster` en el backend
      expone el roster (una sola fuente de verdad, el overlay ya no
      duplica la lista de personajes en TS). `DraftOverlay.tsx` es un
      componente puro (props: `matchState` + `roster`, sin socket ni
      fetch adentro) que renderiza la grilla de 31 retratos, marca los
      baneados (gris + tachado visual), muestra de quién es el turno, y
      cambia a un panel de resultados en `REVEAL`/`DONE`. `App.tsx` solo
      hace el fetch inicial y escucha `match_state_update`, delega el
      render. 6 tests con Vitest + Testing Library cubriendo los mismos
      6 estados que ya se probaron en Python (idle, SETUP, BANNING,
      RANDOMIZING, REVEAL, DONE). Probado además de punta a punta contra
      el backend real: `index.html` + el JS del build + `/api/roster`
      servidos juntos correctamente por el mismo Flask. **Confirmado
      visualmente en la máquina de Seba**: grilla completa en `SETUP`,
      turno + ★ en `BANNING`, grises los baneados, `RANDOMIZING`, y las
      dos cards de resultado en `REVEAL` — los 6 estados se ven
      correctos en el navegador real, no solo en los tests.
- [x] Animación de baneo: desaturado + pulso de escala + tajo diagonal
      rojo/blanco que cruza el retrato al confirmarse, con Framer
      Motion. Corre una sola vez por baneo (remount vía `key`), no se
      repite en re-renders posteriores del mismo match. 7 tests
      (incluye uno específico: el tajo solo aparece en el personaje
      recién baneado, no en los demás).
- [x] Animación de reveal: cada resultado entra con zoom-in + fade desde
      abajo (spring, no lineal), escalonado entre Jugador A y B
      (delay 0 / 0.15s), con un aura magenta pulsante alrededor del
      retrato mientras está en pantalla (CSS `@keyframes`, glow
      continuo). Fase 3 completa: grilla, contrato de eventos,
      confirmación visual en Browser Source real, y las dos animaciones.
- [x] Verificación de que el overlay se ve bien dentro de un Browser
      Source real de OBS (dimensiones, fondo transparente donde
      corresponda). **Confirmado**: la grilla se ve completa y el fondo
      transparente compone bien sobre la escena.

## Fase 3.5 — Rediseño HUD del overlay (referencia LCK/broadcast real)

**Objetivo:** reemplazar la grilla centrada por una franja tipo HUD de
torneo real (nombres en los extremos, slots de baneo centro→afuera por
jugador, panel central configurable, timer de 30s por baneo con
auto-baneo al agotarse, reveal final en los extremos en vez de al
centro). Ver conversación del 31-08-2026 para el detalle completo del
diseño acordado.

- [x] **Checkpoint HUD-1: timer de 30s + política de timeout
      configurable.** `Tournament.timeout_behavior` ("auto_ban" | "skip",
      elegible al crear el torneo en Setup). `DraftService.resolve_ban_timeout()`
      resuelve según esa política: banea al azar o salta el turno sin
      banear nada (`MatchBan.character_id = None`). `MatchBan.was_timeout`
      marca cualquiera de los dos casos, independiente de si hubo
      personaje — es lo que el HUD usará para el ícono de timeout.
      `_record_turn()` centraliza la inserción + auto-transición de
      estado, compartida entre baneo manual y timeout (sin duplicar la
      lógica de conteo). `build_match_state_payload()` ahora expone
      `bans` (lista completa ordenada con `character_id`/`was_timeout`)
      además del `banned_character_ids` de siempre. 13 tests nuevos
      contra SQLite real (auto_ban, skip, payload, y que un baneo manual
      nunca quede marcado `was_timeout`). `BanningScreen` maneja un
      `QTimer` real (30s en producción, `timer_ms` configurable para
      tests): arranca solo cuando el turno cambia, se detiene fuera de
      `BANNING`, y llama a `resolve_ban_timeout()` si se agota. Probado
      con un `QTimer` real acortado a 200ms.
- [x] **Checkpoint HUD-2**: pantalla "Transmisión" en el panel -
      `BroadcastSettings` (fila única: `tournament_label`, `logo_choice`
      "tdf"/"torneo", `custom_logo_filename`), servida al overlay vía
      `/api/broadcast-settings`. Subir un logo custom lo copia a
      `overlay_app/public/branding/torneo-logo.<ext>` (requiere
      `npm run build` después, mismo criterio que los retratos). El
      logo "tdf" por defecto necesita que Seba agregue
      `overlay_app/public/branding/tdf-logo.webp` a mano (no existe
      todavía en el repo — no tengo el archivo real del club). 9 tests
      nuevos (servicio + endpoint + UI real con un archivo de logo
      sintético). De paso: `create_app()` ahora recibe el
      `session_factory` compartido en vez de abrir un engine nuevo por
      request, y se encontró y corrigió un bug real — un
      `QMessageBox.information()` bloqueante en el camino feliz de
      "Guardar" colgaba cualquier test offscreen sin error legible (ver
      `tasks/lessons.md`); se reemplazó por una `QLabel` de estado.
- [x] **Checkpoint HUD-3: rediseño visual completo del overlay.**
      `DraftOverlay.tsx` reescrito de cero como franja HUD inferior:
      nombre de cada jugador en su extremo, slots de baneo entre el
      nombre y el centro (el primer baneo de cada jugador ocupa el slot
      más cercano al centro, el resto se abre hacia afuera — implementado
      invirtiendo el orden de índices del lado izquierdo). Slot activo
      con degradado pulsante + cuenta regresiva real derivada de
      `turn_deadline_ms` (cliente, sin necesitar un tick de socket por
      segundo). Ícono de timeout (⏱) sobre cualquier baneo con
      `was_timeout=true`, marcador de "—" para turnos saltados
      (`character_id=null`). Panel central usa `BroadcastSettings`
      (logo + `tournament_label`, con fallback al nombre real del
      torneo si no está configurado) y el texto de estado del draft.
      Al llegar a `REVEAL`/`DONE`, el reveal final reemplaza la fila de
      slots de cada lado y aparece **en el extremo de cada jugador**
      (no al centro, corregido respecto a la Fase 3 original). Backend:
      `build_match_state_payload()` ahora incluye `tournament_name` y
      `bans_per_player`. 11 tests de Vitest cubriendo slots vacíos/
      llenos, skip, timeout, cuenta regresiva con timers falsos, reveal
      por lado, y el panel central con/sin `tournament_label`. Probado
      además contra el backend real: `index.html` + JS del build nuevo +
      `/api/roster` + `/api/broadcast-settings` servidos juntos.
      **Confirmado visualmente en la máquina de Seba** — encontró y se
      corrigieron 2 bugs reales que el sandbox no podía detectar sin
      navegador: (1) el nombre del jugador se mostraba duplicado (una
      vez como etiqueta afuera, otra vez adentro de `ResultCard`) —
      se sacó del `ResultCard`, el nombre vive una sola vez en
      `player-name-label`; (2) la franja no estaba anclada al fondo del
      viewport (`position: fixed` faltante), todo quedaba apretado
      arriba a la izquierda. Se reemplazó el layout flex por el patrón
      real de **tres cajas ancladas via `calc(50% ± offset)`**, adaptado
      de [RCVolus/lol-pick-ban-ui](https://github.com/RCVolus/lol-pick-ban-ui)
      (MIT License, usado en transmisiones reales de LoL) — mucho más
      robusto que un flex row que depende del ancho del contenedor.
- [x] **Checkpoint HUD-4: selección + "Bloquear" con preview grande y
      transición de elemento compartido.** El clic en un personaje del
      panel ya no banea directo — **selecciona** (resalta en magenta,
      emite `ban_candidate_preview` vía Socket.IO) y el nuevo botón
      **"Bloquear"** confirma el baneo real. Evita baneos accidentales,
      mismo patrón que el pick/ban de League of Legends. El overlay
      muestra el retrato grande del candidato al lado del jugador que
      está eligiendo, y usa el mismo `layoutId` de Framer Motion entre
      el preview grande y el slot chico — al confirmarse, el retrato
      "vuela" automáticamente de uno a otro (FLIP shared-element
      transition), donde se pone gris con el tajo ya existente.
      Selección efímera, nunca toca la base — se limpia sola cuando el
      turno cambia (timeout o baneo resuelto) o cuando llega cualquier
      `match_state_update` real. 3 tests de Vitest + 1 test end-to-end
      con backend y Socket.IO reales confirmando que seleccionar NO
      banea y que "Bloquear" sí lo hace.
- [x] **Checkpoint HUD-5: panel dramático de pantalla completa + colores
      personalizables.** `BroadcastSettings` suma `accent_color` y
      `panel_background_color` (validación laxa de color CSS —
      `#hex`/`rgba()`/`hsl()`/nombre), configurables desde "Transmisión"
      con `QColorDialog` (con canal alfa para el fondo). El overlay
      reestructurado: el preview de selección (checkpoint HUD-4) y el
      reveal final ahora comparten un mismo componente
      `DramaticCharacterPanel` — retrato recortado tipo busto
      (`object-position: center 15%`) que sangra hasta el borde de
      pantalla del lado correspondiente, entra deslizando desde ese
      mismo borde, con una barra de nombre en degradado usando el color
      de acento. Vive como hermano de la franja compacta (no anidado
      adentro), así la franja de slots sigue visible abajo mientras el
      panel dramático ocupa el resto de la altura. Mismo `layoutId` de
      Framer Motion que ya compartía el preview con el slot chico, ahora
      a la escala nueva. 16 tests de Vitest (subieron de 14: 2 nuevos de
      colores personalizados + reveal de ambos lados a la vez). Diseño
      acordado en el chat con dos mockups intermedios antes de programar
      (la primera escala quedó chica, la referencia real de LCK confirmó
      que debía ocupar casi toda la altura — normal, porque durante el
      baneo/reveal todavía no hay gameplay corriendo, no compite por
      espacio con el juego). Se evitó `color-mix()` en el CSS del brillo
      pulsante por compatibilidad con versiones de CEF más viejas.

- [x] **Checkpoint HUD-5.1: correcciones tras la primera prueba real en
      la máquina de Seba.** 4 problemas encontrados y resueltos:
      1. **Bug real de carrera**: seleccionar un personaje llamaba a
         `_refresh_state()` completo, que además de actualizar el botón
         **también reemitía `match_state_update`** — y en el overlay,
         cualquier `match_state_update` borra el preview del candidato
         (para limpiar restos viejos tras una acción real). El preview
         llegaba y medio segundo después se borraba solo. Mi test de
         Python original no lo detectó porque nunca ejercitó la lógica
         real del navegador (`App.tsx`), solo confirmó que el evento
         viajaba por el socket. Arreglado: `_on_character_selected()`
         ya no llama a `_refresh_state()`, solo actualiza el botón
         localmente y emite el preview — el `match_state_update` real
         solo sale al Bloquear/timeout/randomizar/completar. Test
         end-to-end nuevo verificando el conteo exacto de eventos por
         cada acción.
      2. **Nombre del jugador desalineado entre lados**: el boilerplate
         de Vite dejó `#root { text-align: center; width: 1126px; ... }`
         sin limpiar en `index.css`. Como `text-align` se hereda
         (aunque `position: fixed` no respete el layout del padre), el
         lado izquierdo heredaba "centrado" mientras el derecho lo
         pisaba a mano con `text-align: right` — por eso solo P2 se
         veía "bien". Se limpió `index.css` del boilerplate entero (ya
         no lo necesitábamos) en vez de parchar cada componente, más
         `text-align: left` explícito por las dudas.
      3. **Slots de baneo muy chicos**: reemplazado el truco de
         `calc(50% ± offset)` por un `grid-template-columns: 36% 20.8%
         36.2%` explícito, con la franja completa a `35.4vh` de alto —
         proporciones reales que Seba sacó de un HUD de torneo de LoL.
         Slots subieron de 70px fijos a `15vh` (escalan con la
         resolución del canvas de OBS).
      4. **Calidad de imagen mala en el panel dramático**: los retratos
         se habían optimizado a WebP ~500px para los slots chicos, pero
         el panel dramático los estira a ~44% del ancho de pantalla —
         se nota la compresión. `download_portraits.py` ahora genera
         **dos tamaños por personaje** desde la misma descarga: WebP
         chico (slots) + **PNG grande** (`portraits-large/`, hasta
         1200px, sin comprimir) para el panel dramático.
- [x] **Checkpoint HUD-5.2: calidad de imagen y panel central roto.**
      Confirmado con capturas reales (preview funcionando en ambos
      jugadores — el fix de la carrera del HUD-5.1 quedó validado). Dos
      bugs nuevos encontrados:
      1. **Calidad todavía insuficiente**: 1200px no alcanzaba porque
         los renders de Capcom suelen ser más anchos que altos (poses
         de acción), y el recorte tipo busto solo usa la franja
         vertical — subido a `LARGE_MAX_DIMENSION_PX = 2400`.
      2. **Panel central "flotando" mal, tapando slots**: tenía
         `height: 80%` como hijo de un grid con `align-items: end` —
         combinación ambigua (el item no se estira con `align-items:
         end`, así que el porcentaje no tenía contra qué resolverse de
         forma predecible). Cambiado a `align-self: stretch`, explícito
         y sin ambigüedad (ver `tasks/lessons.md`).
- [x] **Checkpoint HUD-5.3: rediseño del panel central (vidrio + VS
      grande).** Confirmado por captura real que la calidad de imagen y
      el panel central ya no flotan mal — quedaba una observación de
      diseño, no un bug: la caja gris opaca del centro se veía
      desconectada del resto (todo lo demás usa transparencias/
      degradados). Acordado en el chat con dos mockups antes de
      programar: (1) fondo tipo "vidrio esmerilado" (`backdrop-filter:
      blur` + gradiente semi-transparente en vez de color plano, borde
      fino con el color de acento, brillo sutil) reemplazando la caja
      opaca; (2) el logo/nombre del torneo bajan de tamaño y pasan a ser
      un detalle chico arriba — el elemento dominante ahora es un **"VS"
      grande** con glow del color de acento (más apropiado para un 1v1
      que un logo institucional chico, que además se veía ilegible a
      ese tamaño). Default de `panel_background_color` bajado de 0.85 a
      0.35 de opacidad para que el efecto vidrio se note. 1 test nuevo
      (17 en total) confirmando que el "VS" está siempre presente.

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
