"""
Capa de compatibilidad con el sistema operativo.

Todo lo que cambia entre Windows, Linux y macOS (privilegios, binarios externos,
nombres de usuario, consejos de elevación) se resuelve aquí, para que el resto
del código no tenga que preguntar en qué sistema está.
"""

from __future__ import annotations

import getpass
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

WINDOWS = "windows"
LINUX = "linux"
MACOS = "macos"
OTHER = "other"


def current_os() -> str:
    """Devuelve 'windows', 'linux', 'macos' u 'other'."""
    if sys.platform.startswith("win"):
        return WINDOWS
    if sys.platform.startswith("linux"):
        return LINUX
    if sys.platform == "darwin":
        return MACOS
    return OTHER


def is_admin() -> bool:
    """True si el proceso tiene privilegios de administrador (Windows) o root (Unix)."""
    if current_os() == WINDOWS:
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False
    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid and geteuid() == 0)


# Rutas donde los instaladores oficiales dejan binarios que no siempre quedan en el PATH.
_WINDOWS_EXTRA_DIRS = {
    "nmap": [r"C:\Program Files (x86)\Nmap", r"C:\Program Files\Nmap"],
}


def find_binary(name: str) -> str | None:
    """Busca un ejecutable en el PATH (y en rutas de instalación conocidas en Windows)."""
    found = shutil.which(name)
    if found:
        return found
    if current_os() == WINDOWS:
        for directory in _WINDOWS_EXTRA_DIRS.get(name, []):
            candidate = Path(directory) / f"{name}.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def username() -> str:
    """Nombre del usuario actual, sin depender de la variable USER (que no existe en Windows)."""
    try:
        return getpass.getuser()
    except Exception:  # getpass puede fallar en entornos sin usuario (contenedores)
        return "desconocido"


def elevation_hint() -> str:
    """Explica, según el sistema, cómo ejecutar dui-IA con privilegios elevados."""
    if current_os() == WINDOWS:
        return (
            "Abre la terminal como Administrador (clic derecho → 'Ejecutar como "
            "administrador') y vuelve a ejecutar: uv run dui-ia"
        )
    return (
        "Ejecuta con sudo usando el Python del entorno virtual: "
        "sudo .venv/bin/dui-ia  (no uses 'sudo python', no tendría las dependencias)"
    )


def packet_capture_hint() -> str:
    """Qué hace falta en cada sistema para capturar tráfico de red."""
    os_name = current_os()
    if os_name == WINDOWS:
        return (
            "Instala Npcap (https://npcap.com, viene también con el instalador de Nmap) "
            "y ejecuta la terminal como Administrador."
        )
    if os_name == MACOS:
        return "Ejecuta con sudo (macOS requiere root para abrir los dispositivos BPF)."
    return (
        "Ejecuta con sudo, o da permisos de captura al intérprete: "
        "sudo setcap cap_net_raw,cap_net_admin=eip $(readlink -f .venv/bin/python)"
    )


@dataclass(frozen=True)
class SystemInfo:
    os: str
    os_version: str
    python: str
    user: str
    admin: bool

    @property
    def os_label(self) -> str:
        return {WINDOWS: "Windows", LINUX: "Linux", MACOS: "macOS"}.get(self.os, self.os)


def system_info() -> SystemInfo:
    return SystemInfo(
        os=current_os(),
        os_version=platform.release(),
        python=platform.python_version(),
        user=username(),
        admin=is_admin(),
    )
