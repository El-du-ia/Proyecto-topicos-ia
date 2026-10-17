"""
Punto de entrada de dui-IA.

    uv run dui-ia                 # terminal interactiva
    uv run dui-ia --check         # diagnóstico del equipo y de la configuración
    uv run dui-ia --model ollama_chat/llama3.1 --api-base http://localhost:11434
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from . import __version__
from .agent import Agent, LiteLLMClient, ToolContext, ToolRegistry
from .agent.prompts import build_system_prompt
from .compat import system_info
from .config import Settings
from .security import AuditLog, Scope, ScopeError
from .tools import default_tools

LOCAL_PROVIDERS = {"ollama", "ollama_chat", "lm_studio", "hosted_vllm", "llamafile"}


def _fix_stdio_encoding() -> None:
    """En Windows la salida redirigida usa cp1252 y rompe acentos y emojis."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and (stream.encoding or "").lower() != "utf-8":
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def new_session_id() -> str:
    return f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"


def build_context(settings: Settings) -> ToolContext:
    return ToolContext(settings=settings, scope=Scope(settings.scope), system=system_info())


def build_agent(context: ToolContext) -> Agent:
    return Agent(
        name="dui-IA",
        instructions=lambda: build_system_prompt(context.system, context.scope.describe()),
        tools=ToolRegistry(default_tools()),
    )


def build_llm(settings: Settings) -> LiteLLMClient:
    return LiteLLMClient(settings.model, api_base=settings.api_base, temperature=settings.temperature)


def run_check(settings: Settings, console: Console) -> int:
    context = build_context(settings)
    agent = build_agent(context)
    system = context.system

    console.print(f"[bold]dui-IA {__version__}[/]")
    console.print(f"Sistema: {system.os_label} {system.os_version} · Python {system.python}")
    console.print(
        f"Usuario: {system.user} · Privilegios: {'administrador/root' if system.admin else 'normal'}"
    )
    console.print(f"Datos: {settings.data_dir}")
    console.print(f"Alcance: {context.scope.describe()}")

    provider = settings.model.split("/", 1)[0]
    console.print(f"Modelo: {settings.model}" + (f" ({settings.api_base})" if settings.api_base else ""))
    if provider in LOCAL_PROVIDERS:
        console.print("  [green]Modelo local: no requiere API key[/]")
    else:
        try:
            import litellm

            env = litellm.validate_environment(model=settings.model)
            if env.get("keys_in_environment"):
                console.print("  [green]API key encontrada[/]")
            else:
                console.print(f"  [yellow]Falta configurar: {', '.join(env.get('missing_keys', []))}[/]")
        except Exception as exc:
            console.print(f"  [yellow]No se pudo verificar la API key: {exc}[/]")

    table = Table(title="Herramientas")
    table.add_column("Herramienta")
    table.add_column("Confirmación")
    table.add_column("Disponible")
    for t in agent.tools:
        availability = t.availability()
        table.add_row(
            t.name, "sí" if t.sensitive else "no", "✅" if availability.ok else f"❌ {availability.detail}"
        )
    console.print(table)
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="dui-ia", description="Agente inteligente de ciberseguridad")
    parser.add_argument("--version", action="version", version=f"dui-IA {__version__}")
    parser.add_argument("--check", action="store_true", help="diagnóstico del equipo y la configuración")
    parser.add_argument(
        "--model", help="modelo LiteLLM, p. ej. gemini/gemini-2.5-flash u ollama_chat/llama3.1"
    )
    parser.add_argument("--api-base", help="URL del servidor del modelo (para modelos locales)")
    parser.add_argument(
        "--scope", action="append", default=[], help="agrega un objetivo al alcance permitido"
    )
    parser.add_argument("--data-dir", type=Path, help="carpeta para auditoría, reportes e historial")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _fix_stdio_encoding()
    args = parse_args(argv)
    console = Console()
    try:
        settings = Settings.from_env()
        if args.model:
            settings.model = args.model
        if args.api_base:
            settings.api_base = args.api_base
        if args.data_dir:
            settings.data_dir = args.data_dir
        settings.scope.extend(args.scope)
        context = build_context(settings)  # valida el alcance configurado
    except (ValueError, ScopeError) as exc:
        console.print(f"[red]Configuración inválida:[/] {exc}")
        return 2

    if args.check:
        return run_check(settings, console)

    from .ui import Terminal

    session_id = new_session_id()
    audit = AuditLog(session_id, settings.audit_path / f"{session_id}.jsonl")
    Terminal(build_agent(context), build_llm(settings), context, audit, console=console).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
