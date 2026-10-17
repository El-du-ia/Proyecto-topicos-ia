"""Utilidades compartidas por las pruebas."""

from __future__ import annotations

import json
from typing import Any

from dui.agent import Agent, LLMResponse, ToolCall, ToolRegistry, Usage


class FakeLLM:
    """Modelo simulado: devuelve respuestas predefinidas y guarda lo que recibió."""

    def __init__(self, responses: list[LLMResponse]) -> None:
        self.model = "fake/model"
        self.responses = list(responses)
        self.calls: list[list[dict[str, Any]]] = []

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        self.calls.append([dict(m) for m in messages])
        if not self.responses:
            return LLMResponse(content="(sin más respuestas)")
        return self.responses.pop(0)


def call(tool_name: str, call_id: str = "call_1", **arguments: Any) -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=tool_name, arguments=json.dumps(arguments))],
        usage=Usage(10, 5, 0.001),
    )


def reply(text: str) -> LLMResponse:
    return LLMResponse(content=text, usage=Usage(10, 5, 0.001))


def make_agent(*tools) -> Agent:
    return Agent(name="test", instructions="Eres un agente de prueba.", tools=ToolRegistry(tools))
