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

## Pendiente de validar en la máquina de Seba (no reproducible en el sandbox)

- Conexión real a una instancia de OBS corriendo (`Test OBS` end-to-end
  contra el WebSocket Server real).
- Comportamiento visual del overlay dentro de un Browser Source real de
  OBS (transparencia, dimensiones).
- Empaquetado con PyInstaller en Windows y arranque del `.exe` en una
  máquina limpia.
