# CODESTYLE.md — TDF Random Select

Reglas de estilo para este proyecto. Aplican a todo el código que se
commitee, sin excepción.

## Idioma

- **Nomenclatura de código** (variables, funciones, clases, archivos,
  eventos de Socket.IO): **inglés estricto**.
- **Comentarios, docstrings, mensajes de commit y documentación**
  (`SPECS.md`, `README.md`, `ROADMAP.md`, este archivo): **español**.
- **Texto visible en el overlay y en el panel de control** (labels,
  botones, mensajes de estado, nombres de estados del draft mostrados al
  usuario): español chileno, tuteo con conjugación de **tú** ("banea",
  "elige", "confirma"), **nunca** voseo rioplatense ("baneá", "elegí",
  "confirmá"). Misma regla sin excepción que en `tdf-edeportes`.
- **Sin em-dash ("—") en texto visible** (overlay ni panel de control).
  Usar punto, coma, o separar en dos oraciones. Esta regla no aplica a
  comentarios de código.
- Antes de dar por terminado cualquier texto nuevo visible, revisar que
  no se haya colado ninguna conjugación de voseo ni ningún em-dash.

## Comentarios

- Comentar **solo** lo que no es obvio desde el código mismo: decisiones
  de arquitectura, trade-offs, "por qué" en vez de "qué".
- Prohibido comentar código evidente.
- Nada de comentarios vagos tipo `# fix` o `# TODO` sin contexto.
- Docstrings solo en funciones/endpoints públicos con lógica no trivial.

## Formato y estructura

- **Python (`backend/`, `control_panel/`, `main.py`):** `ruff` para lint
  + format. Tipado obligatorio con type hints en toda función pública.
  Pydantic (o dataclasses, si Pydantic es demasiado para el caso) para
  validar los payloads que cruzan el Socket.IO.
- **TypeScript (`overlay_app/`):** `eslint` + `prettier`. `strict: true`
  en `tsconfig.json`. Nada de `any` sin justificación explícita en
  comentario.
- Un archivo, una responsabilidad. La lógica de negocio del draft
  (transiciones de estado, validación de baneos) vive en
  `backend/app/services/`, nunca en los handlers de Socket.IO ni en los
  widgets de PyQt6 — esos solo orquestan.
- La lógica de conexión a OBS vive únicamente en
  `backend/app/services/obs_service.py`. Ningún otro módulo llama a
  `obsws-python` directamente.

## Producción

- Nada de credenciales hardcodeadas (password de OBS WebSocket incluido)
  — vía `obs_settings` en SQLite, configurable desde el panel, nunca en
  el código fuente.
- Nada de `print()` en código que llega al `.exe` final — usar `loguru`
  o `logging` estándar, con nivel configurable.
- Manejo explícito de errores en la integración con OBS: si OBS no está
  corriendo o la conexión falla, la app debe seguir funcionando en modo
  degradado (el draft funciona igual, solo sin el cambio automático de
  escena) y mostrar el error en el panel, nunca crashear en medio de un
  stream en vivo.

## Commits

- Conventional commits: `tipo: descripción breve en español`.
  Tipos: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.
- Un commit por checkpoint significativo del `ROADMAP.md`.
- Formatear (`ruff format` / `prettier`) **antes** de cada commit.

## Elegancia sobre parches

- Antes de cerrar cualquier tarea no trivial: ¿hay una forma más simple
  de resolver esto con lo que ya está en el stack? Si la respuesta es
  sí, se rehace antes de commitear.
- No se sobre-ingenieriza: si el problema es simple, la solución es
  simple.
