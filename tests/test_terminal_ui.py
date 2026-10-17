"""Fase 4: streaming, modo sin emojis, barra de estado y autocompletado."""

from __future__ import annotations

import functools
import io

import litellm
import pytest
from helpers import FakeLLM, call, reply
from prompt_toolkit.document import Document
from rich.console import Console

from dui.__main__ import build_agent
from dui.agent import LiteLLMClient, Runner
from dui.agent.prompts import build_system_prompt
from dui.config import Settings
from dui.errors import LLMError
from dui.security import AuditLog
from dui.ui import Terminal, wants_plain
from dui.ui.commands import CommandCompleter, canonical
from dui.ui.hooks import TerminalHooks
from dui.ui.symbols import EMOJI


def make(context, responses, answers, plain=False, streaming=False):
    answers = list(answers)

    def read(prompt=""):
        if not answers:
            raise EOFError
        return answers.pop(0)

    console = Console(file=io.StringIO(), width=120, force_terminal=streaming, color_system=None)
    terminal = Terminal(
        build_agent(context, plain),
        FakeLLM(responses),
        context,
        AuditLog("t"),
        console=console,
        input_func=read,
        plain=plain,
        streaming=streaming,
    )
    terminal.console.input = read
    return terminal


def out(terminal) -> str:
    return terminal.console.file.getvalue()


# ------------------------------------------------------------------ streaming


def test_runner_streams_text_to_hooks():
    class Collect(TerminalHooks):
        def __init__(self):
            super().__init__(Console(file=io.StringIO()), input, {"agent": "", "tool": ""}, streaming=True)
            self.pieces = []

        def on_text(self, delta):
            self.pieces.append(delta)
            super().on_text(delta)

    hooks = Collect()
    result = Runner(build_agent_for_tests(), FakeLLM([reply("Hola, todo bien por aquí")]), hooks=hooks).run(
        [], "hola"
    )
    assert "".join(hooks.pieces) == "Hola, todo bien por aquí" and len(hooks.pieces) > 1
    assert result.final_output == "Hola, todo bien por aquí" and hooks.last_streamed


def build_agent_for_tests():
    from helpers import make_agent

    return make_agent()


def test_streamed_answer_is_not_printed_twice(context):
    terminal = make(context, [reply("Respuesta única en streaming")], ["hola", "/exit"], streaming=True)
    terminal.run()
    assert out(terminal).count("Respuesta única en streaming") == 1


def test_streaming_with_tool_calls_shows_final_answer(context):
    responses = [call("dns_lookup", domain="localhost"), reply("Respuesta final")]
    terminal = make(context, responses, ["consulta", "/exit"], streaming=True)
    terminal.run()
    text = out(terminal)
    assert text.count("Respuesta final") == 1 and "dns_lookup" in text


def test_litellm_client_streaming(monkeypatch):
    original = litellm.completion
    monkeypatch.setattr(
        litellm, "completion", functools.partial(original, mock_response="Hola desde el stream")
    )
    pieces: list[str] = []
    response = LiteLLMClient("gemini/gemini-2.5-flash").complete(
        [{"role": "user", "content": "x"}], [], on_text=pieces.append
    )
    assert "".join(pieces) == "Hola desde el stream" == response.content
    assert response.tool_calls == []


def test_error_after_text_was_shown_is_not_retried(monkeypatch):
    from litellm.types.utils import Delta, ModelResponseStream, StreamingChoices

    def broken_stream(**kwargs):
        def gen():
            yield ModelResponseStream(
                choices=[StreamingChoices(delta=Delta(content="Hola", role="assistant"), index=0)]
            )
            raise litellm.ServiceUnavailableError("se cortó", llm_provider="gemini", model="x")

        return gen()

    monkeypatch.setattr(litellm, "completion", broken_stream)
    client = LiteLLMClient("gemini/gemini-2.5-flash", retries=3)
    client._sleep = lambda s: pytest.fail("no debería reintentar después de mostrar texto")
    pieces: list[str] = []
    with pytest.raises(LLMError, match="se cortó"):
        client.complete([{"role": "user", "content": "x"}], [], on_text=pieces.append)
    assert pieces == ["Hola"]


def test_streaming_disabled_when_output_is_not_a_terminal(context):
    console = Console(file=io.StringIO(), force_terminal=False)
    terminal = Terminal(build_agent(context), FakeLLM([]), context, AuditLog("t"), console=console)
    assert terminal.hooks.streaming is False


# ------------------------------------------------------------- modo sin emojis


def test_plain_mode_has_no_emojis(context):
    responses = [call("dns_lookup", domain="localhost"), reply("ok")]
    terminal = make(
        context, responses, ["consulta", "/help", "/tools", "/status", "/history", "/exit"], plain=True
    )
    terminal.run()
    text = out(terminal)
    for emoji in ("🛡", "🤖", "👤", "🔧", "⚠", "✅", "❌", "📌", "📭", "💾", "📊"):
        assert emoji not in text, emoji
    assert "[OK]" in text  # /tools en ASCII


def test_plain_prompt_asks_model_not_to_use_emojis(context):
    plain = build_system_prompt(context.system, "redes privadas", plain=True)
    rich_prompt = build_system_prompt(context.system, "redes privadas")
    assert "NO uses emojis" in plain and "[CRÍTICO]" in plain and "🔴" not in plain
    assert "🔴" in rich_prompt


def test_wants_plain_detection():
    assert wants_plain(Console(file=io.StringIO()), forced=True)
    assert wants_plain(Console(file=io.StringIO(), legacy_windows=True))
    assert set(EMOJI) >= {"agent", "tool", "ok"}


def test_settings_stream_and_ascii_flags():
    s = Settings.from_env({"DUI_STREAM": "no", "DUI_ASCII": "1"})
    assert s.stream is False and s.ascii is True
    assert Settings.from_env({}).stream is True
    with pytest.raises(ValueError):
        Settings.from_env({"DUI_STREAM": "tal vez"})


# ------------------------------------------------- barra y autocompletado


def test_toolbar_shows_model_session_and_cost(context):
    terminal = make(context, [reply("hola")], ["pregunta de prueba", "/exit"])
    assert "sesión nueva" in terminal.toolbar()
    terminal.run()
    bar = terminal.toolbar()
    assert "fake/model" in bar and "pregunta de prueba" in bar and "15 tokens" in bar and "usuario" in bar


def test_command_completer_with_descriptions():
    completer = CommandCompleter()

    def suggest(text):
        return {c.text: c.display_meta_text for c in completer.get_completions(Document(text), None)}

    sessions = suggest("/se")
    assert "/sessions" in sessions and "/search" in sessions
    assert "Lista las sesiones" in sessions["/sessions"]
    assert "/sesiones" in suggest("/ses")  # alias en español
    assert suggest("hola") == {} and suggest("/load 2") == {}


def test_aliases_resolve_to_commands():
    assert canonical("/SALIR") == "/exit" and canonical("/buscar") == "/search" and canonical("/x") == "/x"


def test_help_is_grouped(context):
    terminal = make(context, [], ["/help", "/exit"])
    terminal.run()
    text = out(terminal)
    assert "General" in text and "Sesiones" in text and "Tab autocompleta" in text


def test_ascii_symbols_survive_rich_markup():
    """rich interpreta '[minúsculas]' como etiqueta de estilo y la borraría de la pantalla."""
    from rich.text import Text

    from dui.ui.symbols import ASCII

    for name, symbol in ASCII.items():
        assert Text.from_markup(symbol).plain == symbol, name
