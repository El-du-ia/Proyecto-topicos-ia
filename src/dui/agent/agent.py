"""El agente: nombre, instrucciones y herramientas (igual que en la arquitectura de CAI)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .tools import ToolRegistry


@dataclass
class Agent:
    name: str
    # Texto fijo o función que lo genera (para reflejar cambios, p. ej. en el alcance).
    instructions: str | Callable[[], str]
    tools: ToolRegistry

    def system_message(self) -> dict[str, Any]:
        text = self.instructions() if callable(self.instructions) else self.instructions
        return {"role": "system", "content": text}
