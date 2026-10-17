"""
Terminal interactiva de dui-IA (rich + prompt_toolkit; funciona en Windows, Linux y macOS).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agent import Agent, LLMClient, LLMResponse, RunHooks, Runner, Tool, ToolContext, Usage
from ..agent.context import select_context
from ..compat import elevation_hint
from ..errors import LLMError, ToolError
from ..security import AuditLog
from ..storage import Session, SessionNotFound, SessionStore, audit_detail, new_session_id

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
    "/sessions": "Lista las sesiones guardadas",
    "/resume": "Continúa la sesión más reciente",
    "/load": "Carga una sesión: '/load 2' (número de la lista) o '/load 47437b' (parte del ID)",
    "/search": "Busca en todas las conversaciones: '/search puertos abiertos'",
    "/history": "Muestra la conversación actual",
    "/audit": "Muestra la auditoría de la sesión actual",
    "/rename": "Cambia el título de la sesión actual: '/rename Red de la oficina'",
    "/export": "Exporta la sesión actual: '/export' (Markdown) o '/export json'",
    "/delete": "Borra una sesión: '/delete 2' o '/delete 47437b'",
    "/new": "Empieza una sesión nueva (la actual queda guardada)",
    "/clear": "Limpia la pantalla",
    "/exit": "Salir",
}
ALIASES = {
    "/sesiones": "/sessions",
    "/continuar": "/resume",
    "/cargar": "/load",
    "/buscar": "/search",
    "/historial": "/history",
    "/auditoria": "/audit",
    "/auditoría": "/audit",
    "/renombrar": "/rename",
    "/exportar": "/export",
    "/borrar": "/delete",
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
        store: SessionStore | None = None,
    ) -> None:
        self.agent = agent
        self.llm = llm
        self.context = context
        self.audit = audit
        # Sin almacenamiento explícito (pruebas), las sesiones viven en memoria.
        self.store = store or audit.store or SessionStore(":memory:")
        self._listing: list[Session] = []  # última lista mostrada, para '/load 2'
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

    def run(self, resume: Session | None = None) -> None:
        if resume is not None:
            self._start_session(resume.id, self.store.load_messages(resume.id))
        self.show_banner()
        if resume is not None:
            self.load_session(resume)
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
            f"[green]✓ Sesión cargada:[/] [bold]{session.title or session.id}[/] "
            f"· {session.message_count} mensajes · última actividad {_human_time(session.updated_at)}"
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
            marker = " ◀ actual" if session.id == self.session_id else ""
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

    def cmd_sessions(self) -> None:
        sessions = self.store.list(limit=20)
        if not sessions:
            self.console.print("📭 Todavía no hay sesiones guardadas.")
            return
        self._session_table(sessions, "Sesiones guardadas")

    def cmd_resume(self) -> None:
        session = self.store.latest(exclude=self.session_id)
        if session is None:
            self.console.print("📭 No hay otra sesión guardada para continuar.")
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
            self.console.print(f"📭 No se encontró '{query}' en ninguna sesión.")
            return
        self._session_table(
            [h.session for h in hits], f"Resultados para '{query}'", [h.snippet for h in hits]
        )

    def cmd_history(self) -> None:
        if not self.history:
            self.console.print("📭 Esta sesión todavía no tiene mensajes.")
            return
        for message in self.history:
            self._print_message(message)

    def _print_message(self, message: dict[str, Any], limit: int | None = None) -> None:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if limit and len(content) > limit:
            content = content[:limit].rstrip() + "…"
        if role == "user":
            self.console.print(Text("👤 ", style="bold") + Text(content))
        elif role == "assistant":
            for call in message.get("tool_calls") or []:
                fn = call.get("function", {})
                self.console.print(f"[dim]   🔧 {fn.get('name')}({fn.get('arguments')})[/]")
            if content:
                self.console.print(Text("🤖 ", style="bold cyan") + Text(content))
        elif role == "tool" and limit is None:
            first = content.splitlines()[0] if content else ""
            self.console.print(f"[dim]   ↳ {message.get('name')}: {first[:100]}[/]")

    def cmd_audit(self) -> None:
        events = self.audit.events
        if not events:
            self.console.print("📭 Sin acciones registradas en esta sesión.")
            return
        table = Table(title=f"Auditoría · {self.session_id}")
        for column in ("Hora", "Evento", "Herramienta", "Argumentos", "Detalle"):
            table.add_column(column)
        for e in events:
            args = e.get("arguments")
            table.add_row(
                e["timestamp"][11:19],
                e["event"],
                e.get("tool", ""),
                _format_args(args) if isinstance(args, dict) else "",
                audit_detail(e),
            )
        self.console.print(table)

    def cmd_rename(self, title: str) -> None:
        if not title:
            self.console.print("[red]Uso: /rename <título nuevo>[/]")
            return
        if not self._saved(self.session_id):
            self.console.print("📭 Escribe algo primero: las sesiones vacías no se guardan.")
            return
        self.store.rename(self.session_id, title)
        self.console.print(f"[green]Sesión renombrada: {title}[/]")

    def cmd_export(self, arg: str) -> None:
        fmt = (arg or "md").lower().lstrip(".")
        if fmt not in ("md", "markdown", "json"):
            self.console.print("[red]Formato no soportado. Usa '/export' (Markdown) o '/export json'.[/]")
            return
        if not self._saved(self.session_id):
            self.console.print("📭 Esta sesión todavía no tiene mensajes para exportar.")
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
        previous = self.store.latest(exclude=self.session_id)
        if previous is not None and not self.history:
            self.console.print(
                f"[dim]Última sesión: «{previous.title}» ({_human_time(previous.updated_at)}). "
                "Escribe /resume para continuarla.[/]"
            )
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
        saved = self._saved(self.session_id)
        table.add_row("[bold]Sesión:[/]", self.session_id + (f" · {saved.title}" if saved else " (nueva)"))
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
        table.add_row("[bold]Base de datos:[/]", str(self.store.path))
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
        if self._saved(self.session_id):
            self.console.print(
                f"💾 Sesión guardada: {self.session_id} · retómala con 'dui-ia --resume' o '/load'"
            )
        self.store.delete_empty()
        self.console.print("[cyan]¡Hasta pronto! Gracias por usar dui-IA.[/]")
