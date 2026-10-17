"""Pruebas de punta a punta: terminal + runner + herramientas con un modelo simulado."""

from __future__ import annotations

import io

from helpers import FakeLLM, call, reply
from rich.console import Console

from dui.__main__ import build_agent, main
from dui.agent import tool
from dui.security import AuditLog
from dui.tools.reports import generate_report
from dui.ui import Terminal


def make_terminal(context, responses, answers):
    answers = iter(answers)
    console = Console(file=io.StringIO(), width=120, force_terminal=False)
    terminal = Terminal(
        build_agent(context),
        FakeLLM(responses),
        context,
        AuditLog("test"),
        console=console,
        input_func=lambda prompt: next(answers),
    )
    terminal.console.input = lambda prompt="": next(answers)  # respuestas a confirmaciones
    return terminal


def output(terminal) -> str:
    return terminal.console.file.getvalue()


def test_conversation_keeps_context_and_commands_work(context):
    terminal = make_terminal(
        context,
        [reply("Primera respuesta"), reply("Segunda respuesta")],
        ["hola", "/status", "otra pregunta", "/cost", "/exit"],
    )
    terminal.run()
    text = output(terminal)
    assert "Primera respuesta" in text and "Segunda respuesta" in text
    assert len(terminal.history) == 4
    assert "Tokens: 20 de entrada" in text


def test_sensitive_tool_confirmation_flow(context):
    @tool(sensitive=True, risks=("Ruido en la red",))
    def fake_scan(target: str) -> str:
        """Escaneo de prueba.

        Args:
            target: Objetivo.
        """
        return "puerto 22 abierto"

    terminal = make_terminal(
        context,
        [call("fake_scan", target="192.168.1.1"), reply("Encontré el puerto 22")],
        ["escanea mi router", "talvez", "s", "/exit"],
    )
    terminal.agent.tools.register(fake_scan)
    terminal.run()
    text = output(terminal)
    assert "CONFIRMACIÓN REQUERIDA" in text and "Ruido en la red" in text
    assert "Responde 's'" in text and "Acción aprobada" in text
    assert "puerto 22 abierto" in text
    assert terminal.audit.summary()["approvals"] == 1


def test_scope_add_requires_confirmation(context):
    terminal = make_terminal(context, [], ["/scope add 8.8.8.8", "n", "/scope add 8.8.8.8", "s", "/exit"])
    terminal.run()
    assert context.scope.check("8.8.8.8")[0]
    assert [e["event"] for e in terminal.audit.events] == ["scope_added"]


def test_llm_error_is_shown_and_session_continues(context):
    from dui.errors import LLMError

    class Broken(FakeLLM):
        def complete(self, messages, tools, on_text=None):
            raise LLMError("AuthenticationError: clave inválida")

    terminal = make_terminal(context, [], ["hola", "/exit"])
    terminal.runner.llm = Broken([])
    terminal.run()
    assert "clave inválida" in output(terminal) and terminal.history == []


def test_generate_report_writes_markdown(context):
    out = generate_report.invoke(
        {"title": "Análisis de red", "content": "## 1. Resumen\nTodo bien", "raw_data": "a ``` b"},
        context,
    )
    path = context.settings.reports_path
    files = list(path.glob("*_analisis-de-red.md"))
    assert len(files) == 1 and str(files[0].resolve()) in out
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("# Análisis de red") and "````text" in text


def test_invalid_scope_config_exits_cleanly(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("DUI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DUI_SCOPE", "-iL")
    assert main(["--check"]) == 2
    assert "Configuración inválida" in capsys.readouterr().out


def test_check_command(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("DUI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DUI_MODEL", "ollama_chat/llama3.1")
    assert main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Modelo local" in out and "dns_lookup" in out
