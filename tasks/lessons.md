# Lecciones aprendidas — TDF Random Select

## Walking skeleton (armado inicial)

- **Flask no mapea `/` a `index.html` solo por configurar `static_folder`.**
  Hay que exponer una ruta explícita (`app.send_static_file("index.html")`)
  o el build de Vite nunca se sirve en la raíz, solo bajo rutas de
  archivo puntuales. Sin esto, el Browser Source de OBS apuntando a
  `http://localhost:5001/` da 404.
- **`obsws-python` no expone una excepción propia estable** para "no se
  pudo conectar" — lo que llega es la excepción cruda de la librería de
  websockets de más abajo (`ConnectionRefusedError`, etc.). `ObsService`
  la captura genérico (`except Exception`) y la re-lanza como
  `ObsConnectionError` propia, para que el resto de la app (panel,
  backend) nunca dependa del tipo de excepción interno de una librería
  de terceros.
- **Al probar subprocesos con Popen para validar el backend real, usar
  siempre `sys.executable`** (o la ruta explícita del intérprete del
  venv), nunca `"python3"` a secas — si no, el subproceso corre con el
  Python del sistema, sin las dependencias instaladas, y falla con
  `ConnectionRefusedError` que parece un problema del servidor pero en
  realidad es que el proceso nunca llegó a levantar.
- **PyQt6 sí se puede instanciar sin display real** con
  `QT_QPA_PLATFORM=offscreen` — útil para validar en CI/sandbox que los
  widgets se construyen sin errores, aunque la validación visual real
  (que se vea bien, que el layout no se rompa) solo se puede hacer en
  una máquina con display real (la de Seba en Windows).

## Validación en la máquina real de Seba (WSL2 + WSLg + OBS en Windows)

- **`wait_timeout` de `python-socketio` Client(): default 1s, insuficiente.**
  Con la ventana PyQt6 renderizando por software (WSLg sin GPU
  passthrough, warnings de `libEGL`/`ZINK` en el log), el handshake del
  namespace de Socket.IO no llegaba a tiempo dentro del segundo por
  defecto y tiraba `One or more namespaces failed to connect`. Subir a
  `wait_timeout=10` en `_ensure_socket_connected` lo resolvió. No se
  logró reproducir la falla exacta en el sandbox (1 solo core, sin la
  misma carga de renderizado), pero el fix es correcto de todas formas
  dado lo ajustado del default.
- **WSL2 en modo NAT no comparte `localhost` con Windows.** `nameserver`
  en `/etc/resolv.conf` apuntando a `10.255.255.254` es la señal de modo
  NAT (no mirrored). Para que la app (corriendo en WSL) llegue al OBS
  real (corriendo en Windows), hay que usar la IP del gateway visible
  desde WSL (`ip route show default | awk '{print $3}'`), nunca
  `localhost`. Se agregó soporte a `OBS_HOST`/`OBS_PORT`/`OBS_PASSWORD`
  por variable de entorno en `MainWindow` para poder probar esto sin
  esperar a la pantalla de configuración real de la Fase 2.
- **Confirmación importante para el diseño real:** este problema de
  `localhost` cruzado desaparece por completo una vez que la app corre
  nativa en Windows (que es como se le entrega al CEO) — ahí el backend,
  el panel y OBS están todos en la misma máquina de verdad. WSL2 sirvió
  para iterar rápido, pero no reemplaza una prueba final en Windows puro.
- **`obsws-python` tira `OBSSDKError: authentication enabled but no
  password provided`** cuando el WebSocket Server de OBS tiene password
  habilitado y no se la pasamos — mensaje de error claro, sin necesidad
  de investigar más.

## Fase 3 checkpoint A: estado final perdido al completar el reveal

- **El match que pasa a `DONE` desaparece de `list_open_matches()`** (por
  diseño, ya no hay nada pendiente que trabajar ahí) — pero eso significa
  que `_reload_matches()` limpia la seleccion del combo justo despues de
  `complete_reveal()`, y si se emite el estado al overlay recien en ese
  punto, el payload que le llega es `{"match_id": None}` en vez del
  estado `DONE` con los resultados. El test end-to-end (backend real +
  panel real + cliente Socket.IO simulando el overlay) lo detecto
  comparando la lista de estados recibidos contra los 5 esperados - "DONE"
  faltaba. Arreglo: emitir el payload final explicitamente ANTES de
  llamar a `_reload_matches()`, no depender del flujo normal de
  `_refresh_state()` para el ultimo estado de un match que esta a punto
  de salir de la lista.
- **Leccion general**: cualquier accion que haga que una entidad "salga
  de la vista" (deje de listarse, cambie de tab, etc.) es un punto donde
  el ultimo estado se puede perder si el evento de notificacion depende
  del mismo refresh que hace que la entidad desaparezca. Conviene emitir
  el estado final de forma explicita, separado del refresh de la UI.

## QMessageBox modal cuelga los tests offscreen

- **`QMessageBox.information()`/`.warning()`/`.critical()` son modales
  bloqueantes** (`.exec()` interno) - esperan un clic real. En
  `QT_QPA_PLATFORM=offscreen` no hay nadie para hacer ese clic, asi que
  el proceso se queda colgado para siempre (el comando del test hay que
  matarlo a mano, no falla con un error legible). Pasó con
  `BroadcastSettingsScreen`: tenía un `QMessageBox.information()` en el
  camino feliz de "Guardar" y el test offscreen se colgó sin ningún
  mensaje de error.
- **Regla para este proyecto**: usar una `QLabel` de estado (mismo
  patrón que `SetupScreen._result_label`) para confirmaciones de
  camino feliz, no un modal - se puede probar sin bloquear, y además es
  menos intrusivo para el staff durante un stream en vivo. Los
  `QMessageBox.warning()` en caminos de error se mantienen (son
  aceptables ahí, el staff necesita confirmar que vio el error), pero
  hay que recordar mockearlos o evitarlos si algún test offscreen llega
  a ejercitar esa ruta.

## Browser Source de OBS: cachea una carga fallida

- **Si agregas el Browser Source antes de que el backend esté arriba**
  (`python main.py` corriendo), el Chromium embebido de OBS (CEF) se
  queda con esa carga fallida en caché y no la reintenta solo, aunque el
  backend arranque después - la fuente se ve en negro/vacía
  indefinidamente. El botón "Actualizar la caché de la página actual"
  (en Propiedades) o "Actualizar" (en el panel de la fuente) fuerza el
  reintento y resuelve. Antes de sospechar de la config del Browser
  Source (URL, dimensiones, CSS), confirmar primero: (1) el backend está
  arriba, (2) la misma URL carga bien en un navegador normal de Windows,
  (3) recién ahí, si OBS sigue en blanco, refrescar su caché.

## Seleccionar un candidato borraba su propio preview (carrera)

- **Cualquier acción que reemita `match_state_update` limpia el preview
  del candidato en el overlay** (diseño intencional: limpiar restos
  viejos tras una acción real). El bug: `_on_character_selected()`
  llamaba a `_refresh_state()` completo para actualizar el resaltado del
  botón, y `_refresh_state()` **también** reemite `match_state_update`
  como efecto colateral. Resultado: el preview llegaba, y milisegundos
  después el propio acto de seleccionar lo borraba solo.
- **Por qué mi test de Python no lo agarró**: `test_ban_candidate_preview.py`
  solo verificaba que el evento `ban_candidate_preview` viajara por el
  socket real - nunca ejercitó la lógica de `App.tsx` que limpia el
  preview al recibir `match_state_update`. Un test E2E puede confirmar
  que "el mensaje llegó" sin confirmar que "el mensaje sobrevivió" si no
  simula el consumidor real completo. Lección: cuando dos sistemas se
  comunican por eventos y uno tiene reglas de "el evento X invalida el
  evento Y", los tests tienen que cubrir la INTERACCIÓN entre ambos
  tipos de evento, no cada uno por separado.
- **Regla para este proyecto**: las acciones que solo cambian estado
  local de UI (como seleccionar sin confirmar) no deben disparar
  `emit_match_state()` bajo ningún motivo - solo las acciones que
  representan un cambio real y persistido del draft (baneo confirmado,
  timeout resuelto, randomizar, completar) tienen permiso de reemitir el
  estado completo.

## `display:grid` sin `grid-template-rows` deja crecer la fila con el contenido

- `.hud-bottom-bar` tenía `height: 35.4vh` en el CONTENEDOR, pero nunca
  se le puso `grid-template-rows` explícito - un grid sin eso deja que
  la fila implícita se dimensione por el contenido más alto de
  cualquier columna, ignorando la altura declarada del contenedor. El
  panel central (VS + pie de estado) resultó más alto que el
  presupuesto real, la fila creció para acomodarlo, y como el
  contenedor está anclado al fondo de un lienzo de altura fija
  (`position:fixed; inset:0`), lo que "creció" de más no se corta con
  un borde visible - queda literalmente por debajo del borde inferior
  del lienzo, sin más canvas donde renderizarse. Tres síntomas
  aparentemente distintos (VS invisible, pie de estado invisible, 3ª
  carta de baneo invisible) tenían esta única causa.
- **Cómo se descartó la hipótesis equivocada primero**: al ver el
  problema por primera vez, la sospecha inicial fue "la ventana del
  navegador es más baja que 1080px" (ver la lección anterior sobre
  `vh` + píxeles fijos) - una hipótesis razonable pero incorrecta.
  Confirmarla o descartarla costó UN mensaje pidiendo que Seba probara
  directo en OBS (no en una pestaña de navegador) antes de tocar más
  CSS a ciegas - valió la pena, evitó seguir iterando sobre un
  diagnóstico equivocado.
- **Regla general**: cualquier `display:grid` con una altura de
  contenedor fija en la que el contenido de las columnas pueda variar,
  necesita `grid-template-rows` explícito (`100%`, `1fr`, etc.) - sin
  eso, el grid prioriza mostrar el contenido completo por sobre
  respetar la altura declarada, y en un contenedor `position:fixed`
  anclado al fondo de la pantalla, ese overflow es invisible en vez de
  visible, lo cual lo hace mucho más difícil de diagnosticar a simple
  vista que un overflow normal.

## Mezclar `vh` con píxeles fijos rompe en ventanas mas bajas que 1080p

- La franja del HUD mide su altura en `vh` (35.4vh, pensado para
  escalar con cualquier resolución), pero varios paddings/gaps internos
  quedaron en píxeles fijos (`padding-bottom: 18px`, etc.). En una
  ventana de altura real MENOR a 1080px (como una pestaña normal de
  navegador con barra de direcciones, en vez del canvas exacto de OBS),
  el presupuesto en `vh` se achica proporcionalmente pero los píxeles
  fijos no - terminan comiendo una porción cada vez mayor del espacio
  disponible, hasta que el contenido de más abajo (el "VS", la última
  carta de baneo) queda literalmente empujado fuera de la pantalla
  visible, sin overflow ni scroll que lo delate, solo "desaparece".
- **Arreglo**: los paddings/gaps que compiten por el mismo presupuesto
  de altura que ya está en `vh` pasan a `vh` también (o a `clamp()`
  cuando conviene poner un piso/techo), para que todo se achique en
  conjunto en vez de que una pieza fija rompa la proporción.
- **Ojo con el entorno de prueba real**: en el Browser Source de OBS
  esto importa menos (se configura a una resolución exacta, sin chrome
  de navegador de por medio), pero vale la pena no depender de que la
  ventana de prueba sea exactamente 1080px - Seba prueba en una pestaña
  normal de Brave antes de pasar a OBS, así que el HUD tiene que
  aguantar esa altura reducida también.

## `height: %` dentro de un grid item con `align-items: end` es ambiguo

- El panel central (`.center-panel`) tenía `height: 80%` como hijo de un
  `.hud-bottom-bar { display: grid; align-items: end; }`. Con
  `align-items: end`, el item NO se estira para llenar la fila (se
  auto-dimensiona por contenido y se ancla abajo) - un `height: 80%` en
  ese contexto no tiene un porcentaje claro contra el cual resolverse,
  y el resultado visual fue un panel "flotando" en una posición
  impredecible, tapando parte de los slots de baneo.
- **Arreglo**: `align-self: stretch` en el item específico en vez de un
  `height` en porcentaje - le dice al grid explícitamente "llena el
  alto completo de tu columna", sin ambigüedad, sin depender de cómo el
  navegador interprete un porcentaje contra un contenedor de altura
  intrínseca.
- **Regla general**: evitar `height: %` dentro de contenedores flex/grid
  salvo que el eje de alineación sea `stretch` (el default) o el padre
  tenga una altura explícita y definida - en cualquier otro caso, usar
  `align-self`/`flex`/unidades absolutas (`vh`, `px`) en vez de
  porcentajes.

## Boilerplate de Vite sin limpiar causó un bug de alineación real

- **`index.css` seguía con el boilerplate original de Vite**:
  `#root { text-align: center; width: 1126px; margin: 0 auto; ... }`.
  Como `text-align` es una propiedad heredada (a diferencia del layout
  de `position`, que si escapa del padre con `position: fixed`), un
  componente que no fija su propio `text-align` explícito hereda lo que
  sea que diga el ancestro más cercano que sí lo defina - en este caso,
  "centrado", sin que nadie lo haya pedido a propósito.
- **Cómo se manifestó**: el nombre del jugador de la izquierda en el
  panel dramático (HUD-5) se veía descentrado/mal ubicado, mientras que
  el de la derecha se veía bien - porque el de la derecha SÍ tenía
  `text-align: right` explícito (para el efecto espejado), y por
  casualidad esa declaración explícita tapaba el problema heredado.
- **Regla general**: al armar un proyecto nuevo desde un scaffold
  (`npm create vite`), limpiar el CSS base heredado (`index.css`,
  `App.css`) antes de construir encima, no cuando algo ya se ve raro -
  la herencia de CSS puede esconder bugs reales detrás de estilos que
  "no debería estar aplicando nadie, pero están".

## Pendiente de validar en la máquina de Seba

- Comportamiento visual del overlay dentro de un Browser Source real de
  OBS (transparencia, dimensiones) — la conexión Socket.IO ya está
  probada, falta agregarlo como Browser Source real y verlo en la
  escena.
- Empaquetado con PyInstaller en Windows y arranque del `.exe` en una
  máquina limpia.
- Ejecución nativa en Windows (no WSL) del flujo completo, para dejar de
  depender de la traducción de IP/`localhost` entre WSL y Windows.
