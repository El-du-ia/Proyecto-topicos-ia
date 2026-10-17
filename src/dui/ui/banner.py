"""
Pantalla de inicio: logo "DUI-IA" en letras grandes y la información del entorno.

El logo se arma letra por letra (cada letra tiene el mismo ancho en todas sus filas),
así nunca queda desalineado. Hay dos fuentes: bloques Unicode y ASCII puro, para las
consolas que no muestran bien esos caracteres (modo --ascii).
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Fuente "ANSI Shadow": 6 filas por letra.
BLOCK = {
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "-": ["      ", "      ", "█████╗", "╚════╝", "      ", "      "],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
}

# Fuente ASCII ("standard" de figlet): 5 filas por letra.
PLAIN = {
    "D": [" ____  ", "|  _ \\ ", "| | | |", "| |_| |", "|____/ "],
    "U": [" _   _ ", "| | | |", "| | | |", "| |_| |", " \\___/ "],
    "I": [" ___ ", "|_ _|", " | | ", " | | ", "|___|"],
    "-": ["       ", "       ", " _____ ", "|_____|", "       "],
    "A": ["    _    ", "   / \\   ", "  / _ \\  ", " / ___ \\ ", "/_/   \\_\\"],
}

# Degradado de arriba hacia abajo.
GRADIENT = ["bright_cyan", "cyan", "deep_sky_blue1", "dodger_blue1", "slate_blue1", "medium_purple"]


def logo(word: str = "DUI-IA", plain: bool = False) -> list[str]:
    font = PLAIN if plain else BLOCK
    gap = " " if plain else ""  # la fuente ASCII no trae espacio entre letras
    height = len(next(iter(font.values())))
    rows = [""] * height
    for index, char in enumerate(word):
        glyph = font[char]
        width = max(len(line) for line in glyph)
        for i in range(height):
            rows[i] += (gap if index else "") + glyph[i].ljust(width)
    return [row.rstrip() for row in rows]


def logo_width(plain: bool = False) -> int:
    return max(len(row) for row in logo(plain=plain))


def render_logo(plain: bool) -> Text:
    # Alineado a la izquierda dentro del bloque; Align.center centra el bloque completo.
    # (justify="center" centraría cada fila por separado y desarmaría las letras).
    text = Text(justify="left", no_wrap=True)
    rows = logo(plain=plain)
    width = max(len(r) for r in rows)
    for i, row in enumerate(rows):
        text.append(row.ljust(width), style=f"bold {GRADIENT[min(i, len(GRADIENT) - 1)]}")
        if i < len(rows) - 1:
            text.append("\n")
    return text


def render_banner(
    console: Console,
    *,
    version: str,
    plain: bool,
    sym: dict[str, str],
    info: list[tuple[str, str]],
    examples: list[str],
) -> Group:
    """Logo (si cabe) + subtítulo + panel con la información + ejemplos para empezar."""
    parts: list = []
    if console.width >= logo_width(plain) + 4:
        parts.append(Align.center(render_logo(plain)))
    else:  # terminal angosta: solo el nombre
        parts.append(Align.center(Text("dui-IA", style="bold bright_cyan")))
    parts.append(
        Align.center(
            Text.assemble(
                ("Agente inteligente de ciberseguridad", "bold"),
                (f"  {sym['sep']}  ", "dim"),
                (f"v{version}", "dim"),
            )
        )
    )
    parts.append(Text())

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right", no_wrap=True)
    table.add_column()
    for label, value in info:
        table.add_row(label, value)

    if examples:
        table.add_row("", "")
        table.add_row("Prueba", f"[italic]{examples[0]}[/]")
        for example in examples[1:]:
            table.add_row("", f"[italic]{example}[/]")

    parts.append(
        Panel(
            table,
            border_style="cyan",
            title=f"{sym['app']} Listo para ayudarte".strip(),
            title_align="left",
            padding=(1, 2),
        )
    )
    return Group(*parts)
