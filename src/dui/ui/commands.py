"""Catálogo de comandos de la terminal y su autocompletado."""

from __future__ import annotations

from collections.abc import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

COMMAND_GROUPS: dict[str, dict[str, str]] = {
    "General": {
        "/help": "Muestra esta ayuda",
        "/tools": "Herramientas y si están disponibles en este equipo",
        "/scope": "Alcance permitido ('/scope add <objetivo>' para ampliarlo)",
        "/model": "Muestra o cambia el modelo ('/model ollama_chat/llama3.1')",
        "/status": "Estado del sistema, del modelo y de la sesión",
        "/cost": "Tokens y costo acumulado de la sesión",
        "/clear": "Limpia la pantalla",
        "/exit": "Salir",
    },
    "Sesiones": {
        "/sessions": "Lista las sesiones guardadas",
        "/resume": "Continúa la sesión más reciente",
        "/load": "Carga una sesión: '/load 2' (número) o '/load 47437b' (parte del ID)",
        "/search": "Busca en todas las conversaciones: '/search puertos abiertos'",
        "/history": "Muestra la conversación actual",
        "/audit": "Auditoría de la sesión actual",
        "/rename": "Cambia el título: '/rename Red de la oficina'",
        "/export": "Exporta la sesión: '/export' (Markdown) o '/export json'",
        "/delete": "Borra una sesión: '/delete 2' o '/delete 47437b'",
        "/new": "Empieza una sesión nueva (la actual queda guardada)",
    },
}

COMMANDS: dict[str, str] = {cmd: desc for group in COMMAND_GROUPS.values() for cmd, desc in group.items()}

ALIASES = {
    "/ayuda": "/help",
    "/herramientas": "/tools",
    "/alcance": "/scope",
    "/modelo": "/model",
    "/estado": "/status",
    "/costo": "/cost",
    "/limpiar": "/clear",
    "/quit": "/exit",
    "/salir": "/exit",
    "/sesiones": "/sessions",
    "/continuar": "/resume",
    "/cargar": "/load",
    "/buscar": "/search",
    "/historial": "/history",
    "/auditoria": "/audit",
    "/auditoría": "/audit",
    "/renombrar": "/rename",
    "/exportar": "/export",
    "/borrar": "/delete",
    "/nueva": "/new",
}


def canonical(name: str) -> str:
    name = name.lower()
    return ALIASES.get(name, name)


class CommandCompleter(Completer):
    """Sugiere comandos con su descripción mientras se escribe '/...'."""

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        text = document.text_before_cursor
        if not text.startswith("/") or " " in text:
            return
        typed = text.lower()
        for command, description in COMMANDS.items():
            if command.startswith(typed):
                yield Completion(command, start_position=-len(text), display_meta=description)
        for alias, target in ALIASES.items():
            if alias.startswith(typed) and len(typed) > 1:
                yield Completion(alias, start_position=-len(text), display_meta=f"= {target}")
