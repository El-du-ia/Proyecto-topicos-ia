"""
Terminal interactiva de dui-IA (rich + prompt_toolkit; funciona en Windows, Linux y macOS).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agent import Agent, LLMClient, Runner, ToolContext, Usage
from ..agent.context import select_context
from ..compat import elevation_hint
from ..errors import LLMError, ToolError
from ..security import AuditLog
from ..storage import Session, SessionNotFound, SessionStore, audit_detail, new_session_id
from .commands import COMMAND_GROUPS, CommandCompleter, canonical
from .hooks import YES, TerminalHooks, answer_panel, format_args
from .symbols import symbols

LEGAL_NOTICE = (
    "Analizar redes o equipos que no te pertenecen puede ser ilegal. "
    "Asegúrate de tener permiso antes de continuar."
)


def _human_time(iso: str) -> str:
    """'2026-10-16T21:01:37' → 'hoy 21:01', 'ayer 09:15' o '03/10/2026 18:20'."""
    try:
        moment = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    days = (date.today() - moment.date()).days
    if days == 0:
        return f"hoy {moment:%H:%M}"
    if days == 1:
        return f"ayer {moment:%H:%M}"
    return f"{moment:%d/%m/%Y %H:%M}"


class Terminal:
    def __init__(
        self,
        agent: Agent,
        llm: LLMClient,
        context: ToolContext,
        audit: AuditLog,
        console: Console | None = None,
        input_func: Callable[[str], str] | None = None,
        store: SessionStore | None = None,
        plain: bool = False,
        streaming: bool | None = None,
    ) -> None:
        self.agent = agent
        self.llm = llm
        self.context = context
        self.audit = audit
        # Sin almacenamiento explícito (pruebas), las sesiones viven en memoria.
        self.store = store or audit.store or SessionStore(":memory:")
        self._listing: list[Session] = []  # última lista mostrada, para '/load 2'
        self.console = console or Console()
        self.sym = symbols(plain)
        if streaming is None:
            # Con la salida redirigida a un archivo no tiene sentido redibujar en vivo.
            streaming = context.settings.stream and self.console.is_terminal
        self._input = input_func or self._build_input()
        self.hooks = TerminalHooks(self.console, self._plain_input, self.sym, streaming=streaming)
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
        """prompt_toolkit si hay terminal real (historial, autocompletado, barra); si no, input()."""
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return self._plain_input
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory

        history_file = self.context.settings.data_dir / "input_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=CommandCompleter(),
            complete_while_typing=True,
            bottom_toolbar=self.toolbar,
        )
        prompt = [("ansicyan bold", f"dui-IA {self.sym['prompt']} ")]
        return lambda _prompt: session.prompt(prompt)

    def toolbar(self) -> str:
        """Barra inferior: modelo, sesión, consumo y privilegios."""
        sep = f" {self.sym['sep']} "
        saved = self._saved(self.session_id)
        title = saved.title if saved else "sesión nueva"
        if len(title) > 30:
            title = title[:29] + "…"
        u = self.usage
        privileges = "admin" if self.context.system.admin else "usuario"
        return " " + sep.join(
            [
                self.llm.model,
                title,
                f"{u.prompt_tokens + u.completion_tokens} tokens ${u.cost:.4f}",
                privileges,
                "/help",
            ]
        )

    # ------------------------------------------------------------------- bucle

    def run(self, resume: Session | None = None) -> None:
        if resume is not None:
            self._start_session(resume.id, self.store.load_messages(resume.id))
        self.show_banner()
        if resume is not None:
            self.load_session(resume)
        while True:
            try:
                text = self._input(f"dui-IA {self.sym['prompt']} ").strip()
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

    @property
    def session_id(self) -> str:
        return self.audit.session_id

    def ask(self, text: str) -> None:
        context = select_context(self.history, max_messages=self.context.settings.max_history)
        try:
            result = self.runner.run(context, text)
        except LLMError as exc:
            self.console.print(Panel(str(exc), title="Error del modelo", border_style="red"))
            return
        except KeyboardInterrupt:
            self.hooks.stop()
            self.console.print("[yellow]Petición cancelada.[/]")
            return
        self.history.extend(result.new_messages)
        self.usage = self.usage + result.usage
        # Autoguardado: el turno completo (pregunta, herramientas, respuesta) se guarda de una vez.
        self.store.create(self.session_id, self.llm.model)
        self.store.append_messages(self.session_id, result.new_messages, model=self.llm.model)
        if result.final_output.strip() and not self.hooks.last_streamed:
            self.console.print(answer_panel(result.final_output, self.sym))

    # ---------------------------------------------------------------- comandos

    def handle_command(self, text: str) -> bool:
        """Ejecuta un comando. Devuelve False si hay que salir."""
        name, _, arg = text.partition(" ")
        name = canonical(name)
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
            "/sessions": lambda _a: self.cmd_sessions(),
            "/resume": lambda _a: self.cmd_resume(),
            "/load": self.cmd_load,
            "/search": self.cmd_search,
            "/history": lambda _a: self.cmd_history(),
            "/audit": lambda _a: self.cmd_audit(),
            "/rename": self.cmd_rename,
            "/export": self.cmd_export,
            "/delete": self.cmd_delete,
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
        previous = self.session_id
        self._start_session(new_session_id())
        saved = self._saved(previous)
        note = f" La anterior quedó guardada ({previous})." if saved else ""
        self.console.print(f"[green]Sesión nueva.{note}[/]")

    # ---------------------------------------------------------------- sesiones

    def _start_session(self, session_id: str, history: list[dict[str, Any]] | None = None) -> None:
        self.audit.switch(session_id)
        self.history = list(history or [])
        self.usage = Usage()

    def _saved(self, session_id: str) -> Session | None:
        try:
            session = self.store.get(session_id)
        except SessionNotFound:
            return None
        return session if session.message_count else None

    def _resolve(self, ref: str) -> Session | None:
        """'/load 2' usa la última lista mostrada; si no, se busca por ID o fragmento de ID."""
        ref = ref.strip()
        if not ref:
            self.console.print("[red]Indica una sesión: número de /sessions o parte de su ID.[/]")
            return None
        if ref.isdigit() and 1 <= int(ref) <= len(self._listing):
            return self._listing[int(ref) - 1]
        try:
            return self.store.find(ref)
        except SessionNotFound as exc:
            self.console.print(f"[red]{exc.args[0] if exc.args else 'Sesión no encontrada'}[/]")
            return None

    def load_session(self, session: Session) -> None:
        self._start_session(session.id, self.store.load_messages(session.id))
        self.console.print(
            f"[green]{self.sym['loaded']} Sesión cargada:[/] [bold]{session.title or session.id}[/] "
            f"{self.sym['sep']} {session.message_count} mensajes {self.sym['sep']} "
            f"última actividad {_human_time(session.updated_at)}"
        )
        exchanges = [m for m in self.history if m.get("role") in ("user", "assistant") and m.get("content")]
        if exchanges:
            self.console.print("[dim]Últimos mensajes:[/]")
            for message in exchanges[-4:]:
                self._print_message(message, limit=160)
        self.console.print("[dim]Puedes continuar la conversación donde la dejaste.[/]\n")

    def _session_table(self, sessions: list[Session], title: str, snippets: list[str] | None = None) -> None:
        self._listing = sessions
        table = Table(title=title)
        table.add_column("#", justify="right")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Título", max_width=45, no_wrap=True, overflow="ellipsis")
        table.add_column("Mensajes", justify="right")
        table.add_column("Última actividad")
        if snippets:
            table.add_column("Coincidencia")
        for index, session in enumerate(sessions, 1):
            marker = f" {self.sym['current']} actual" if session.id == self.session_id else ""
            row = [
                str(index),
                session.id,
                (session.title or "(sin título)") + marker,
                str(session.message_count),
                _human_time(session.updated_at),
            ]
            if snippets:
                row.append(snippets[index - 1])
            table.add_row(*row)
        self.console.print(table)
        self.console.print("[dim]Usa '/load <#>' para continuar una sesión.[/]")

    def _empty(self, message: str) -> None:
        self.console.print(f"{self.sym['empty']} {message}")

    def cmd_sessions(self) -> None:
        sessions = self.store.list(limit=20)
        if not sessions:
            self._empty("Todavía no hay sesiones guardadas.")
            return
        self._session_table(sessions, "Sesiones guardadas")

    def cmd_resume(self) -> None:
        session = self.store.latest(exclude=self.session_id)
        if session is None:
            self._empty("No hay otra sesión guardada para continuar.")
            return
        self.load_session(session)

    def cmd_load(self, ref: str) -> None:
        session = self._resolve(ref)
        if session is not None:
            self.load_session(session)

    def cmd_search(self, query: str) -> None:
        if not query:
            self.console.print("[red]Uso: /search <texto>[/]")
            return
        hits = self.store.search(query)
        if not hits:
            self._empty(f"No se encontró '{query}' en ninguna sesión.")
            return
        self._session_table(
            [h.session for h in hits], f"Resultados para '{query}'", [h.snippet for h in hits]
        )

    def cmd_history(self) -> None:
        if not self.history:
            self._empty("Esta sesión todavía no tiene mensajes.")
            return
        for message in self.history:
            self._print_message(message)

    def _print_message(self, message: dict[str, Any], limit: int | None = None) -> None:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if limit and len(content) > limit:
            content = content[:limit].rstrip() + "…"
        if role == "user":
            self.console.print(Text(f"{self.sym['user']} ", style="bold") + Text(content))
        elif role == "assistant":
            for call in message.get("tool_calls") or []:
                fn = call.get("function", {})
                self.console.print(f"[dim]   {self.sym['tool']} {fn.get('name')}({fn.get('arguments')})[/]")
            if content:
                self.console.print(Text(f"{self.sym['agent']} ", style="bold cyan") + Text(content))
        elif role == "tool" and limit is None:
            first = content.splitlines()[0] if content else ""
            self.console.print(f"[dim]   {self.sym['result']} {message.get('name')}: {first[:100]}[/]")

    def cmd_audit(self) -> None:
        events = self.audit.events
        if not events:
            self._empty("Sin acciones registradas en esta sesión.")
            return
        table = Table(title=f"Auditoría {self.sym['sep']} {self.session_id}")
        for column in ("Hora", "Evento", "Herramienta", "Argumentos", "Detalle"):
            table.add_column(column)
        for e in events:
            args = e.get("arguments")
            table.add_row(
                e["timestamp"][11:19],
                e["event"],
                e.get("tool", ""),
                format_args(args) if isinstance(args, dict) else "",
                audit_detail(e),
            )
        self.console.print(table)

    def cmd_rename(self, title: str) -> None:
        if not title:
            self.console.print("[red]Uso: /rename <título nuevo>[/]")
            return
        if not self._saved(self.session_id):
            self._empty("Escribe algo primero: las sesiones vacías no se guardan.")
            return
        self.store.rename(self.session_id, title)
        self.console.print(f"[green]Sesión renombrada: {title}[/]")

    def cmd_export(self, arg: str) -> None:
        fmt = (arg or "md").lower().lstrip(".")
        if fmt not in ("md", "markdown", "json"):
            self.console.print("[red]Formato no soportado. Usa '/export' (Markdown) o '/export json'.[/]")
            return
        if not self._saved(self.session_id):
            self._empty("Esta sesión todavía no tiene mensajes para exportar.")
            return
        is_json = fmt == "json"
        text = (
            self.store.export_json(self.session_id)
            if is_json
            else self.store.export_markdown(self.session_id)
        )
        directory = self.context.settings.exports_path
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"sesion_{self.session_id}.{'json' if is_json else 'md'}"
        path.write_text(text, encoding="utf-8")
        self.console.print(f"[green]Sesión exportada:[/] {path.resolve()}")

    def cmd_delete(self, ref: str) -> None:
        session = self._resolve(ref)
        if session is None:
            return
        answer = self._plain_input(
            f"¿Borrar la sesión '{session.title or session.id}' y su auditoría? No se puede deshacer [s/N]: "
        )
        if answer.strip().lower() not in YES:
            self.console.print("Sesión conservada.")
            return
        self.store.delete(session.id)
        self._listing = [s for s in self._listing if s.id != session.id]
        if session.id == self.session_id:
            self._start_session(new_session_id())
            self.console.print("[green]Sesión borrada. Empezaste una sesión nueva.[/]")
        else:
            self.console.print("[green]Sesión borrada.[/]")

    # ---------------------------------------------------------------- pantallas

    def show_banner(self) -> None:
        system = self.context.system
        sep = self.sym["sep"]
        info = Table.grid(padding=(0, 1))
        info.add_row("[bold]Modelo:[/]", self.llm.model)
        info.add_row(
            "[bold]Sistema:[/]", f"{system.os_label} {system.os_version} {sep} usuario {system.user}"
        )
        privileges = "[green]administrador/root[/]" if system.admin else "[yellow]usuario normal[/]"
        info.add_row("[bold]Privilegios:[/]", privileges)
        info.add_row("[bold]Alcance:[/]", self.context.scope.describe())
        self.console.print(
            Panel(
                info,
                title=f"{self.sym['app']} dui-IA {sep} Agente de ciberseguridad".strip(),
                border_style="cyan",
                title_align="left",
            )
        )
        if not system.admin:
            self.console.print(f"[dim]Algunas herramientas necesitan privilegios. {elevation_hint()}[/]")
        self.console.print(f"[yellow]{self.sym['note']} {LEGAL_NOTICE}[/]")
        previous = self.store.latest(exclude=self.session_id)
        if previous is not None and not self.history:
            self.console.print(
                f"[dim]Última sesión: «{previous.title}» ({_human_time(previous.updated_at)}). "
                "Escribe /resume para continuarla.[/]"
            )
        self.console.print("[dim]Escribe tu pregunta, /help para ver comandos o /exit para salir.[/]\n")

    def show_help(self) -> None:
        for group, commands in COMMAND_GROUPS.items():
            table = Table(title=group, title_justify="left", show_header=False, box=None, padding=(0, 2))
            for command, description in commands.items():
                table.add_row(f"[cyan]{command}[/]", description)
            self.console.print(table)
        b = self.sym["bullet"]
        self.console.print(
            "\n[bold]Ejemplos:[/]\n"
            f"  {b} ¿Quién registró el dominio example.com?\n"
            f"  {b} ¿Qué servidores de correo usa gmail.com?\n"
            f"  {b} ¿A quién pertenece la IP 8.8.8.8?\n"
            "\n[dim]Tab autocompleta comandos · ↑/↓ recorre lo que escribiste · "
            "Ctrl+C cancela una respuesta · Ctrl+D sale[/]"
        )

    def show_tools(self) -> None:
        table = Table(title="Herramientas")
        table.add_column("Herramienta", style="cyan")
        table.add_column("Categoría")
        table.add_column("Confirmación")
        table.add_column("Disponible")
        for t in self.agent.tools:
            availability = t.availability()
            status = self.sym["ok"] if availability.ok else f"{self.sym['fail']} {availability.detail}"
            table.add_row(t.name, t.category, "sí" if t.sensitive else "no", status)
        self.console.print(table)

    def show_status(self) -> None:
        system = self.context.system
        sep = self.sym["sep"]
        summary = self.audit.summary()
        table = Table.grid(padding=(0, 1))
        saved = self._saved(self.session_id)
        table.add_row(
            "[bold]Sesión:[/]", self.session_id + (f" {sep} {saved.title}" if saved else " (nueva)")
        )
        table.add_row("[bold]Modelo:[/]", self.llm.model)
        table.add_row(
            "[bold]Sistema:[/]", f"{system.os_label} {system.os_version} {sep} Python {system.python}"
        )
        table.add_row("[bold]Privilegios:[/]", "administrador/root" if system.admin else "usuario normal")
        table.add_row("[bold]Mensajes en contexto:[/]", str(len(self.history)))
        table.add_row("[bold]Acciones ejecutadas:[/]", str(summary["total_actions"]))
        table.add_row(
            "[bold]Confirmaciones:[/]",
            f"{summary['approvals']} aprobadas {sep} {summary['rejections']} rechazadas",
        )
        table.add_row("[bold]Streaming:[/]", "activado" if self.hooks.streaming else "desactivado")
        table.add_row("[bold]Datos:[/]", str(self.context.settings.data_dir))
        table.add_row("[bold]Base de datos:[/]", str(self.store.path))
        self.console.print(Panel(table, title="Estado", title_align="left"))

    def show_cost(self) -> None:
        u = self.usage
        sep = self.sym["sep"]
        self.console.print(
            f"Tokens: {u.prompt_tokens} de entrada {sep} {u.completion_tokens} de salida {sep} "
            f"costo estimado: ${u.cost:.6f}"
        )

    def show_goodbye(self) -> None:
        summary = self.audit.summary()
        if summary["total_actions"]:
            self.console.print(
                f"\n{self.sym['stats']} Acciones realizadas: {summary['total_actions']} {self.sym['sep']} "
                f"herramientas: {', '.join(summary['tools_used'])}"
            )
        if self._saved(self.session_id):
            self.console.print(
                f"{self.sym['saved']} Sesión guardada: {self.session_id} {self.sym['sep']} "
                "retómala con 'dui-ia --resume' o '/load'"
            )
        self.store.delete_empty()
        self.console.print("[cyan]¡Hasta pronto! Gracias por usar dui-IA.[/]")
