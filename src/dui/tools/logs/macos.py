"""
Registros de macOS (experimental) mediante `log show`, el registro unificado del sistema.

Por ahora solo cubre inicios de sesión fallidos y fallas graves; se probará en un
equipo real en la fase 5.
"""

from __future__ import annotations

import json

from .common import LogAccessError, LogEvent, LogResult, run

PREDICATES = {
    "logins_fallidos": (
        '(process == "sshd" AND eventMessage CONTAINS[c] "failed") OR '
        '(eventMessage CONTAINS[c] "authentication failed") OR '
        '(eventMessage CONTAINS[c] "incorrect password attempt")'
    ),
    "errores": "messageType == fault",
}

LEVELS = {"fault": "crítico", "error": "error", "default": "información", "info": "información"}


def read(category: str, hours: int, max_events: int) -> LogResult:
    predicate = PREDICATES.get(category)
    if predicate is None:
        raise LogAccessError(f"La categoría '{category}' todavía no está disponible en macOS.")
    code, out, err = run(
        ["log", "show", "--last", f"{hours}h", "--style", "ndjson", "--predicate", predicate], timeout=120
    )
    if code != 0:
        raise LogAccessError(f"'log show' falló: {err.strip()[:200]}")
    events = []
    for line in out.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if "eventMessage" not in entry:
            continue
        process = str(entry.get("processImagePath", "")).rsplit("/", 1)[-1]
        events.append(
            LogEvent(
                time=str(entry.get("timestamp", ""))[:19].replace(" ", "T"),
                source=process,
                level=LEVELS.get(str(entry.get("messageType", "")).lower(), "información"),
                message=str(entry["eventMessage"]),
            )
        )
    events = events[-max_events:]
    notes = ["Soporte de macOS experimental."]
    return LogResult(events, "registro unificado de macOS", notes, truncated=len(events) >= max_events)
