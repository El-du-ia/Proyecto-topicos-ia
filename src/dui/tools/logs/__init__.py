"""
Análisis de registros del sistema con la misma interfaz en Windows, Linux y macOS.

    Windows → Visor de eventos (wevtutil)
    Linux   → journalctl, o /var/log/auth.log, secure, syslog...
    macOS   → registro unificado (log show), experimental
"""

from __future__ import annotations

from typing import Literal

from ...agent.tools import Availability, ToolError, tool
from ...compat import LINUX, MACOS, WINDOWS, current_os, find_binary
from . import linux, macos, windows
from .common import Category, LogAccessError, summarize
from .files import analyze_file

PRIVACY_RISK = (
    "El contenido de los registros (usuarios, IPs, nombres de equipos) se enviará al modelo "
    "de IA configurado; si es un modelo en la nube, saldrá de tu equipo."
)

BACKENDS = {WINDOWS: windows.read, LINUX: linux.read, MACOS: macos.read}
REQUIRED_PROGRAM = {WINDOWS: "wevtutil", LINUX: None, MACOS: "log"}


def _check() -> Availability:
    os_name = current_os()
    if os_name not in BACKENDS:
        return Availability.no("Sistema operativo no soportado.")
    program = REQUIRED_PROGRAM[os_name]
    if program and not find_binary(program):
        return Availability.no(f"No se encontró '{program}'.")
    return Availability.yes()


@tool(sensitive=True, category="system", risks=(PRIVACY_RISK,), check=_check)
def analyze_logs(category: Category = "logins_fallidos", hours: int = 24, max_events: int = 200) -> str:
    """Revisa los registros de seguridad de ESTE equipo y resume lo importante.

    Funciona en Windows (Visor de eventos) y Linux (journalctl o /var/log). Sirve para
    detectar intentos de acceso, cuentas creadas sin permiso, servicios sospechosos
    instalados, errores graves o alertas del antivirus.

    Args:
        category: logins_fallidos (contraseñas incorrectas, posible fuerza bruta),
            cuentas (usuarios creados/eliminados o agregados a grupos como Administradores),
            errores (fallas críticas del sistema), servicios (servicios instalados o que fallan;
            un servicio desconocido puede ser malware) o antivirus (detecciones de Windows
            Defender/ClamAV o protección desactivada).
        hours: Cuántas horas hacia atrás revisar (1 a 720).
        max_events: Máximo de eventos a leer (1 a 1000).
    """
    hours = max(1, min(int(hours), 720))
    max_events = max(1, min(int(max_events), 1000))
    reader = BACKENDS.get(current_os())
    if reader is None:
        raise ToolError("Este sistema operativo no está soportado para el análisis de registros.")
    try:
        result = reader(category, hours, max_events)
    except LogAccessError as exc:
        raise ToolError(str(exc)) from exc
    return summarize(category, hours, result)


@tool(sensitive=True, category="system", risks=(PRIVACY_RISK,))
def analyze_log_file(
    path: str,
    focus: Literal["todo", "errores", "autenticacion", "sospechoso"] = "todo",
    max_lines: int = 2000,
) -> str:
    """Analiza un archivo de log concreto (de una aplicación, servidor web, etc.) buscando
    errores, fallos de autenticación o señales de ataque (inyección SQL, rutas '../', etc.).

    Args:
        path: Ruta del archivo, por ejemplo 'C:\\inetpub\\logs\\LogFiles\\W3SVC1\\u_ex261016.log'
            o '/var/log/nginx/access.log'.
        focus: Qué buscar: todo, errores, autenticacion o sospechoso.
        max_lines: Cuántas líneas del final del archivo revisar (10 a 20000).
    """
    return analyze_file(path, focus, max_lines)


__all__ = ["analyze_log_file", "analyze_logs"]
