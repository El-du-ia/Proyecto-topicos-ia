"""
Selección de contexto para sesiones largas.

Una conversación reanudada puede tener cientos de mensajes y superar el límite
del modelo. Se envían solo los más recientes, dentro de un presupuesto de
mensajes y de caracteres, y siempre empezando en un mensaje del usuario: así
nunca se corta un par "llamada a herramienta → resultado", que la mayoría de
proveedores rechaza.
"""

from __future__ import annotations

import json
from typing import Any


def _size(message: dict[str, Any]) -> int:
    size = len(str(message.get("content") or ""))
    if message.get("tool_calls"):
        size += len(json.dumps(message["tool_calls"], ensure_ascii=False))
    return size


def select_context(
    history: list[dict[str, Any]], max_messages: int = 60, max_chars: int = 120_000
) -> list[dict[str, Any]]:
    if len(history) <= max_messages and sum(_size(m) for m in history) <= max_chars:
        return history

    start = len(history)
    total = 0
    while start > 0 and len(history) - start < max_messages:
        size = _size(history[start - 1])
        if total + size > max_chars and start < len(history):
            break
        total += size
        start -= 1

    # Avanzar hasta el primer mensaje del usuario dentro de la ventana.
    while start < len(history) and history[start].get("role") != "user":
        start += 1
    if start == len(history):
        # Un solo turno enorme: se conserva desde su último mensaje de usuario.
        start = max((i for i, m in enumerate(history) if m.get("role") == "user"), default=len(history))
    return history[start:]
