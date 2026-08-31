from __future__ import annotations

import logging

import obsws_python as obs

logger = logging.getLogger(__name__)


class ObsConnectionError(Exception):
    """OBS no está corriendo, o el WebSocket Server está deshabilitado/mal configurado."""


class ObsService:
    """Única puerta de entrada a obsws-python (ver CODESTYLE.md).

    Modo degradado: si OBS no está disponible, el draft debe poder seguir
    corriendo igual (ver CODESTYLE.md, sección Producción) — por eso los
    métodos públicos capturan el error de conexión y lo transforman en
    ObsConnectionError en vez de dejar reventar la excepción cruda de la
    librería hacia el resto de la app.
    """

    def __init__(self, host: str = "localhost", port: int = 4455, password: str = "") -> None:
        self._host = host
        self._port = port
        self._password = password
        self._client: obs.ReqClient | None = None
        self._previous_scene: str | None = None

    def connect(self) -> None:
        try:
            self._client = obs.ReqClient(
                host=self._host, port=self._port, password=self._password, timeout=3
            )
        except Exception as exc:  # la librería no expone una excepción propia estable
            raise ObsConnectionError(str(exc)) from exc

    def list_scenes(self) -> list[str]:
        if self._client is None:
            raise ObsConnectionError("No hay conexión activa a OBS.")
        response = self._client.get_scene_list()
        return [scene["sceneName"] for scene in response.scenes]

    def switch_to_draft_scene(self, draft_scene_name: str) -> None:
        """Guarda la escena activa y cambia a la escena de draft (SPECS.md §5)."""
        if self._client is None:
            raise ObsConnectionError("No hay conexión activa a OBS.")
        current = self._client.get_current_program_scene()
        self._previous_scene = current.current_program_scene_name
        self._client.set_current_program_scene(draft_scene_name)

    def restore_previous_scene(self) -> None:
        """Vuelve a la escena guardada en switch_to_draft_scene, si existe."""
        if self._client is None:
            raise ObsConnectionError("No hay conexión activa a OBS.")
        if self._previous_scene is None:
            logger.warning("restore_previous_scene llamado sin una escena guardada previa.")
            return
        self._client.set_current_program_scene(self._previous_scene)
        self._previous_scene = None
