from __future__ import annotations

from typing import Any

from helpers import FakeLLM, call, make_agent, reply

from dui.agent import Availability, RunHooks, Runner, Tool, ToolContext, tool
from dui.agent.runner import REJECTED_MESSAGE
from dui.security import AuditLog

executed: list[str] = []


def _scope_validator(arguments: dict[str, Any], ctx: ToolContext) -> None:
    ctx.scope.ensure_allowed(arguments["target"])


@tool(sensitive=True, validator=_scope_validator)
def scan(target: str) -> str:
    """Escanea un objetivo.

    Args:
        target: Objetivo.
    """
    executed.append(target)
    return f"escaneado {target}"


@tool
def lookup(name: str) -> str:
    """Consulta pasiva.

    Args:
        name: Nombre.
    """
    return f"info de {name}"


@tool(check=lambda: Availability.no("falta Npcap"))
def sniff() -> str:
    """Captura tráfico."""
    return "nunca"


@tool
def crash() -> str:
    """Falla siempre."""
    raise RuntimeError("explotó")


class Hooks(RunHooks):
    def __init__(self, answer: bool) -> None:
        self.answer = answer
        self.asked: list[tuple[str, dict]] = []

    def confirm(self, tool: Tool, arguments: dict) -> bool:
        self.asked.append((tool.name, arguments))
        return self.answer


def run(responses, hooks=None, context=None, tools=(scan, lookup, sniff, crash), **kwargs):
    executed.clear()
    audit = AuditLog("test")
    llm = FakeLLM(responses)
    runner = Runner(make_agent(*tools), llm, context=context, hooks=hooks, audit=audit, **kwargs)
    return runner.run([], "hola"), llm, audit


def tool_results(result) -> list[str]:
    return [m["content"] for m in result.new_messages if m["role"] == "tool"]


def test_plain_answer_without_tools():
    result, llm, _ = run([reply("Hola, ¿en qué te ayudo?")])
    assert result.final_output == "Hola, ¿en qué te ayudo?"
    assert [m["role"] for m in result.new_messages] == ["user", "assistant"]
    assert llm.calls[0][0]["role"] == "system"


def test_sensitive_tool_rejected_is_not_executed(context):
    hooks = Hooks(answer=False)
    result, _, audit = run([call("scan", target="192.168.1.10"), reply("De acuerdo")], hooks, context)
    assert executed == []
    assert tool_results(result) == [REJECTED_MESSAGE]
    assert hooks.asked == [("scan", {"target": "192.168.1.10"})]
    assert audit.summary()["rejections"] == 1


def test_sensitive_tool_approved_is_executed_and_audited(context):
    hooks = Hooks(answer=True)
    result, _, audit = run([call("scan", target="192.168.1.10"), reply("Listo")], hooks, context)
    assert executed == ["192.168.1.10"]
    assert tool_results(result) == ["escaneado 192.168.1.10"]
    summary = audit.summary()
    assert summary["approvals"] == 1 and summary["tools_used"] == ["scan"]


def test_default_hooks_deny_sensitive_tools(context):
    result, _, _ = run([call("scan", target="192.168.1.10"), reply("ok")], None, context)
    assert executed == [] and tool_results(result) == [REJECTED_MESSAGE]


def test_out_of_scope_is_blocked_before_asking(context):
    hooks = Hooks(answer=True)
    result, _, audit = run([call("scan", target="8.8.8.8"), reply("ok")], hooks, context)
    assert hooks.asked == [] and executed == []
    assert "FUERA del alcance" in tool_results(result)[0]
    assert audit.events[0]["event"] == "tool_blocked"


def test_non_sensitive_tool_runs_without_confirmation():
    hooks = Hooks(answer=False)
    result, _, _ = run([call("lookup", name="x"), reply("ok")], hooks)
    assert hooks.asked == [] and tool_results(result) == ["info de x"]


def test_errors_are_reported_to_the_model_not_raised():
    responses = [
        call("missing_tool"),
        call("lookup", call_id="2", wrong="x"),
        call("sniff", call_id="3"),
        call("crash", call_id="4"),
        reply("fin"),
    ]
    result, _, _ = run(responses)
    errors = tool_results(result)
    assert "no existe" in errors[0]
    assert "desconocidos" in errors[1]
    assert "falta Npcap" in errors[2]
    assert "explotó" in errors[3]
    assert result.final_output == "fin"


def test_invalid_json_arguments():
    from dui.agent import LLMResponse, ToolCall

    bad = LLMResponse(content=None, tool_calls=[ToolCall("1", "lookup", "{no json")])
    result, _, _ = run([bad, reply("ok")])
    assert "JSON" in tool_results(result)[0]


def test_max_turns_stops_infinite_tool_loops():
    responses = [call("lookup", call_id=str(i), name="x") for i in range(10)]
    result, _, _ = run(responses, max_turns=3)
    assert result.hit_max_turns and result.turns == 3


def test_long_tool_output_is_truncated():
    @tool
    def big() -> str:
        """Mucho texto."""
        return "x" * 50

    result, _, _ = run([call("big"), reply("ok")], tools=(big,), max_tool_output=10)
    assert tool_results(result)[0].startswith("x" * 10) and "truncada" in tool_results(result)[0]


def test_usage_is_accumulated():
    result, _, _ = run([call("lookup", name="x"), reply("ok")])
    assert result.usage.prompt_tokens == 20 and round(result.usage.cost, 6) == 0.002


def test_history_is_sent_to_model():
    history = [{"role": "user", "content": "antes"}, {"role": "assistant", "content": "respuesta"}]
    llm = FakeLLM([reply("ok")])
    Runner(make_agent(lookup), llm).run(history, "ahora")
    assert [m["content"] for m in llm.calls[0][1:]] == ["antes", "respuesta", "ahora"]
