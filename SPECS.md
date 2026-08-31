# SPECS.md — TDF Random Select

## 1. Contexto

Herramienta de escritorio para Windows, independiente de la web de
`tdf-edeportes`, para correr torneos de **selección random de personaje**
en Street Fighter 6 dentro de TDF e-deportes. La mecánica: antes de cada
match, ambos jugadores banean personajes de una grilla compartida (para
sacar los personajes fuertes conocidos de ambos jugadores del pool), y
luego a cada jugador se le asigna un personaje al azar entre lo que quedó
sin banear.

Se entrega compilada (`.exe`) al CEO (bazthyfreeman) para que la use en
vivo durante las transmisiones, con integración a OBS Studio para que el
draft aparezca en el stream con animación propia.

**No pertenece al repo de la web** (`tdf-edeportes`) — es una app de
escritorio distribuible con su propio ciclo de vida, sin dependencia de
Render/Vercel/Supabase para funcionar. Puede correr sin internet salvo por
la conexión local a OBS.

## 2. Referencia de arquitectura

El diseño sigue el patrón probado de
[TournamentStreamHelper](https://github.com/joaorb64/TournamentStreamHelper)
(MIT, no se reutiliza código directamente, solo la arquitectura como
referencia validada por la escena FGC):

- Panel de control nativo (PyQt6), no un webview envolviendo web.
- Backend Flask + flask-socketio embebido en el mismo proceso.
- Sitio del overlay (lo que ve el stream) como app React/Vite separada,
  compilada a estático y servida por ese mismo backend.
- El Browser Source de OBS es un proceso Chromium (CEF) aparte del
  proceso de la app — la única forma de comunicarse con él es por red
  (WebSocket a `localhost`), nunca vía IPC directo.

Diferencia respecto a TSH: TSH usa OBS de forma **pasiva** (el staff
agrega el Browser Source una vez y nunca más toca OBS, todo el update es
vía WebSocket dentro de la página). Este proyecto usa OBS de forma
**activa** además de eso, vía `obsws-python`, para cambiar de escena
automáticamente al iniciar/terminar el draft (ver §5).

## 3. Alcance

### Incluido (v1)
- Panel de control (PyQt6) para que el staff arme el draft: elegir
  Jugador A / Jugador B, cantidad de baneos (configurable por torneo),
  ejecutar el baneo alternado, disparar el random, ver el reveal.
- Overlay web (React) con la grilla de 31 personajes de SF6 (retratos
  oficiales de Capcom), animación de baneo y de reveal.
- Sección de carga manual de "personajes fuertes conocidos" por jugador
  (referencia visual en pantalla durante el baneo, no filtra la grilla).
- Integración con OBS: cambio automático a la escena de draft al iniciar
  el baneo, vuelta automática a la escena anterior al terminar el reveal,
  con botón de override manual.
- Persistencia local en SQLite (jugadores, torneos, matches, baneos,
  resultados) — sin dependencia de Supabase.
- Empaquetado a `.exe` para Windows (PyInstaller).

### Explícitamente fuera de alcance (v1)
- Cualquier dependencia de la infraestructura de `tdf-edeportes`
  (Render/Vercel/Supabase). Si más adelante se quiere importar el roster
  de jugadores o las estadísticas de `cfn_matches` desde ahí, es una
  decisión aparte y explícita, no algo que se asuma.
- Soporte multiplataforma (macOS/Linux) — el CEO usa Windows, no se
  invierte tiempo en portabilidad que nadie pidió.
- Bracket/torneo completo (esto es solo la herramienta de selección
  random por match, no un sistema de brackets).

## 4. Modelo de baneo (decisión tomada)

- **Pool compartido**: un baneo saca ese personaje de la grilla para
  ambos jugadores (no hay pools individuales por jugador).
- **Alternado 1x1**: banea A, banea B, banea A, ... hasta completar
  `bans_per_player × 2`.
- **Cantidad de baneos**: configurable por torneo (`tournaments.bans_per_player`),
  no un número fijo hardcodeado.
- **Random final**: sobre el pool restante (grilla menos baneados), cada
  jugador se sortea independientemente, **con reposición** — el mirror
  match (mismo personaje para ambos) está permitido explícitamente.
- **"Personajes fuertes" por jugador**: se carga a mano en una sección de
  la app (`character_tags`). Es **solo referencia visual** durante el
  baneo (ej. resaltar el personaje en la grilla), **no filtra ni
  restringe** qué se puede banear.

## 5. Integración OBS (decisión tomada)

Vía `obsws-python` contra el servidor OBS WebSocket nativo de OBS 28+
(protocolo v5). Responsabilidad centralizada en `backend/app/services/obs_service.py`.

Flujo:
1. Staff hace clic en "Iniciar Baneo" en el panel de control.
2. `obs_service` guarda el nombre de la escena actualmente activa
   (`GetCurrentProgramScene`).
3. `obs_service` cambia a la escena de draft configurada
   (`SetCurrentProgramScene`), que en OBS contiene el Browser Source
   apuntando al overlay local.
4. En paralelo, el backend emite el evento Socket.IO que arranca el
   estado `BANNING` en el overlay — la transición de escena de OBS y la
   animación interna del overlay son capas independientes (la primera es
   configuración propia de OBS, la segunda es Framer Motion en React).
5. Al terminar el estado `REVEAL`, `obs_service` vuelve automáticamente a
   la escena guardada en el paso 2.
6. El panel de control tiene un botón de override manual para volver
   antes (ej. el caster quiere quedarse comentando el reveal).

Configuración de conexión (host, puerto, password de OBS WebSocket,
nombre de la escena de draft) vive en una tabla `obs_settings` local, no
hardcodeada.

## 6. Modelo de datos (SQLite local)

```
players
  id                  INTEGER PK
  display_name        TEXT NOT NULL
  cfn_id              TEXT              -- opcional, solo referencia visual

character_tags                          -- "personajes fuertes" por jugador
  id                  INTEGER PK
  player_id           INTEGER FK -> players.id
  character_id        TEXT NOT NULL     -- id interno del roster SF6
  note                TEXT              -- opcional

tournaments
  id                  INTEGER PK
  name                TEXT NOT NULL
  bans_per_player      INTEGER NOT NULL DEFAULT 1

matches
  id                  INTEGER PK
  tournament_id        INTEGER FK -> tournaments.id
  player_a_id          INTEGER FK -> players.id
  player_b_id          INTEGER FK -> players.id
  status               TEXT NOT NULL     -- SETUP | BANNING | RANDOMIZING | REVEAL | DONE
  created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP

match_bans
  id                  INTEGER PK
  match_id             INTEGER FK -> matches.id
  character_id         TEXT NOT NULL
  banned_by_player_id  INTEGER FK -> players.id
  turn_order           INTEGER NOT NULL

match_results
  id                  INTEGER PK
  match_id             INTEGER FK -> matches.id
  player_id            INTEGER FK -> players.id
  assigned_character_id TEXT NOT NULL

obs_settings
  id                  INTEGER PK        -- fila única
  host                TEXT NOT NULL DEFAULT 'localhost'
  port                 INTEGER NOT NULL DEFAULT 4455
  password             TEXT
  draft_scene_name      TEXT
```

## 7. Arquitectura del walking skeleton (primer entregable)

Antes de construir lógica de negocio real, se valida que las cuatro
piezas de integración nuevas funcionan juntas, de punta a punta, con
datos reales (no mocks):

1. `main.py` abre una ventana PyQt6 con un botón "Ping" — valida que
   `qasync` comparte el loop de eventos entre Qt y asyncio sin choques.
2. Ese proceso levanta Flask-SocketIO embebido en un thread aparte.
3. El botón emite un evento Socket.IO real al backend.
4. El backend lo reenvía a un overlay mínimo (React+Vite compilado a
   estático, servido por el mismo Flask) que solo muestra el texto que
   le llega — valida que el build de Vite se sirve bien y que
   `socket.io-client` conecta de verdad.
5. Un botón aparte "Test OBS" llama a `obsws-python`, lista las escenas
   reales del OBS del staff y hace un `SetCurrentProgramScene` de prueba
   contra una instancia real — valida la conexión real, no mockeada.

Solo después de que este esqueleto corre de punta a punta se construye
encima: modelo de datos → lógica del draft → UI real del panel → UI real
del overlay con Framer Motion → automatización completa de OBS →
empaquetado final con PyInstaller. Ver `ROADMAP.md`.

## 8. Empaquetado

PyInstaller, `--onefile` para Windows. El build de `overlay_app` se
compila una vez (`npm run build`) y sus estáticos se empaquetan dentro
del `.exe` (`--add-data`), no se sirven desde un directorio externo — el
CEO recibe un solo archivo ejecutable.

Pendiente de definir cuando se llegue a esa etapa: firma de código (para
evitar el warning de "editor desconocido" de Windows SmartScreen) — no
bloqueante para v1, se evalúa si el club tiene certificado o se vive con
el warning.
