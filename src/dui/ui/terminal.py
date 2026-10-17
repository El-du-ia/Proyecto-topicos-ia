"""
Terminal interactiva de dui-IA (rich + prompt_toolkit; funciona en Windows, Linux y macOS).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agent import Agent, LLMClient, LLMResponse, RunHooks, Runner, Tool, ToolContext, Usage
from ..compat import elevation_hint
from ..errors import LLMError, ToolError
from ..security import AuditLog

LEGAL_NOTICE = (
    "📌 Analizar redes o equipos que no te pertenecen puede ser ilegal. "
    "Asegúrate de tener permiso antes de continuar."
)

COMMANDS: dict[str, str] = {
    "/help": "Muestra esta ayuda",
    "/tools": "Lista las herramientas y si están disponibles en este equipo",
    "/scope": "Muestra el alcance permitido ('/scope add <objetivo>' para ampliarlo)",
    "/model": "Muestra o cambia el modelo ('/model ollama_chat/llama3.1')",
    "/status": "Estado del sistema, del modelo y de la sesión",
    "/cost": "Tokens y costo acumulado de la sesión",
    "/new": "Empieza una conversación nueva (olvida el contexto actual)",
    "/clear": "Limpia la pantalla",
    "/exit": "Salir",
}
ALIASES = {
    "/ayuda": "/help",
    "/herramientas": "/tools",
    "/alcance": "/scope",
    "/modelo": "/model",
    "/estado": "/status",
    "/costo": "/cost",
    "/nueva": "/new",
    "/limpiar": "/clear",
    "/quit": "/exit",
    "/salir": "/exit",
}

YES = {"s", "si", "sí", "y", "yes"}
NO = {"n", "no", ""}


def _format_args(arguments: dict[str, Any]) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in arguments.items())


class TerminalHooks(RunHooks):
    def __init__(self, console: Console, ask: Callable[[str], str]) -> None:
        self.console = console
        self.ask = ask
        self._status: Any = None

    def _start(self, message: str) -> None:
        self.stop()
        self._status = self.console.status(message, spinner="dots")
        self._status.start()

    def stop(self) -> None:
        if self._status is not None:
            self._status.stop()
            self._status = None

    def on_llm_start(self) -> None:
        self._start("[cyan]Pensando…")

    def on_llm_end(self, response: LLMResponse) -> None:
        self.stop()
        # Texto que el modelo escribe antes de usar una herramienta (p. ej. "Voy a escanear...").
        if response.tool_calls and response.content and response.content.strip():
            self.console.print(Markdown(response.content.strip()), style="dim")

    def on_llm_error(self) -> None:
        self.stop()

    def on_tool_start(self, tool: Tool, arguments: dict[str, Any]) -> None:
        self._start(f"[yellow]Ejecutando {tool.name}…")

    def on_tool_end(self, tool: Tool, arguments: dict[str, Any], result: str, ok: bool) -> None:
        self.stop()
        lines = result.splitlines()
        preview = "\n".join(lines[:15]) + (f"\n… ({len(lines) - 15} líneas más)" if len(lines) > 15 else "")
        self.console.print(
            Panel(
                Text(preview),
                title=f"🔧 {tool.name}({_format_args(arguments)})",
                title_align="left",
                border_style="green" if ok else "red",
                style="dim",
            )
        )

    def confirm(self, tool: Tool, arguments: dict[str, Any]) -> bool:
        self.stop()
        body = Table.grid(padding=(0, 1))
        body.add_row("[bold]Acción:[/]", tool.description.splitlines()[0])
        body.add_row("[bold]Herramienta:[/]", tool.name)
        for key, value in arguments.items():
            body.add_row(f"[bold]{key}:[/]", str(value))
        if tool.risks:
            body.add_row("[bold]Riesgos:[/]", "\n".join(f"• {r}" for r in tool.risks))
        body.add_row("", "[dim]Tu decisión quedará registrada en la auditoría.[/]")
        self.console.print(
            Panel(body, title="⚠️  CONFIRMACIÓN REQUERIDA", border_style="yellow", title_align="left")
        )
        while True:
            try:
                answer = self.ask("¿Deseas continuar? [s/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            if answer in YES:
                self.console.print("[green]✅ Acción aprobada[/]")
                return True
            if answer in NO:
                self.console.print("[red]❌ Acción cancelada[/]")
                return False
            self.console.print("Responde 's' para sí o 'n' para no.")


class Terminal:
    def __init__(
        self,
        agent: Agent,
        llm: LLMClient,
        context: ToolContext,
        audit: AuditLog,
        console: Console | None = None,
        input_func: Callable[[str], str] | None = None,
    ) -> None:
        self.agent = agent
        self.llm = llm
        self.context = context
        self.audit = audit
        self.console = console or Console()
        self._input = input_func or self._build_input()
        self.hooks = TerminalHooks(self.console, self._plain_input)
        self.runner = Runner(
            agent,
            llm,
            context=context,
            hooks=self.hooks,
            audit=audit,
            max_turns=context.settings.max_turns,
        )
        self.history: list[dict[str, Any]] = []
        self.usage = Usage()

    # ------------------------------------------------------------------ entrada

    def _plain_input(self, prompt: str) -> str:
        return self.console.input(prompt)

    def _build_input(self) -> Callable[[str], str]:
        """prompt_toolkit si hay terminal real (historial y autocompletado); si no, input()."""
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return self._plain_input
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import FileHistory

        history_file = self.context.settings.data_dir / "input_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=WordCompleter([*COMMANDS, *ALIASES], sentence=True),
            complete_while_typing=True,
        )
        return lambda _prompt: session.prompt(HTML("<ansicyan><b>dui-IA › </b></ansicyan>"))

    # ------------------------------------------------------------------- bucle

    def run(self) -> None:
        self.show_banner()
        while True:
            try:
                text = self._input("dui-IA › ").strip()
            except KeyboardInterrupt:
                continue  # Ctrl+C en el prompt solo limpia la línea
            except EOFError:
                break
            if not text:
                continue
            if text.startswith("/"):
                if not self.handle_command(text):
                    break
                continue
            self.ask(text)
        self.show_goodbye()

    def ask(self, text: str) -> None:
        try:
            result = self.runner.run(self.history, text)
        except LLMError as exc:
            self.console.print(Panel(str(exc), title="Error del modelo", border_style="red"))
            return
        except KeyboardInterrupt:
            self.hooks.stop()
            self.console.print("[yellow]Petición cancelada.[/]")
            return
        self.history.extend(result.new_messages)
        self.usage = self.usage + result.usage
        if result.final_output.strip():
            self.console.print(
                Panel(
                    Markdown(result.final_output), title="🤖 dui-IA", title_align="left", border_style="cyan"
                )
            )

    # ---------------------------------------------------------------- comandos

    def handle_command(self, text: str) -> bool:
        """Ejecuta un comando. Devuelve False si hay que salir."""
        name, _, arg = text.partition(" ")
        name = ALIASES.get(name.lower(), name.lower())
        arg = arg.strip()
        if name == "/exit":
            return False
        handlers: dict[str, Callable[[str], None]] = {
            "/help": lambda _a: self.show_help(),
            "/tools": lambda _a: self.show_tools(),
            "/scope": self.cmd_scope,
            "/model": self.cmd_model,
            "/status": lambda _a: self.show_status(),
            "/cost": lambda _a: self.show_cost(),
            "/new": lambda _a: self.cmd_new(),
            "/clear": lambda _a: self.console.clear(),
        }
        handler = handlers.get(name)
        if handler is None:
            self.console.print(f"[red]Comando desconocido: {name}[/]. Escribe /help.")
        else:
            handler(arg)
        return True

    def cmd_scope(self, arg: str) -> None:
        scope = self.context.scope
        action, _, target = arg.partition(" ")
        if action.lower() in ("add", "agregar") and target.strip():
            target = target.strip()
            self.console.print(
                f"[yellow]Vas a permitir análisis activos (escaneos) sobre [bold]{target}[/].[/]"
            )
            answer = self._plain_input("¿Confirmas que tienes autorización para analizarlo? [s/N]: ")
            if answer.strip().lower() not in YES:
                self.console.print("Alcance sin cambios.")
                return
            try:
                scope.add(target)
            except ToolError as exc:
                self.console.print(f"[red]{exc}[/]")
                return
            self.audit.record("scope_added", target=target)
            self.console.print(f"[green]Agregado. Alcance actual: {scope.describe()}[/]")
            return
        self.console.print(f"Alcance permitido: [bold]{scope.describe()}[/]")
        self.console.print("[dim]Usa '/scope add <ip|red|dominio>' para ampliarlo.[/]")

    def cmd_model(self, arg: str) -> None:
        if arg:
            self.llm.model = arg
            self.console.print(f"[green]Modelo cambiado a {arg}[/]")
        else:
            self.console.print(f"Modelo actual: [bold]{self.llm.model}[/]")

    def cmd_new(self) -> None:
        self.history.clear()
        self.console.print("[green]Conversación nueva. El contexto anterior se olvidó.[/]")

    # ---------------------------------------------------------------- pantallas

    def show_banner(self) -> None:
        system = self.context.system
        info = Table.grid(padding=(0, 1))
        info.add_row("[bold]Modelo:[/]", self.llm.model)
        info.add_row("[bold]Sistema:[/]", f"{system.os_label} {system.os_version} · usuario {system.user}")
        privileges = "[green]administrador/root[/]" if system.admin else "[yellow]usuario normal[/]"
        info.add_row("[bold]Privilegios:[/]", privileges)
        info.add_row("[bold]Alcance:[/]", self.context.scope.describe())
        self.console.print(
            Panel(info, title="🛡️  dui-IA · Agente de ciberseguridad", border_style="cyan", title_align="left")
        )
        if not system.admin:
            self.console.print(f"[dim]Algunas herramientas necesitan privilegios. {elevation_hint()}[/]")
        self.console.print(f"[yellow]{LEGAL_NOTICE}[/]")
        self.console.print("[dim]Escribe tu pregunta, /help para ver comandos o /exit para salir.[/]\n")

    def show_help(self) -> None:
        table = Table(title="Comandos", show_header=False, box=None)
        for command, description in COMMANDS.items():
            table.add_row(f"[cyan]{command}[/]", description)
        self.console.print(table)
        self.console.print(
            "\n[bold]Ejemplos:[/]\n"
            "  • ¿Quién registró el dominio example.com?\n"
            "  • ¿Qué servidores de correo usa gmail.com?\n"
            "  • ¿A quién pertenece la IP 8.8.8.8?\n"
        )

    def show_tools(self) -> None:
        table = Table(title="Herramientas")
        table.add_column("Herramienta", style="cyan")
        table.add_column("Categoría")
        table.add_column("Confirmación")
        table.add_column("Disponible")
        for t in self.agent.tools:
            availability = t.availability()
            status = "✅" if availability.ok else f"❌ {availability.detail}"
            table.add_row(t.name, t.category, "sí" if t.sensitive else "no", status)
        self.console.print(table)

    def show_status(self) -> None:
        system = self.context.system
        summary = self.audit.summary()
        table = Table.grid(padding=(0, 1))
        table.add_row("[bold]Sesión:[/]", self.audit.session_id)
        table.add_row("[bold]Modelo:[/]", self.llm.model)
        table.add_row("[bold]Sistema:[/]", f"{system.os_label} {system.os_version} · Python {system.python}")
        table.add_row("[bold]Privilegios:[/]", "administrador/root" if system.admin else "usuario normal")
        table.add_row("[bold]Mensajes en contexto:[/]", str(len(self.history)))
        table.add_row("[bold]Acciones ejecutadas:[/]", str(summary["total_actions"]))
        table.add_row(
            "[bold]Confirmaciones:[/]",
            f"{summary['approvals']} aprobadas · {summary['rejections']} rechazadas",
        )
        table.add_row("[bold]Datos:[/]", str(self.context.settings.data_dir))
        if self.audit.path:
            table.add_row("[bold]Auditoría:[/]", str(self.audit.path))
        self.console.print(Panel(table, title="Estado", title_align="left"))

    def show_cost(self) -> None:
        u = self.usage
        self.console.print(
            f"Tokens: {u.prompt_tokens} de entrada · {u.completion_tokens} de salida · "
            f"costo estimado: ${u.cost:.6f}"
        )

    def show_goodbye(self) -> None:
        summary = self.audit.summary()
        if summary["total_actions"]:
            self.console.print(
                f"\n📊 Acciones realizadas: {summary['total_actions']} · "
                f"herramientas: {', '.join(summary['tools_used'])}"
            )
            if self.audit.path:
                self.console.print(f"📁 Auditoría: {self.audit.path}")
        self.console.print("[cyan]¡Hasta pronto! Gracias por usar dui-IA.[/]")
