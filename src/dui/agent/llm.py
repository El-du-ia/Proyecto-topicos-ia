"""
Acceso a modelos de lenguaje.

El Runner solo conoce la interfaz LLMClient. La implementación por defecto usa
LiteLLM, que habla con más de 100 proveedores (Gemini, OpenAI, Anthropic,
Mistral, Groq...) y con modelos locales (Ollama, LM Studio, vLLM) usando el
formato de mensajes de OpenAI. Cambiar de modelo es cambiar un texto:
"gemini/gemini-2.5-flash", "ollama_chat/llama3.1", "openai/gpt-4o-mini", etc.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from ..errors import LLMError


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
            self.cost + other.cost,
        )


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON tal como lo devolvió el modelo


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)

    def to_message(self) -> dict[str, Any]:
        """Mensaje del asistente en formato OpenAI, listo para el historial."""
        message: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments},
                }
                for call in self.tool_calls
            ]
        return message


TextCallback = Callable[[str], None]


class LLMClient(Protocol):
    model: str

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback | None = None,
    ) -> LLMResponse:
        """Si se pasa `on_text`, la respuesta se recibe en streaming y cada fragmento de texto
        se entrega en cuanto llega. El resultado final es el mismo en ambos modos."""
        ...


class LiteLLMClient:
    def __init__(
        self,
        model: str,
        api_base: str | None = None,
        temperature: float | None = None,
        timeout: float = 180,
        retries: int = 3,
        retry_delay: float = 2.0,
    ) -> None:
        self.model = model
        self.api_base = api_base
        self.temperature = temperature
        self.timeout = timeout
        # Reintentos con espera creciente (2 s, 4 s, 8 s) ante errores pasajeros del proveedor.
        self.retries = retries
        self.retry_delay = retry_delay
        self._sleep = time.sleep

    @staticmethod
    def _litellm() -> Any:
        # Usar el mapa de precios incluido en el paquete en lugar de descargarlo al arrancar.
        os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
        import litellm  # importación diferida: tarda en cargar

        litellm.suppress_debug_info = True
        return litellm

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: TextCallback | None = None,
    ) -> LLMResponse:
        litellm = self._litellm()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "timeout": self.timeout,
            "drop_params": True,  # ignora parámetros que un proveedor no soporte
        }
        if tools:
            kwargs["tools"] = tools
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        if on_text is not None:
            kwargs["stream"] = True
            kwargs["stream_options"] = {"include_usage": True}

        attempt = 0
        emitted = False
        while True:
            try:
                if on_text is None:
                    response = litellm.completion(**kwargs)
                else:

                    def emit(delta: str) -> None:
                        nonlocal emitted
                        emitted = True
                        on_text(delta)

                    response = self._stream(litellm, kwargs, emit)
                break
            except Exception as exc:
                # Si ya se mostró texto al usuario, reintentar lo duplicaría: se informa el error.
                if attempt < self.retries and _is_transient(exc) and not emitted:
                    self._sleep(self.retry_delay * 2**attempt)
                    attempt += 1
                    continue
                raise LLMError(_friendly_error(self.model, exc)) from exc

        message = response.choices[0].message
        tool_calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=call.function.arguments or "{}",
            )
            for call in (getattr(message, "tool_calls", None) or [])
        ]
        usage = Usage()
        if getattr(response, "usage", None):
            usage.prompt_tokens = response.usage.prompt_tokens or 0
            usage.completion_tokens = response.usage.completion_tokens or 0
        try:
            usage.cost = float(litellm.completion_cost(completion_response=response) or 0.0)
        except Exception:  # modelos locales o sin precio conocido
            usage.cost = 0.0
        return LLMResponse(content=message.content, tool_calls=tool_calls, usage=usage)

    @staticmethod
    def _stream(litellm: Any, kwargs: dict[str, Any], emit: TextCallback) -> Any:
        """Recibe la respuesta por fragmentos y la reconstruye completa (texto, tool calls y uso)."""
        chunks = []
        for chunk in litellm.completion(**kwargs):
            chunks.append(chunk)
            if chunk.choices:
                delta = getattr(chunk.choices[0].delta, "content", None)
                if delta:
                    emit(delta)
        response = litellm.stream_chunk_builder(chunks, messages=kwargs["messages"])
        if response is None:
            raise LLMError("El modelo no devolvió ninguna respuesta.")
        return response


_TRANSIENT_ERRORS = {"ServiceUnavailableError", "RateLimitError", "InternalServerError", "Timeout"}


def _is_transient(exc: Exception) -> bool:
    """Errores que suelen resolverse solos (saturación del proveedor, cortes breves)."""
    name = type(exc).__name__
    if name == "APIConnectionError":
        return "api key" not in str(exc).lower()  # falta de API key: reintentar no sirve
    return name in _TRANSIENT_ERRORS


def _error_text(exc: Exception) -> str:
    """Extrae el mensaje legible, aunque el proveedor lo devuelva como JSON en varias líneas."""
    raw = str(exc)
    match = re.search(r'"message"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if match:
        try:
            return str(json.loads(f'"{match.group(1)}"'))[:300]
        except ValueError:
            return match.group(1)[:300]
    first = next((line.strip() for line in raw.splitlines() if line.strip()), type(exc).__name__)
    return first[:300]


def _friendly_error(model: str, exc: Exception) -> str:
    name = type(exc).__name__
    text = _error_text(exc)
    provider = model.split("/", 1)[0]
    hints = {
        "AuthenticationError": f"Revisa la API key de '{provider}' en tu archivo .env.",
        "APIConnectionError": "No hay conexión con el proveedor. Si usas un modelo local, "
        "¿está corriendo el servidor (por ejemplo 'ollama serve')?",
        "NotFoundError": f"El modelo '{model}' no existe o no está disponible para tu cuenta.",
        "RateLimitError": "Se alcanzó el límite de uso del proveedor. Espera un momento.",
        "ServiceUnavailableError": "El proveedor está saturado (ya se reintentó varias veces). "
        "Prueba en unos minutos o cambia de modelo con /model.",
        "InternalServerError": "Error interno del proveedor. Prueba de nuevo en un momento.",
        "BadRequestError": "El proveedor rechazó la petición. Algunos modelos locales no "
        "soportan herramientas (function calling); prueba con otro modelo.",
        "Timeout": "El modelo tardó demasiado en responder.",
    }
    hint = hints.get(name, "")
    # LiteLLM reporta la falta de API key como error de conexión.
    if "api key" in text.lower() or "api_key" in text.lower():
        hint = hints["AuthenticationError"] + " (ver .env.example)"
    text = text.removeprefix("litellm.").removeprefix(f"{name}: ").removeprefix("litellm.")
    return f"{name}: {text}" + (f"\n{hint}" if hint else "")
