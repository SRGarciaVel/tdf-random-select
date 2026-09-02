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
- [x] **Checkpoint HUD-5.4: pulido final tras confirmación visual real
      del checkpoint anterior.** 3 ajustes:
      1. Slots de baneo agrandados (`--hud-ban-slot-size` de 15vh a
         21vh) — se veían chicos al lado del panel central alto.
      2. Contenido del panel central redistribuido: pasó de
         `justify-content: center` (todo apretado al medio, mucho
         espacio vacío arriba/abajo) a `justify-content: space-between`
         con 3 grupos (marca arriba, VS al medio — ahora más grande,
         2.1rem → 2.8rem —, estado abajo), usando todo el alto
         disponible del panel.
      3. La barra de nombre del panel dramático pasó del degradado
         magenta-a-transparente a una placa blanca sólida con texto
         negro, ajustada al ancho del texto (no estirada a todo el
         panel — un blanco sólido en toda esa franja se veía demasiado
         agresivo sobre el retrato).
- [x] **Checkpoint HUD-6: mazo de cartas en vez de fila de slots.**
      Confirmado por captura real que HUD-5.4 mejoró las cosas, pero
      surgió una tensión matemática real: pedir que los slots midan lo
      mismo de alto que el panel central (`35.4vh`) y que entren varios
      lado a lado en una columna de 36% de ancho no es compatible (3
      slots de ese alto en cuadrado no entran ni cerca). Se resolvió
      conversando la geometría antes de tocar código: en vez de una fila
      de cuadrados, los baneos ahora se muestran como un **mazo de
      cartas apiladas** — la carta del primer baneo (más cercana al
      centro) va al frente, a la altura completa del panel central; las
      siguientes se asoman detrás, corridas hacia el nombre del jugador,
      un poco más chicas (profundidad de mazo real). Al arrancar el
      baneo (`SETUP → BANNING`), el mazo completo "nace" del panel
      central con una animación de entrada — antes de eso no se muestra
      nada (ni la franja vieja ni el mazo), para que el reparto sea un
      gesto real y no algo que ya estaba ahí. Se evaluó y **se descartó
      explícitamente** que cada baneo individual saliera volando del
      centro (competiría con la transición de `layoutId` que ya usa el
      preview grande para volar a su carta al confirmar — dos vuelos
      simultáneos para el mismo evento se iban a pisar). De paso,
      arreglado el corte de los nombres de jugador contra el borde de
      pantalla (`overflow: hidden` + falta de padding en `.player-side`).
      19 tests (subieron de 17): 2 nuevos confirmando que el mazo no
      aparece en `SETUP` y que la carta del primer baneo ancla contra el
      borde más cercano al centro.
- [x] **Checkpoint HUD-7: fila visible para baneados + placas diagonales
      TDF.** Confirmado que HUD-6 arregló el ancho, pero las cartas
      baneadas quedaban casi escondidas dentro del mazo (solo se veía un
      sliver de las de atrás) — el problema que resolvía el mazo
      (espacio) generó uno nuevo (visibilidad). Solución acordada:
      separar "cartas por usar" de "cartas ya usadas". El mazo compacto
      (`ban-empty-stack`) ahora solo contiene los baneos *pendientes*
      (apagados, no importa que no se lean bien, son placeholders); cada
      baneo confirmado se saca de ahí y pasa a una **fila visible**
      (`ban-row`) que crece desde el centro hacia afuera en el orden en
      que se banearon — ahí sí se ve cada personaje baneado con
      claridad. De paso, el nombre del jugador se movió arriba de las
      cartas (antes al costado) usando una **placa con corte diagonal**
      (`clip-path`) — mismo lenguaje visual del `hud-frame` de
      `tdf-edeportes` (identidad TDF, no un estilo suelto). El mismo
      componente `DiagonalPlate` se reutiliza en el panel dramático: el
      nombre del personaje (grande) y el nombre del jugador (chico)
      apilados, ambos con el corte diagonal — antes el panel dramático
      solo mostraba el nombre del personaje en una barra sin ese
      lenguaje. 21 tests (subieron de 19): confirmando que las cartas
      baneadas quedan en la fila visible (no escondidas en el mazo), y
      que el panel dramático muestra personaje + jugador apilados.
- [x] **Checkpoint HUD-7.1: nombre mal alineado + robustez de altura +
      tamaños.** Confirmado con captura real que el "VS" y la 3ª carta
      no se veían. Diagnóstico: la captura se sacó en una pestaña normal
      del navegador (con barra de direcciones/pestañas, altura real
      menor a 1080px), y varios márgenes internos estaban en píxeles
      fijos en vez de proporcionales — en una ventana más baja que
      1080p, esos píxeles fijos "comen" proporcionalmente más del
      presupuesto de `35.4vh` y terminan empujando contenido fuera de
      la pantalla visible. Convertidos los paddings críticos de
      `.hud-bottom-bar`, `.player-side` y `.center-panel` a `vh`/
      `clamp()`, y el tamaño del "VS" a `clamp(1.4rem, 7vh, 2.8rem)` —
      se achica antes de desbordar, nunca desaparece. Esto debería
      importar menos en OBS real (el Browser Source se configura a una
      resolución exacta, sin chrome de navegador de por medio), pero
      igual vale la pena no depender de que la ventana sea
      exactamente 1080px. Bug real aparte: el nombre del jugador de la
      franja compacta heredaba el mismo `align-items` que el mazo de
      cartas y terminaba pegado al borde interior (junto al VS) en vez
      del borde exterior real de la pantalla, viéndose como un nombre
      redundante metido en el medio — arreglado con `align-self`
      explícito en la placa. Tamaños subidos a pedido de Seba: nombre
      del jugador +40%, nombre del torneo +30%.
- [x] **Checkpoint HUD-7.2: bug real de grid encontrado (confirmado en
      OBS real, no era la ventana del navegador).** HUD-7.1 asumió que
      el problema era la altura de la pestaña del navegador - Seba lo
      probó directo en el Browser Source de OBS y seguía exactamente
      igual, lo cual descartó esa hipótesis. Diagnóstico correcto:
      `.hud-bottom-bar` es un `display:grid` **sin `grid-template-rows`
      explícito** - sin eso, la fila implícita del grid CRECE para
      acomodar el contenido más alto de cualquier columna (el panel
      central, con el VS y el pie de estado, era más alto que el
      presupuesto de `35.4vh`). Como el contenedor está anclado al
      fondo de un lienzo de altura fija (`position:fixed; inset:0`),
      lo que "crece" de más no se corta con un borde visible - termina
      literalmente por debajo del borde inferior del lienzo, sin más
      canvas donde dibujarse. Eso explica los tres síntomas a la vez
      (VS invisible, pie de estado invisible, 3ª carta de baneo
      invisible) con una sola causa. Arreglado con
      `grid-template-rows: 100%` explícito, más `overflow: hidden`
      como red de seguridad en `.center-panel` y `.player-side` por si
      algo igual no entra (mejor que se recorte a que desaparezca sin
      explicación). Aparte, el nombre "duplicado" que seguía viéndose
      no era un bug de posición sino de diseño: cuando el panel
      dramático ya muestra el nombre del jugador (apilado bajo el
      personaje), la franja compacta mostraba el mismo nombre de nuevo
      — ahora se oculta la placa propia de la franja compacta cuando el
      panel dramático de ese lado ya está mostrando el nombre. 22 tests
      (subieron de 21): confirmando que el nombre no se duplica cuando
      el panel dramático está activo.
- [x] **Checkpoint HUD-7.3: mazo de baneos centrado respecto al panel
      central.** Confirmado con captura real que HUD-7.2 arregló los
      tres síntomas (VS, pie de estado, 3ª carta ya visibles). Quedaba
      un detalle de pulido: el mazo de cartas no quedaba a la misma
      altura visual que el panel central. Causa: el mazo usaba
      `flex: 1` ("ocupá lo que sobre" después de la placa de nombre),
      mientras que el panel central distribuye su contenido con
      `justify-content: space-between` en una proporción fija — como la
      placa de nombre es más alta que el renglón de marca del panel
      central, el mazo terminaba con menos aire disponible y no
      quedaba alineado. Arreglado: el mazo ahora usa una proporción
      fija del alto disponible (`height: 82%`, no `flex:1`), y
      `.player-side` centra el grupo completo (nombre + mazo)
      verticalmente con `justify-content: center` — mismo criterio de
      "proporción fija en vez de espacio sobrante" que ya usa el panel
      central.
- [x] **Checkpoint HUD-7.4: columnas del grid no sumaban 100% (bug real,
      no de detalle).** Seba dibujó líneas de referencia sobre el
      centro real del lienzo en una captura y confirmó que el "VS" NO
      estaba centrado de verdad, corrido hacia la izquierda — y que la
      placa de CHUBI (lado derecho) no llegaba hasta el borde real de
      la pantalla. Causa encontrada: `grid-template-columns: 36% 20.8%
      36.2%` — esos números (medidos a ojo por Seba con ayuda de
      ChatGPT sobre una captura de referencia de LCK) suman **93%, no
      100%**. Un grid no reparte solo el porcentaje que falta; el 7%
      sobrante queda vacío a la derecha, corriendo las tres columnas
      completas (VS incluido) hacia la izquierda. Arreglado
      cambiando de `%` a `fr` (`36fr 20.8fr 36.2fr`) - las unidades
      `fr` reparten el 100% del ancho disponible manteniendo la misma
      proporción relativa entre columnas, sin importar si los números
      originales suman justo 100 o no. Esto también explica por qué
      HUD-7.3 (centrado del mazo) no alcanzaba: el mazo podía estar
      bien centrado *dentro de su columna*, pero la columna entera
      estaba mal ubicada en la pantalla.
- [x] **Checkpoint HUD-8: cartas de baneo con marco tipo paralelogramo,
      mismo lenguaje visual que las placas de nombre.** A pedido de
      Seba: las cartas de baneo (tanto las pendientes/compactas como la
      fila de ya baneadas) pasan de rectángulos con borde a un marco
      blanco con `clip-path` de paralelogramo (dos cortes diagonales
      paralelos entre sí, mismo lenguaje visual que las placas de
      nombre de HUD-7). Encajan entre sí sin espacio real: mismo ángulo
      de corte para todas (`--ban-card-skew`), margen negativo exacto
      al ángulo para que el corte de una carta coincida con el de la
      siguiente, y un `border-right` que el propio `clip-path` recorta
      en diagonal, quedando como la costura gris entre cartas (gris, no
      negro, para no chocar contra el marco blanco - a pedido explícito
      de Seba). El retrato vive en un nuevo wrapper `.ban-card-inner`
      con su propio recorte diagonal, esta vez en **porcentaje** (no
      px) — mismo criterio para el retrato grande del panel dramático
      (`.dramatic-panel-img`, aplicado como prueba a pedido de Seba:
      "veamos qué tal queda", queda comentado en el CSS cómo revertirlo
      si no convence): al compartir la misma unidad relativa entre
      ambos, la transición de `layoutId` (el vuelo del preview grande
      hacia su carta al confirmar el baneo) no "salta" de forma al
      aterrizar, aunque los tamaños absolutos sean muy distintos.
      Estado activo (turno actual) cambiado de `border-color` a
      `filter: drop-shadow()` — un `box-shadow` normal dibuja un halo
      rectangular que se saldría del paralelogramo, `drop-shadow` sigue
      la forma real de los píxeles visibles. Explícitamente fuera de
      alcance de este checkpoint (a pedido de Seba, se trabaja después):
      el efecto de "refresco" al banear (degradé de arriba hacia abajo)
      y el panel de estadísticas por CFN con toggle manual del staff.
- [x] **Checkpoint HUD-9: figura conectada de extremo a extremo + línea
      con estela recorriendo el contorno completo.** Tres piezas:
      1. Margen blanco de las cartas achicado (`5% 14%` → `2.5% 8%`,
         se ve más el retrato).
      2. Panel central rediseñado con el **mismo `clip-path` exacto**
         que las cartas (no uno parecido — tiene que ser idéntico para
         que las diagonales coincidan), ensanchado con
         `margin-inline: calc(var(--ban-card-skew) * -1)` para que sus
         bordes se alineen con la carta pegada de cada lado. Sin
         padding en el costado de `.player-side` que mira al centro,
         para que no quede espacio real entre cartas y panel. Cartas al
         74.8% de alto (85% de 88%, la proporción exacta pedida por
         Seba: "las cartas deben ser un 15% más chicas que el
         paralelepípedo central").
      3. **Línea con estela recorriendo el contorno completo (360°)**
         de la figura conectada (mazo izquierdo + panel central + mazo
         derecho), en bucle constante. Implementada con SVG, **midiendo
         posiciones reales del DOM** (`getBoundingClientRect` +
         `ResizeObserver`) en vez de calcular la geometría a mano — las
         cartas y el panel central tienen alturas distintas (85%/88%),
         y confiar en matemática pura sin ver el render real era
         demasiado riesgo de que no coincidiera. `pathLength={1}` en el
         `<path>` normaliza el largo real a 0-1, así el
         `stroke-dasharray`/`dashoffset` animado no depende de medir el
         largo exacto del trazo (que cambia con cada baneo confirmado).
         Color de la línea = `var(--hud-accent-color)`, ya heredado y
         configurable desde "Transmisión" (sin prop nueva). Cuando una
         carta se acaba de banear, un pulso de brillo de 0.9s la
         resalta — aproximación razonable a "la línea la abraza al
         pasar" sin la complejidad de desviar literalmente el trazo
         principal en vivo (que competiría además con el vuelo de
         `layoutId` que ya existe para ese mismo evento). 5 tests
         nuevos probando de verdad la lógica de construcción del
         contorno (`buildPerimeterPath`, exportada para poder probarla
         sin necesitar layout real de navegador, que jsdom no calcula) -
         27 tests en total.
- [x] **Checkpoint HUD-10: efecto de refresco al banear + estadísticas
      de CFN, con toggle manual del staff.** Le da uso real al CFN ID
      que ya se cargaba al inscribir jugadores (hasta ahora sin uso en
      el flujo del draft). Cruza dos proyectos:
      1. **`tdf-edeportes` (otro repo)**: dato nuevo que no existía en
         ningún lado — win rate TOTAL por personaje (histórico completo,
         no una ventana de días como `cfn_matches`), de la pestaña
         `/play` → sub-pestaña "Win Rate" → filtro "Total" de Buckler's
         Boot Camp. Tabla nueva `cfn_character_stats`, scraper nuevo
         `get_character_win_rates()`, endpoint público
         `GET /cfn/players/{cfn_id}/character-stats/{character_name}`
         (case-insensitive, `ever_played: false` en vez de 404 para
         "nunca lo jugó"). Selectores **confirmados contra HTML real**
         que Seba subió (no a ciegas): la sub-pestaña se llama "Win
         Rate", no "Characters" como se había supuesto, y viene
         seleccionada por default; el filtro "Total" es un `<select>`
         nativo, no un botón (`select_option()`, no `click()` — el
         primer intento tiró justo ese error real en la corrida de
         Seba). Corrida real: 288 filas de 9 jugadores, 0 errores.
      2. **`tdf-random-select` (este proyecto)**: `character_stats_service.py`
         nuevo consume ese endpoint (nunca escribe en `tdf-edeportes`,
         solo lee). Precarga automática cada 10 min desde `main.py` en
         background (Render duerme la capa gratis a los 15 min sin
         tráfico — a pedido de Seba: "que cuando se necesite desplegar
         la información ya estén despiertas"). Botón "Mostrar
         estadísticas" en `BanningScreen`, habilitado solo con al
         menos un baneo real confirmado, consulta en un thread aparte
         (nunca traba el panel — verificado con un test que haría
         timeout si se colgara), y le muestra el resultado al staff en
         el panel además del overlay (a pedido de Seba: "por si quiere
         mencionarla en stream"). Siempre apunta al **último baneo
         confirmado** (más simple que dejar elegir carta puntual, según
         lo acordado). Efecto de refresco: degradé que tapa la carta de
         **izquierda a derecha** (ajustado durante la conversación —
         la primera mención había sido "arriba hacia abajo", la
         referencia final del HUD real de LoL confirmó izquierda a
         derecha), mostrando nombre del personaje + winrate (o "Nunca
         jugado").
      3. **Bug real encontrado y corregido**: mandar `payload=None`
         para "ocultar" se perdía en el viaje por el socket
         (python-socketio no lo entrega de forma confiable al cliente
         del otro lado). Contrato cambiado a un dict siempre presente
         con `visible: bool` explícito — confirmado con un test E2E
         real (backend levantado, socket real, no mockeado) mostrando
         Y ocultando.
      31 tests en el overlay (4 nuevos), 51 en el backend de
      tdf-random-select (6 nuevos del servicio de estadísticas).
- [x] **Checkpoint HUD-10.1: pulido tras la primera prueba real con
      datos reales de Supabase.** Funcionó de punta a punta (Seba lo
      confirmó con AckermanFG/Nocturne real), quedaban ajustes visuales
      finos comparando contra la referencia real de LoL: fondo blanco
      sólido en vez del degradé morado-transparente (mismo lenguaje
      visual que el resto de las cartas), nombre del personaje en
      mayúsculas y con `overflow: hidden` + `text-overflow: ellipsis`
      para que nunca se salga del ancho de la carta, "WIN%" como
      etiqueta chica separada arriba del número grande (antes era un
      solo texto tipo "61.0%" sin la etiqueta). De paso, el efecto
      ahora también anima al revés al ocultar (`AnimatePresence` +
      `exit`) en vez de desaparecer de golpe - antes solo animaba al
      aparecer.
      2 bugs reales encontrados y corregidos en `tdf-edeportes` durante
      la primera carga real de datos:
      1. La primera corrida se hizo contra la base **local** de Docker
         en vez de Supabase (mismo error de "local vs Supabase" que ya
         había pasado con las migraciones) - por eso todo salía "nunca
         jugado" pese a que el scrape había funcionado bien.
      2. Al cargar contra Supabase por primera vez (tabla vacía, sin
         filas previas), el scraper devolvió "RANDOM" duplicado para un
         jugador - como no había fila previa que `.first()` pudiera
         encontrar, SQLAlchemy agrupó todos los inserts pendientes en
         un solo INSERT masivo al hacer commit, y ninguna de las dos
         filas "RANDOM" se detectó como duplicada hasta que Postgres
         tiró el error de la constraint única. Arreglado deduplicando
         por `(cfn_id, character_name)` en Python antes de tocar la
         base (se queda con la última aparición) - verificado
         reproduciendo el escenario exacto contra Postgres real.
         Corrida real final: 495 filas de 512 combinaciones
         jugador-personaje, 0 errores.
- [x] **Checkpoint HUD-10.2: textos agrandados en general.** A pedido
      de Seba tras ver una captura del HUD completo compuesto en OBS:
      "TDF RANDOM TOURNAMENT" (`.center-label`), "VS" (`.center-vs`),
      el estado ("Reveal"/"Randomizando...", `.center-status`), y todo
      el contenido de la carta de estadísticas (nombre del personaje,
      "WIN%", el número) se veían chicos comparados con el resto del
      HUD (las cartas grandes, el panel central). Subidos entre 20% y
      35% cada uno.

## Fase 4 — Automatización completa de OBS

- [x] Pantalla de configuración de OBS en el panel (`ObsSettingsScreen`,
      pestaña "OBS"): reemplaza las env vars `OBS_HOST`/`OBS_PORT`/
      `OBS_PASSWORD` del walking skeleton por la tabla `obs_settings`
      real (host, puerto, password, nombre de la escena de draft) -
      `DiagnosticsScreen` seguía usando las env vars directo, ahora la
      config real vive en la base. Botón "Probar conexión" que además
      completa un combo editable con las escenas reales de OBS si está
      prendido (o se puede tipear a mano si todavía no lo está).
- [x] Botón "Iniciar Baneo" dispara `obs_service.switch_to_draft_scene()`
      además del evento de Socket.IO hacia el overlay que ya existía
      (Fase 3) - si no hay escena de baneo configurada, no intenta
      conectar a OBS en absoluto (no es un error, simplemente no está
      en uso esa parte).
- [x] `_switch_to_draft_scene()` guarda la escena activa antes de
      cambiar (via `ObsService.switch_to_draft_scene`, que ya guardaba
      la escena previa internamente desde el walking skeleton).
- [x] Vuelta automática a la escena guardada al completar el reveal
      (`_restore_obs_scene()`, enganchado en "Completar reveal").
- [x] Manejo de error explícito si OBS no está corriendo o la conexión
      falla: se loguea en un label del panel (`_obs_status_label`), el
      draft sigue funcionando exactamente igual sin bloquearse (modo
      degradado, ver `CODESTYLE.md`) - verificado con un test real
      simulando `obsws_python.ReqClient` caído, confirmando que el
      match sigue avanzando a `BANNING` igual.
      7 tests nuevos del servicio (`obs_settings_service`, contra
      SQLite real) - 58 en total en el backend.

## Fase 4.5 — Reforma de UI del panel de control

Con el HUD y la automatización de OBS ya cerrados, Seba pidió una pasada
de diseño sobre el panel de control en sí (PyQt6) - hoy usa el estilo
gris genérico de Qt sin ningún tema propio. Acordado en el chat antes de
programar: tema oscuro con identidad de TDF en vez de perseguir el
Fluent Design nativo de Windows 11 (que requeriría una librería de
terceros) - mismo criterio que usan apps profesionales como Discord o
VS Code. Checkpoints en orden (cada pantalla se hace por separado):

- [x] **Checkpoint UI-1: tema oscuro global.** `control_panel/theme.py`
      nuevo con la hoja de estilo QSS completa (paleta morado/magenta,
      misma familia que el color de acento por defecto del HUD, pero
      fija - el tema del panel es una decisión del staff, no algo
      atado a lo que el CEO configure en Transmisión para el público).
      Cubre botones, pestañas, campos de texto, tablas, checkboxes,
      scrollbars finos, menús contextuales y tooltips. Fuente Segoe UI
      (la tipografía nativa de Windows) con fallback automático de Qt
      si no está instalada. `mark_as_primary_action()` marca el botón
      principal de cada pantalla (Agregar jugador, Crear match, Iniciar
      baneo, Bloquear, Completar reveal, Guardar) para que se destaque
      con el color de acento - máximo un botón así por pantalla,
      mismo criterio de "una sola acción principal" que se usó también
      en el HUD. Verificado con capturas reales generadas en el propio
      sandbox (`window.grab()` en modo offscreen) - no solo compilación,
      se vio el resultado real antes de entregarlo. 58 tests de fondo
      siguen pasando igual, confirmando que el tema no rompió ninguna
      interacción.
- [x] **Checkpoint UI-2: pantalla Jugadores.** Columna ID sacada (no le
      servía a nadie verla) - el id del jugador ahora viaja escondido en
      `Qt.ItemDataRole.UserRole` del item de la columna Nombre, para que
      las acciones (renombrar, eliminar) sigan sabiendo a quién
      corresponde cada fila sin mostrarlo. Clic derecho con Renombrar,
      Editar CFN ID, Copiar nombre, Copiar CFN ID y Eliminar (con
      confirmación) - `update_player()` nuevo en `player_service.py`
      para el rename/edición (antes solo existía crear/borrar). Dos
      columnas nuevas con datos reales de tdf-edeportes: Rango/MR y
      Personaje actual, vía `player_profile_service.py`
      (`GET /cfn/players/{cfn_id}`, mismo tracker que ya usa HUD-10) -
      se consultan en threads de fondo por jugador (nunca traba la
      pantalla mientras cargan, verificado con un test que haría
      timeout si se colgara), con "Sin datos" si el jugador no tiene
      CFN ID o la consulta falla (modo degradado, no rompe nada si
      tdf-edeportes está caído). Columnas con `ResizeToContents` para
      que el texto no quede cortado. Verificado con capturas reales
      (`window.grab()`), no solo tests. 15 tests nuevos (6 de
      `update_player`, 4 de `player_profile_service`, 5 de la UI real
      con `fetch_player_profile` mockeado) - 68 en total.
- [x] **Checkpoint UI-3: pantalla Setup.** Botón "Eliminar torneo" junto
      al selector (deshabilitado cuando está seleccionado "crear
      nuevo"), con confirmación que muestra cuántas partidas se van a
      borrar junto con el torneo. `Tournament.matches` no tenía
      `cascade="all, delete-orphan"` (aunque `Match.bans`/`Match.results`
      sí) - sin eso, borrar un torneo con partidas hubiera reventado con
      un error de integridad referencial. Agregado el cascade completo
      y `delete_tournament()` nuevo en `tournament_service.py`,
      verificado con un test real que arma un match con un baneo de
      verdad (`DraftService`) y confirma que `MatchBan` también
      desaparece al borrar el torneo, no solo el torneo mismo. Lista de
      "personajes fuertes" con `setMaximumHeight(140)` - antes crecía
      sin límite y había que agrandar toda la ventana para ver una
      lista larga completa, ahora usa su propia barra de scroll interna
      (`QListWidget` ya la trae, solo hacía falta ponerle un techo).
      6 tests nuevos del servicio + 5 de la UI real - 71 en total.
      **Tres rondas de fix tras las pruebas reales**: (1) el scroll que
      faltaba no era el de la lista de ya agregados (ese ya tenía el
      límite de alto) sino el del propio desplegable del combo para
      *agregar* un personaje nuevo. (2) `setMaxVisibleItems()` solo no
      alcanzó - no era un problema de WSL2 (la sospecha inicial de
      Seba) sino del QSS propio (checkpoint UI-1) interfiriendo con el
      cálculo automático de Qt. (3) fijar `view().setMaximumHeight()`
      a mano tampoco alcanzó del todo - dejaba un hueco en blanco
      arriba de la lista, porque con QSS propio Qt seguía usando el
      modo de popup "nativo" por dentro (que ignora esa altura),
      dejando el marco del popup con el tamaño original y solo la
      vista interna recortada. La causa raíz real:
      `combobox-popup: 0` en el QSS del propio `QComboBox` (una
      propiedad de Qt hecha justo para esto) fuerza el modo de popup
      "clásico", el único que respeta `setMaxVisibleItems()`/
      `setMaximumHeight()` de forma confiable con estilos propios -
      verificado con una captura real del popup abierto de verdad
      (`showPopup()` + `grab()`), no solo midiendo su altura.
- [x] **Checkpoint UI-4: pantalla Baneo (el más grande).**
      1. **Grilla estilo selección de campeón de LoL**: `CharacterButton`
         reusa los mismos retratos chicos que ya tiene el overlay
         (`overlay_app/public/portraits/{id}.webp`), confirmado con un
         test real que `QPixmap` carga `.webp` sin problema (no hace
         falta un tercer set de imágenes). Marcadores por prefijo de
         texto en vez de tachado real (Qt no soporta `text-decoration`
         de forma confiable vía QSS): ★ para personaje fuerte del
         rival, ✕ para ya baneado. Estado seleccionado vía
         `setProperty("state", "selected")` + regla QSS (mismo patrón
         que `mark_as_primary_action`), no `setStyleSheet` directo.
         Barra de búsqueda que esconde/muestra en vivo (`setVisible`).
         **Fix real tras la primera prueba de Seba**: la primera versión
         usaba un solo `QToolButton` con `ToolButtonTextUnderIcon`
         (imagen y nombre juntos adentro del mismo recuadro bordeado) -
         el pixmap nativo del retrato (mucho más grande que el ícono
         pedido) empujaba el tamaño real del botón más allá del límite
         fijado, superponiendo filas enteras de la grilla. Rehecho como
         widget compuesto (`QWidget` con un `QToolButton` chico de
         tamaño fijo en los dos ejes de la política de tamaño, no solo
         `setFixedSize`, para que Qt no pueda ignorarlo - solo con la
         cara y su borde, más un `QLabel` aparte y sin borde debajo con
         el nombre), a pedido explícito de Seba: "el nombre debe ir
         debajo del cuadro, no dentro del cuadro". Verificado con una
         captura real (`window.grab()`) confirmando que ya no hay
         superposición entre filas.
      2. **Panel de CFN de ambos jugadores**: rango/MR/personaje actual,
         reusando `player_profile_service.py` (checkpoint UI-2, mismo
         tracker que HUD-10) - consultado en threads de fondo por
         jugador. Se decidió explícitamente NO construir un endpoint
         nuevo de "top de campeones" en tdf-edeportes (conversación con
         Seba: el picante del baneo se decide charlando con el rival en
         vivo el día del torneo, no hace falta que la app lo sugiera) -
         ahorra una vuelta completa a otro repo.
      3. **Eliminar partidas**: `delete_match()` individual y
         `delete_all_matches()` masivo en `draft_service.py` (con
         confirmación y conteo real antes de borrar) - `Match.bans`/
         `Match.results` ya cascadeaban solos (igual que se confirmó
         para torneos en UI-3), un test real arma un match con un baneo
         de verdad y confirma que `MatchBan` también desaparece.
      13 tests nuevos del servicio (`delete_match`/`delete_all_matches`)
      + 6 de la UI real (panel de CFN, estrella, filtro de búsqueda,
      marcador de baneado, eliminar individual, limpieza masiva) - 75
      en total. Verificado también con una captura real de la pantalla
      completa (`window.grab()`), no solo tests.
- [ ] **Checkpoint UI-5 (pendiente): pantalla Transmisión, repensada.**
      Hoy está subutilizada (solo nombre/logo/colores, poco uso real).
      Direcciones acordadas para explorar, las 4 juntas:
      1. Vista previa en vivo del HUD dentro del panel (mini-render que
         se actualiza mientras se tocan los campos).
      2. Presets guardados (combos completos con nombre, para tener
         listo un preset armado con anticipación).
      3. Espacio para logos de auspiciadores/redes.
      4. Un checklist "antes de salir al aire" centralizando cosas que
         hoy viven sueltas en otras pestañas (segundos del timer de
         baneo, comportamiento al agotarse, etc.).

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
