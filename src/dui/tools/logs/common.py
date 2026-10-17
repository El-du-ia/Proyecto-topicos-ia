"""
Modelo común de eventos y resúmenes para los registros de cada sistema operativo.

Cada backend (Windows, Linux, macOS) convierte sus registros a LogEvent; el
resumen y el texto que recibe el modelo son iguales en todos los sistemas.
"""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

Category = Literal["logins_fallidos", "cuentas", "errores", "servicios", "antivirus"]

CATEGORY_LABELS: dict[str, str] = {
    "logins_fallidos": "Inicios de sesión fallidos",
    "cuentas": "Cambios en cuentas de usuario y grupos",
    "errores": "Errores críticos del sistema",
    "servicios": "Servicios instalados o con fallas",
    "antivirus": "Detecciones y estado del antivirus",
}

# A partir de cuántos intentos fallidos desde un mismo origen se señala posible fuerza bruta.
BRUTE_FORCE_THRESHOLD = 10


class LogAccessError(Exception):
    """No se pueden leer los registros (permisos, programa ausente...). El mensaje explica la causa."""


@dataclass
class LogEvent:
    time: str  # ISO 8601
    source: str  # proveedor (Windows), unidad o proceso (Linux/macOS)
    level: str  # crítico, error, advertencia, información
    message: str
    event_id: str = ""
    fields: dict[str, str] = field(default_factory=dict)  # user, origin, logon_type, reason...


@dataclass
class LogResult:
    events: list[LogEvent]
    origin: str  # de dónde se leyó (p. ej. "Visor de eventos: Security")
    notes: list[str] = field(default_factory=list)  # avisos (permisos, límites)
    truncated: bool = False


def run(command: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Ejecuta un programa (sin shell) y devuelve (código, stdout, stderr) decodificados."""
    try:
        completed = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise LogAccessError(f"No se encontró el programa '{command[0]}' en este equipo.") from exc
    except subprocess.TimeoutExpired as exc:
        raise LogAccessError(f"'{command[0]}' tardó más de {timeout} s en responder.") from exc
    return completed.returncode, decode(completed.stdout), decode(completed.stderr)


def decode(data: bytes) -> str:
    """UTF-8 si se puede; si no, la página ANSI de Windows ('mbcs', p. ej. cp1252), que es la que usa
    wevtutil al redirigir su salida; en otros sistemas, latin-1 como último recurso."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    if sys.platform.startswith("win"):
        try:
            return data.decode("mbcs")
        except (LookupError, UnicodeDecodeError):
            pass
    return data.decode("latin-1", errors="replace")


def _short(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _top(counter: Counter[str], n: int = 5) -> str:
    return ", ".join(f"{value} ({count})" for value, count in counter.most_common(n))


def summarize(category: str, hours: int, result: LogResult, sample: int = 15) -> str:
    events = result.events
    label = CATEGORY_LABELS.get(category, category)
    lines = [f"{label} · últimas {hours} h · fuente: {result.origin}"]
    lines += [f"Nota: {note}" for note in result.notes]

    if not events:
        lines.append("No se encontraron eventos de este tipo en el periodo.")
        return "\n".join(lines)

    times = sorted(e.time for e in events if e.time)
    total = f"{len(events)}{'+' if result.truncated else ''}"
    lines.append(f"Eventos: {total}" + (f" (del {times[0][:16]} al {times[-1][:16]})" if times else ""))
    if result.truncated:
        lines.append("Se alcanzó el máximo de eventos pedido; puede haber más.")

    by_level = Counter(e.level for e in events if e.level)
    if len(by_level) > 1:
        lines.append(f"Por nivel: {_top(by_level)}")
    by_source = Counter(e.source for e in events if e.source)
    if by_source:
        lines.append(f"Fuentes principales: {_top(by_source)}")
    by_id = Counter(e.event_id for e in events if e.event_id)
    if by_id:
        lines.append(f"IDs de evento: {_top(by_id)}")

    if category == "logins_fallidos":
        users = Counter(e.fields["user"] for e in events if e.fields.get("user"))
        origins = Counter(e.fields["origin"] for e in events if e.fields.get("origin"))
        reasons = Counter(e.fields["reason"] for e in events if e.fields.get("reason"))
        kinds = Counter(e.fields["logon_type"] for e in events if e.fields.get("logon_type"))
        if users:
            lines.append(f"Usuarios intentados: {_top(users)}")
        if origins:
            lines.append(f"Orígenes: {_top(origins)}")
        if reasons:
            lines.append(f"Motivos: {_top(reasons)}")
        if kinds:
            lines.append(f"Tipo de acceso: {_top(kinds)}")
        suspicious = [o for o, c in origins.items() if c >= BRUTE_FORCE_THRESHOLD and o not in ("-", "local")]
        if suspicious:
            lines.append(
                f"ALERTA: {len(suspicious)} origen(es) con {BRUTE_FORCE_THRESHOLD} o más intentos "
                f"fallidos ({', '.join(suspicious[:5])}): patrón compatible con fuerza bruta."
            )

    # Los eventos idénticos (mismo origen, ID, mensaje y datos) se agrupan: "×N, último a las...".
    groups: dict[tuple, list[LogEvent]] = {}
    for e in sorted(events, key=lambda ev: ev.time, reverse=True):
        key = (e.source, e.event_id, e.message, tuple(sorted(e.fields.items())))
        groups.setdefault(key, []).append(e)
    lines.append(f"\nEventos más recientes (hasta {sample}, los repetidos agrupados):")
    for group in list(groups.values())[:sample]:
        e = group[0]
        extra = " ".join(f"{k}={v}" for k, v in e.fields.items() if v)
        ident = f" [{e.event_id}]" if e.event_id else ""
        repeat = f" (×{len(group)}, el último)" if len(group) > 1 else ""
        lines.append(
            f"- {e.time[:19]}{repeat} {e.level} {e.source}{ident}: {_short(e.message)}"
            + (f" ({extra})" if extra else "")
        )
    return "\n".join(lines)
