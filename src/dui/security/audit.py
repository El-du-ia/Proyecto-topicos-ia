"""
Registro de auditoría: cada confirmación (aprobada o rechazada) y cada ejecución
de herramienta queda guardada, una línea JSON por evento.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, session_id: str, path: Path | None = None) -> None:
        """Si path es None, el registro solo se guarda en memoria (útil para pruebas)."""
        self.session_id = session_id
        self.path = path
        self.events: list[dict[str, Any]] = []
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, **data: Any) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "session_id": self.session_id,
            "event": event,
            **data,
        }
        self.events.append(entry)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def summary(self) -> dict[str, Any]:
        confirmations = [e for e in self.events if e["event"] == "confirmation"]
        executions = [e for e in self.events if e["event"] == "tool_execution"]
        return {
            "total_actions": len(executions),
            "approvals": sum(1 for e in confirmations if e.get("approved")),
            "rejections": sum(1 for e in confirmations if not e.get("approved")),
            "tools_used": sorted({e["tool"] for e in executions}),
        }
