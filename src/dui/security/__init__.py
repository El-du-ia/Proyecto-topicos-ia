"""Seguridad del propio agente: alcance permitido y auditoría."""

from .audit import AuditLog
from .scope import Scope, ScopeError

__all__ = ["AuditLog", "Scope", "ScopeError"]
