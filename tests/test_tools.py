from __future__ import annotations

from typing import Literal

import pytest

from dui.agent import Availability, ToolContext, ToolError, ToolRegistry, tool


@tool(sensitive=True, category="network", risks=("Hace ruido en la red",))
def sample(
    target: str,
    mode: Literal["fast", "slow"] = "fast",
    count: int = 10,
    ports: list[int] | None = None,
    ctx: ToolContext | None = None,
) -> str:
    """Herramienta de ejemplo.

    Args:
        target: Objetivo a analizar.
        mode: Velocidad del análisis,
            rápida o lenta.
        count: Cantidad de intentos.
    Returns:
        Un texto.
    """
    return f"{target}-{mode}-{count}-{ports}-{ctx is not None}"


def test_schema_generated_from_signature_and_docstring():
    fn = sample.to_openai()["function"]
    assert fn["name"] == "sample"
    assert fn["description"] == "Herramienta de ejemplo."
    props = fn["parameters"]["properties"]
    assert props["target"] == {"type": "string", "description": "Objetivo a analizar."}
    assert props["mode"]["enum"] == ["fast", "slow"]
    assert props["mode"]["description"] == "Velocidad del análisis, rápida o lenta."
    assert props["mode"]["default"] == "fast"
    assert props["count"]["type"] == "integer"
    assert props["ports"] == {"type": "array", "items": {"type": "integer"}}
    assert "ctx" not in props
    assert fn["parameters"]["required"] == ["target"]
    assert sample.sensitive and sample.risks == ("Hace ruido en la red",)


def test_invoke_injects_context(context):
    assert sample.invoke({"target": "x"}, context) == "x-fast-10-None-True"


def test_invoke_rejects_unknown_and_missing_arguments():
    with pytest.raises(ToolError, match="desconocidos"):
        sample.invoke({"target": "x", "evil": 1})
    with pytest.raises(ToolError, match="obligatorios"):
        sample.invoke({})


def test_tool_still_callable_directly():
    assert sample("y", "slow", 1) == "y-slow-1-None-False"


def test_missing_docstring_or_hints_is_rejected():
    with pytest.raises(TypeError):

        @tool
        def no_doc(x: str) -> str:
            return x

    with pytest.raises(TypeError):

        @tool
        def no_hint(x) -> str:
            """Doc."""
            return x


def test_broken_check_reports_unavailable():
    def boom() -> Availability:
        raise RuntimeError("falla")

    @tool(check=boom)
    def checked() -> str:
        """Doc."""
        return "ok"

    assert not checked.availability().ok


def test_registry_rejects_duplicates():
    registry = ToolRegistry([sample])
    assert "sample" in registry and len(registry) == 1
    with pytest.raises(ValueError):
        registry.register(sample)
