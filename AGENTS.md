# AGENTS.md — Orden de trabajo obligatorio en este proyecto

Al iniciar cualquier sesión de desarrollo en este repo, seguir este orden:

1. Leer `./SPECS.md`, `README.md`, `CODESTYLE.md` y `ROADMAP.md`, en ese orden.
2. Completar los bullet points correspondientes en `ROADMAP.md` a medida que
   se avanza — no acumular trabajo sin reflejarlo ahí.
3. Commit en cada checkpoint significativo, no al final de la sesión.
   Conventional commits (`tipo: descripción`), hechos por CLI.
4. No abusar de comentarios ni de tokens — ver reglas de comentarios en
   `CODESTYLE.md`.
5. Formatear (`ruff format` en Python, `prettier` en `overlay_app`) antes de
   cada commit.

Metodología general del proyecto (aplica a cualquier tarea no trivial, 3+
pasos o decisión de arquitectura):

- Entrar en modo plan antes de construir. Si algo se tuerce, detenerse y
  volver a planificar — no seguir empujando sobre un plan que dejó de servir.
- Actualizar `tasks/lessons.md` después de cualquier corrección del usuario.
- Nunca marcar una tarea como completa sin demostrar que funciona
  (correr, probar, mostrar logs). Para las piezas que dependen de hardware
  o software que solo existe en la máquina de Seba (OBS real, PyQt6 con
  display real en Windows), dejar explícito en el checklist qué se validó
  en el sandbox y qué queda pendiente de validar en su máquina.
- Preferir la solución elegante sobre el parche rápido en cambios no
  triviales; saltarse esto en arreglos simples y obvios.

## Particularidad de este proyecto: walking skeleton primero

A diferencia de un backend web tradicional, este proyecto integra cuatro
piezas nuevas para Seba al mismo tiempo (PyQt6 + asyncio compartiendo
loop vía `qasync`, Flask-SocketIO embebido dentro de un proceso desktop,
un build de Vite servido por ese mismo Flask, y la conexión real a
`obsws-python`). Antes de construir lógica de negocio, se valida que las
cuatro piezas funcionan juntas de punta a punta con datos reales — ver
`SPECS.md §7`. No se avanza a la lógica del draft hasta que el esqueleto
esté confirmado funcionando.
