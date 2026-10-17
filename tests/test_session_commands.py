"""Comandos de sesión en la terminal, con un modelo simulado y una base SQLite temporal."""

from __future__ import annotations

import io

import pytest
from helpers import FakeLLM, call, reply
from rich.console import Console

from dui.__main__ import build_agent, main
from dui.security import AuditLog
from dui.storage import SessionStore
from dui.ui import Terminal


class Scripted:
    def __init__(self) -> None:
        self.answers: list[str] = []

    def __call__(self, prompt: str = "") -> str:
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)


@pytest.fixture
def store(tmp_path):
    s = SessionStore(tmp_path / "dui.db")
    yield s
    s.close()


def make(context, store, responses, session_id="s_actual"):
    inputs = Scripted()
    console = Console(file=io.StringIO(), width=140, force_terminal=False)
    terminal = Terminal(
        build_agent(context),
        FakeLLM(responses),
        context,
        AuditLog(session_id, store),
        console=console,
        input_func=inputs,
        store=store,
    )
    terminal.console.input = inputs
    return terminal, inputs


def out(terminal) -> str:
    return terminal.console.file.getvalue()


def test_turns_are_autosaved_with_tool_messages(context, store):
    terminal, inputs = make(context, store, [call("dns_lookup", domain="localhost"), reply("Listo")])
    inputs.answers = ["consulta dns", "/exit"]
    terminal.run()
    messages = store.load_messages("s_actual")
    assert [m["role"] for m in messages] == ["user", "assistant", "tool", "assistant"]
    assert store.get("s_actual").title == "consulta dns"
    assert "Sesión guardada: s_actual" in out(terminal)


def test_resume_restores_full_context_for_the_model(context, store):
    first, inputs = make(context, store, [reply("Tu IP es 10.0.0.2")], session_id="s_vieja")
    inputs.answers = ["¿cuál es mi IP?", "/exit"]
    first.run()

    second, inputs = make(context, store, [reply("Sigue siendo 10.0.0.2")], session_id="s_nueva")
    inputs.answers = ["/resume", "¿y ahora?", "/exit"]
    second.run()
    sent = second.llm.calls[0]
    assert [m["content"] for m in sent[1:]] == ["¿cuál es mi IP?", "Tu IP es 10.0.0.2", "¿y ahora?"]
    # Lo nuevo se guarda en la sesión reanudada, no en una nueva.
    assert store.get("s_vieja").message_count == 4
    assert [s.id for s in store.list()] == ["s_vieja"]


def test_sessions_list_load_by_number_and_fragment(context, store):
    for sid, text in (("20261016_100000_aaa111", "uno"), ("20261016_110000_bbb222", "dos")):
        store.create(sid)
        store.append_messages(
            sid, [{"role": "user", "content": text}, {"role": "assistant", "content": "ok"}]
        )
    terminal, inputs = make(context, store, [])
    inputs.answers = ["/sessions", "/load 2", "/load bbb222", "/load nada", "/exit"]
    terminal.run()
    text = out(terminal)
    assert "Sesiones guardadas" in text and "aaa111" in text and "bbb222" in text
    assert terminal.session_id == "20261016_110000_bbb222"
    assert "No existe ninguna sesión 'nada'" in text


def test_search_rename_history_audit_and_export(context, store):
    terminal, inputs = make(context, store, [reply("El dominio es legítimo")])
    inputs.answers = [
        "revisa el dominio ejemplo.mx",
        "/rename Revisión de ejemplo.mx",
        "/search legítimo",
        "/history",
        "/audit",
        "/export",
        "/export json",
        "/export pdf",
        "/exit",
    ]
    terminal.run()
    text = out(terminal)
    assert store.get("s_actual").title == "Revisión de ejemplo.mx"
    assert "Resultados para 'legítimo'" in text and "«legítimo»" in text
    assert "👤 revisa el dominio ejemplo.mx" in text
    assert "Sin acciones registradas" in text
    exports = sorted(p.name for p in context.settings.exports_path.iterdir())
    assert exports == ["sesion_s_actual.json", "sesion_s_actual.md"]
    assert "Formato no soportado" in text


def test_delete_requires_confirmation_and_current_session_restarts(context, store):
    terminal, inputs = make(context, store, [reply("hola")])
    inputs.answers = ["hola", "/delete s_actual", "n", "/delete s_actual", "s", "/exit"]
    terminal.run()
    assert store.list() == []
    assert terminal.session_id != "s_actual" and terminal.history == []
    assert "Sesión conservada" in out(terminal) and "Sesión borrada" in out(terminal)


def test_new_session_keeps_previous_saved(context, store):
    terminal, inputs = make(context, store, [reply("a"), reply("b")])
    inputs.answers = ["primera", "/new", "segunda", "/exit"]
    terminal.run()
    assert len(store.list()) == 2
    assert "La anterior quedó guardada (s_actual)" in out(terminal)


def test_rename_empty_session_is_explained(context, store):
    terminal, inputs = make(context, store, [])
    inputs.answers = ["/rename Algo", "/exit"]
    terminal.run()
    assert "las sesiones vacías no se guardan" in out(terminal) and store.list() == []


def test_banner_offers_last_session(context, store):
    store.create("s_vieja")
    store.append_messages("s_vieja", [{"role": "user", "content": "escaneo de la red"}])
    terminal, inputs = make(context, store, [])
    inputs.answers = ["/exit"]
    terminal.run()
    assert "Última sesión: «escaneo de la red»" in out(terminal)


def test_cli_resume_flags(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DUI_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO("/exit\n"))
    assert main(["--session", "noexiste"]) == 1
    assert "No existe ninguna sesión" in capsys.readouterr().out
    assert main(["--resume"]) == 0
    assert "No hay sesiones guardadas" in capsys.readouterr().out
