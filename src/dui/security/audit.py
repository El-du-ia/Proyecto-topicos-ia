"""
Registro de auditoría: cada confirmación (aprobada o rechazada), bloqueo y
ejecución de herramienta queda guardada en la base de datos de sesiones.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import SessionStore


class AuditLog:
    def __init__(self, session_id: str, store: SessionStore | None = None) -> None:
        """Sin `store`, el registro solo vive en memoria (útil para pruebas)."""
        self.session_id = session_id
        self.store = store
        self._events: list[dict[str, Any]] = []

    def switch(self, session_id: str) -> None:
        """Cambia a otra sesión (al cargar o crear una)."""
        self.session_id = session_id
        self._events = []

    def record(self, event: str, **data: Any) -> None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        if self.store is not None:
            self.store.create(self.session_id)  # no hace nada si ya existe
            self.store.record_audit(self.session_id, event, data, timestamp)
        else:
            self._events.append(
                {"timestamp": timestamp, "session_id": self.session_id, "event": event, **data}
            )

    @property
    def events(self) -> list[dict[str, Any]]:
        if self.store is not None:
            return self.store.audit_events(self.session_id)
        return list(self._events)

    def summary(self) -> dict[str, Any]:
        events = self.events
        confirmations = [e for e in events if e["event"] == "confirmation"]
        executions = [e for e in events if e["event"] == "tool_execution"]
        return {
            "total_actions": len(executions),
            "approvals": sum(1 for e in confirmations if e.get("approved")),
            "rejections": sum(1 for e in confirmations if not e.get("approved")),
            "tools_used": sorted({e["tool"] for e in executions}),
        }
