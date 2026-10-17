"""
Runner: el ciclo del agente.

    usuario → modelo → (¿pide herramientas?) → validar → confirmar → ejecutar → modelo → ...

La confirmación de herramientas sensibles la impone el Runner, no el prompt: el
modelo no puede ejecutar un escaneo sin que el usuario lo apruebe, aunque "se
olvide" de preguntar. Cada decisión y ejecución queda en la auditoría.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from ..errors import ToolError
from ..security.audit import AuditLog
from .agent import Agent
from .llm import LLMClient, LLMResponse, ToolCall, Usage
from .tools import Tool, ToolContext

REJECTED_MESSAGE = (
    "El usuario RECHAZÓ esta acción y no se ejecutó. No la intentes de nuevo por otro "
    "camino; pregúntale qué prefiere hacer."
)


class RunHooks:
    """Puntos de extensión para que la interfaz muestre el progreso.

    Por defecto no hacen nada y `confirm` RECHAZA: si nadie puede preguntarle al
    usuario, una acción sensible no se ejecuta.
    """

    # Si es True, el Runner pide la respuesta en streaming y llama a on_text con cada fragmento.
    streaming: bool = False

    def on_text(self, delta: str) -> None: ...

    def on_llm_start(self) -> None: ...

    def on_llm_end(self, response: LLMResponse) -> None: ...

    def on_llm_error(self) -> None: ...

    def on_tool_start(self, tool: Tool, arguments: dict[str, Any]) -> None: ...

    def on_tool_end(self, tool: Tool, arguments: dict[str, Any], result: str, ok: bool) -> None: ...

    def confirm(self, tool: Tool, arguments: dict[str, Any]) -> bool:
        return False


@dataclass
class RunResult:
    final_output: str
    new_messages: list[dict[str, Any]]
    usage: Usage = field(default_factory=Usage)
    turns: int = 0
    hit_max_turns: bool = False


class Runner:
    def __init__(
        self,
        agent: Agent,
        llm: LLMClient,
        context: ToolContext | None = None,
        hooks: RunHooks | None = None,
        audit: AuditLog | None = None,
        max_turns: int = 20,
        max_tool_output: int = 20_000,
    ) -> None:
        self.agent = agent
        self.llm = llm
        self.context = context
        self.hooks = hooks or RunHooks()
        self.audit = audit
        self.max_turns = max_turns
        self.max_tool_output = max_tool_output

    def run(self, history: list[dict[str, Any]], user_input: str) -> RunResult:
        """Procesa un mensaje del usuario. `history` no se modifica; usa `new_messages`."""
        user_message = {"role": "user", "content": user_input}
        messages = [self.agent.system_message(), *history, user_message]
        new_messages: list[dict[str, Any]] = [user_message]
        usage = Usage()
        tools = self.agent.tools.schemas()

        for turn in range(1, self.max_turns + 1):
            self.hooks.on_llm_start()
            try:
                on_text = self.hooks.on_text if self.hooks.streaming else None
                response = self.llm.complete(messages, tools, on_text=on_text)
            except BaseException:
                self.hooks.on_llm_error()  # para que la interfaz limpie (p. ej. el spinner)
                raise
            self.hooks.on_llm_end(response)
            usage = usage + response.usage

            assistant_message = response.to_message()
            messages.append(assistant_message)
            new_messages.append(assistant_message)

            if not response.tool_calls:
                return RunResult(response.content or "", new_messages, usage, turn)

            for call in response.tool_calls:
                result = self._execute(call)
                tool_message = {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.name,
                    "content": result,
                }
                messages.append(tool_message)
                new_messages.append(tool_message)

        return RunResult(
            "Se alcanzó el límite de pasos para esta petición. Puedes pedirme que continúe.",
            new_messages,
            usage,
            self.max_turns,
            hit_max_turns=True,
        )

    def _execute(self, call: ToolCall) -> str:
        tool = self.agent.tools.get(call.name)
        if tool is None:
            return f"Error: la herramienta '{call.name}' no existe."

        try:
            arguments = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            return f"Error: los argumentos para {call.name} no son JSON válido."
        if not isinstance(arguments, dict):
            return f"Error: los argumentos para {call.name} deben ser un objeto JSON."

        availability = tool.availability()
        if not availability.ok:
            return f"La herramienta {tool.name} no está disponible en este equipo: {availability.detail}"

        # Validar antes de confirmar: no tiene sentido pedir permiso para algo inválido
        # o fuera del alcance.
        try:
            tool.validate(arguments, self.context)
        except ToolError as exc:
            self._audit("tool_blocked", tool=tool.name, arguments=arguments, reason=str(exc))
            return f"Error: {exc}"

        if tool.sensitive:
            approved = bool(self.hooks.confirm(tool, arguments))
            self._audit("confirmation", tool=tool.name, arguments=arguments, approved=approved)
            if not approved:
                return REJECTED_MESSAGE

        self.hooks.on_tool_start(tool, arguments)
        started = time.perf_counter()
        ok = True
        try:
            result = tool.invoke(arguments, self.context)
        except ToolError as exc:
            ok, result = False, f"Error: {exc}"
        except Exception as exc:  # error inesperado: se informa al modelo, no se cae la sesión
            ok, result = False, f"Error inesperado en {tool.name}: {type(exc).__name__}: {exc}"
        duration = round(time.perf_counter() - started, 3)

        self._audit(
            "tool_execution",
            tool=tool.name,
            arguments=arguments,
            ok=ok,
            duration_s=duration,
            output_preview=result[:500],
        )
        self.hooks.on_tool_end(tool, arguments, result, ok)

        if len(result) > self.max_tool_output:
            omitted = len(result) - self.max_tool_output
            result = (
                result[: self.max_tool_output] + f"\n\n[... salida truncada, {omitted} caracteres omitidos]"
            )
        return result

    def _audit(self, event: str, **data: Any) -> None:
        if self.audit is not None:
            self.audit.record(event, **data)
