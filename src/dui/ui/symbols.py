"""
Íconos de la interfaz, con alternativa en texto plano.

La consola clásica de Windows (conhost), algunas terminales por SSH y los lectores
de pantalla no muestran bien los emojis. En esos casos (o con DUI_ASCII=1 /
--ascii) se usan equivalentes en ASCII.
"""

from __future__ import annotations

from rich.console import Console

EMOJI = {
    "app": "🛡️ ",
    "agent": "🤖",
    "user": "👤",
    "tool": "🔧",
    "warn": "⚠️ ",
    "ok": "✅",
    "fail": "❌",
    "note": "📌",
    "empty": "📭",
    "saved": "💾",
    "stats": "📊",
    "result": "↳",
    "current": "◀",
    "bullet": "•",
    "loaded": "✓",
    "sep": "·",
    "prompt": "›",
}

ASCII = {
    "app": "",
    "agent": "[IA]",
    "user": ">",
    "tool": "*",
    "warn": "!!",
    "ok": "[OK]",
    "fail": "[X]",
    "note": "(!)",
    "empty": "-",
    "saved": "[GUARDADO]",
    "stats": "-",
    "result": "->",
    "current": "<",
    "bullet": "-",
    "loaded": "[OK]",
    "sep": "|",
    "prompt": ">",
}


def wants_plain(console: Console, forced: bool = False) -> bool:
    """True si conviene usar ASCII: forzado, consola clásica de Windows o codificación no UTF-8."""
    if forced:
        return True
    if console.legacy_windows:
        return True
    return "utf" not in (console.encoding or "").lower()


def symbols(plain: bool) -> dict[str, str]:
    return ASCII if plain else EMOJI
