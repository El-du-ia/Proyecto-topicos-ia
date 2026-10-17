"""Interfaz de usuario en terminal."""

from .hooks import TerminalHooks
from .symbols import wants_plain
from .terminal import Terminal

__all__ = ["Terminal", "TerminalHooks", "wants_plain"]
