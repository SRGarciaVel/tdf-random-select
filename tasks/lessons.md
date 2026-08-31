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

## Pendiente de validar en la máquina de Seba

- Comportamiento visual del overlay dentro de un Browser Source real de
  OBS (transparencia, dimensiones) — la conexión Socket.IO ya está
  probada, falta agregarlo como Browser Source real y verlo en la
  escena.
- Empaquetado con PyInstaller en Windows y arranque del `.exe` en una
  máquina limpia.
- Ejecución nativa en Windows (no WSL) del flujo completo, para dejar de
  depender de la traducción de IP/`localhost` entre WSL y Windows.
