"""
Cómo se ve el trabajo del agente en la terminal: spinner mientras piensa, texto
en streaming, panel por cada herramienta y diálogo de confirmación.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..agent import LLMResponse, RunHooks, Tool

YES = {"s", "si", "sí", "y", "yes"}
NO = {"n", "no", ""}


def format_args(arguments: dict[str, Any]) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in arguments.items())


def answer_panel(text: str, sym: dict[str, str]) -> Panel:
    return Panel(Markdown(text), title=f"{sym['agent']} dui-IA", title_align="left", border_style="cyan")


class TerminalHooks(RunHooks):
    def __init__(
        self,
        console: Console,
        ask: Callable[[str], str],
        sym: dict[str, str],
        streaming: bool = False,
    ) -> None:
        self.console = console
        self.ask = ask
        self.sym = sym
        self.streaming = streaming
        self._status: Any = None
        self._live: Live | None = None
        self._buffer = ""
        # True si la última respuesta ya se mostró en streaming (la terminal no la repite).
        self.last_streamed = False

    # ------------------------------------------------------------ indicadores

    def _spinner(self, message: str) -> None:
        self.stop()
        self._status = self.console.status(message, spinner="dots")
        self._status.start()

    def stop(self) -> None:
        if self._status is not None:
            self._status.stop()
            self._status = None
        if self._live is not None:
            self._live.stop()
            self._live = None

    # ---------------------------------------------------------------- modelo

    def on_llm_start(self) -> None:
        self._buffer = ""
        self.last_streamed = False
        self._spinner("[cyan]Pensando…")

    def on_text(self, delta: str) -> None:
        self._buffer += delta
        if self._live is None:
            if self._status is not None:
                self._status.stop()
                self._status = None
            self._live = Live(
                answer_panel(self._buffer, self.sym),
                console=self.console,
                refresh_per_second=12,
                vertical_overflow="visible",
            )
            self._live.start()
        else:
            self._live.update(answer_panel(self._buffer, self.sym))

    def on_llm_end(self, response: LLMResponse) -> None:
        streamed = self._live is not None
        if streamed:
            self._live.update(answer_panel(response.content or self._buffer, self.sym))
        self.stop()
        self.last_streamed = streamed and not response.tool_calls
        # Texto que el modelo escribe antes de usar una herramienta (p. ej. "Voy a consultar...").
        if not streamed and response.tool_calls and response.content and response.content.strip():
            self.console.print(Markdown(response.content.strip()), style="dim")

    def on_llm_error(self) -> None:
        self.stop()
        self.last_streamed = False

    # ------------------------------------------------------------ herramientas

    def on_tool_start(self, tool: Tool, arguments: dict[str, Any]) -> None:
        self._spinner(f"[yellow]Ejecutando {tool.name}…")

    def on_tool_end(self, tool: Tool, arguments: dict[str, Any], result: str, ok: bool) -> None:
        self.stop()
        lines = result.splitlines()
        preview = "\n".join(lines[:15]) + (f"\n… ({len(lines) - 15} líneas más)" if len(lines) > 15 else "")
        self.console.print(
            Panel(
                Text(preview),
                title=f"{self.sym['tool']} {tool.name}({format_args(arguments)})",
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
            body.add_row("[bold]Riesgos:[/]", "\n".join(f"{self.sym['bullet']} {r}" for r in tool.risks))
        body.add_row("", "[dim]Tu decisión quedará registrada en la auditoría.[/]")
        self.console.print(
            Panel(
                body,
                title=f"{self.sym['warn']} CONFIRMACIÓN REQUERIDA",
                border_style="yellow",
                title_align="left",
            )
        )
        while True:
            try:
                answer = self.ask("¿Deseas continuar? [s/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            if answer in YES:
                self.console.print(f"[green]{self.sym['ok']} Acción aprobada[/]")
                return True
            if answer in NO:
                self.console.print(f"[red]{self.sym['fail']} Acción cancelada[/]")
                return False
            self.console.print("Responde 's' para sí o 'n' para no.")
