"""Generación de reportes en Markdown."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

from ..agent.tools import ToolContext, tool


def _slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:50] or "reporte"


@tool(category="utility")
def generate_report(title: str, content: str, raw_data: str = "", ctx: ToolContext | None = None) -> str:
    """Guarda un reporte de seguridad en un archivo Markdown.

    Úsala solo cuando el usuario haya aceptado generar un reporte.

    Args:
        title: Título del reporte, por ejemplo 'Análisis de la red doméstica'.
        content: Reporte completo en Markdown, con las secciones indicadas en tus instrucciones.
        raw_data: Salidas técnicas relevantes de las herramientas, para auditoría.
    """
    reports_dir = ctx.settings.reports_path if ctx else Path.cwd() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    path = reports_dir / f"{now:%Y%m%d_%H%M%S}_{_slug(title)}.md"

    system = f" · Sistema: {ctx.system.os_label}" if ctx else ""
    body = content.strip()
    parts = []
    if not body.startswith("# "):
        parts.append(f"# {title}\n")
    parts.append(f"*Generado por dui-IA el {now:%Y-%m-%d %H:%M}{system}*\n")
    parts.append(body + "\n")
    if raw_data.strip():
        fence = "```"
        while fence in raw_data:
            fence += "`"
        parts.append(f"---\n\n## Anexo: datos técnicos crudos\n\n{fence}text\n{raw_data.strip()}\n{fence}\n")

    path.write_text("\n".join(parts), encoding="utf-8")
    return f"Reporte guardado en: {path.resolve()}"
