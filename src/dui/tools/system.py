"""
Información de red del PROPIO equipo: interfaces y conexiones/puertos abiertos.

Usa psutil, que funciona igual en Windows, Linux y macOS. Solo lee el estado
local (como `ipconfig`/`ip addr` y `netstat`): no envía nada a la red.
"""

from __future__ import annotations

import ipaddress
import socket
from collections import Counter
from typing import Literal

import psutil

from ..agent.tools import ToolError, tool
from ..compat import MACOS, current_os, elevation_hint

# Servicios que conviene no exponer a la red (o solo con cuidado).
RISKY_PORTS: dict[int, str] = {
    21: "FTP (envía contraseñas sin cifrar)",
    23: "Telnet (sin cifrar, obsoleto)",
    135: "RPC de Windows (normal en Windows; no debe quedar expuesto a Internet)",
    139: "NetBIOS / carpetas compartidas (normal en Windows en redes de confianza)",
    445: "SMB / carpetas compartidas (normal en Windows; nunca debe exponerse a Internet)",
    1433: "SQL Server",
    2375: "API de Docker sin cifrar (control total del equipo)",
    3306: "MySQL/MariaDB",
    3389: "Escritorio remoto (RDP)",
    5432: "PostgreSQL",
    5900: "VNC (control remoto)",
    6379: "Redis (suele no tener contraseña)",
    9200: "Elasticsearch",
    11211: "Memcached",
    27017: "MongoDB",
}


def _family(family: int) -> str:
    if family == socket.AF_INET:
        return "IPv4"
    if family == socket.AF_INET6:
        return "IPv6"
    if family == getattr(psutil, "AF_LINK", object()) or family == getattr(socket, "AF_PACKET", object()):
        return "MAC"
    return str(family)


@tool(category="system")
def network_interfaces() -> str:
    """Muestra las interfaces de red de este equipo (Wi-Fi, Ethernet, VPN...): si están
    activas, su velocidad y sus direcciones IPv4, IPv6 y MAC."""
    addresses = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    lines = ["Interfaces de red de este equipo:"]
    for name in sorted(addresses, key=lambda n: (not stats.get(n, None) or not stats[n].isup, n.lower())):
        stat = stats.get(name)
        state = "activa" if stat and stat.isup else "inactiva"
        speed = f", {stat.speed} Mb/s" if stat and stat.speed else ""
        lines.append(f"- {name} ({state}{speed})")
        for addr in addresses[name]:
            kind = _family(addr.family)
            if kind not in ("IPv4", "IPv6", "MAC") or not addr.address:
                continue
            value = addr.address.split("%")[0]
            mask = f" máscara {addr.netmask}" if kind == "IPv4" and addr.netmask else ""
            note = ""
            if kind in ("IPv4", "IPv6"):
                try:
                    ip = ipaddress.ip_address(value)
                    note = (
                        " (loopback)" if ip.is_loopback else " (privada)" if ip.is_private else " (pública)"
                    )
                except ValueError:
                    pass
            lines.append(f"    {kind}: {value}{mask}{note}")
    return "\n".join(lines)


def _process_names() -> dict[int, str]:
    names: dict[int, str] = {}
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            names[proc.info["pid"]] = proc.info["name"] or "?"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names


def endpoint(ip: str, port: int) -> str:
    """'192.168.1.5:80' o '[2001:db8::1]:443': IPv6 entre corchetes para no confundir el puerto."""
    return f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"


def _exposure(ip: str) -> str:
    if ip in ("0.0.0.0", "::", ""):
        return "toda la red"
    try:
        return "solo este equipo" if ipaddress.ip_address(ip.split("%")[0]).is_loopback else "red"
    except ValueError:
        return "red"


@tool(category="system")
def local_connections(
    state: Literal["escuchando", "establecidas", "todas"] = "escuchando", limit: int = 60
) -> str:
    """Lista los puertos abiertos y las conexiones de red de ESTE equipo, con el programa que
    los usa (como netstat). Señala servicios riesgosos expuestos a la red (RDP, SMB, Telnet,
    bases de datos...).

    Args:
        state: escuchando (puertos abiertos esperando conexiones), establecidas (conexiones
            activas con otros equipos) o todas.
        limit: Máximo de filas a mostrar (1 a 300).
    """
    limit = max(1, min(int(limit), 300))
    try:
        connections = psutil.net_connections(kind="inet")
    except psutil.AccessDenied as exc:
        hint = "En macOS se necesita sudo para ver las conexiones. " if current_os() == MACOS else ""
        raise ToolError(f"Sin permiso para listar conexiones. {hint}{elevation_hint()}") from exc

    names = _process_names()
    wanted = {"escuchando": {psutil.CONN_LISTEN}, "establecidas": {psutil.CONN_ESTABLISHED}}.get(state)
    rows = []
    for conn in connections:
        is_udp = conn.type == socket.SOCK_DGRAM
        status = "LISTEN" if is_udp and not conn.raddr else conn.status
        if wanted is not None:
            if state == "escuchando" and not (status == psutil.CONN_LISTEN or (is_udp and not conn.raddr)):
                continue
            if state == "establecidas" and status not in wanted:
                continue
        rows.append((conn, "UDP" if is_udp else "TCP", status))

    unknown_owner = sum(1 for conn, _, _ in rows if not conn.pid)
    lines = [f"Conexiones de este equipo ({state}): {len(rows)}"]
    risky: list[str] = []
    seen: set[tuple] = set()
    for conn, proto, _status in sorted(rows, key=lambda r: (r[0].laddr.port if r[0].laddr else 0, r[1])):
        local_ip = conn.laddr.ip if conn.laddr else ""
        local_port = conn.laddr.port if conn.laddr else 0
        remote = endpoint(conn.raddr.ip, conn.raddr.port) if conn.raddr else ""
        process = names.get(conn.pid, "?") if conn.pid else "?"
        key = (proto, local_ip, local_port, remote, process)
        if key in seen:
            continue
        seen.add(key)
        exposure = _exposure(local_ip)
        if len(seen) <= limit:
            detail = f" → {remote}" if remote else f" (accesible desde: {exposure})"
            lines.append(
                f"- {proto} {endpoint(local_ip, local_port)}{detail} · {process} (PID {conn.pid or '?'})"
            )
        if not remote and local_port in RISKY_PORTS and exposure != "solo este equipo":
            risky.append(f"{local_port} ({RISKY_PORTS[local_port]}) por {process}, expuesto a: {exposure}")
    if len(seen) > limit:
        lines.append(f"… y {len(seen) - limit} más (aumenta 'limit' para verlas).")

    if state in ("escuchando", "todas"):
        if risky:
            lines.append("\nServicios sensibles abiertos a la red:")
            lines += [f"- {r}" for r in dict.fromkeys(risky)]
        else:
            lines.append("\nNo hay servicios de la lista de riesgo abiertos a la red.")
    if state in ("establecidas", "todas"):
        remotes = Counter(conn.raddr.ip for conn, _, _ in rows if conn.raddr)
        if remotes:
            lines.append(
                "Equipos remotos con más conexiones: "
                + ", ".join(f"{ip} ({n})" for ip, n in remotes.most_common(5))
            )
    if unknown_owner:
        lines.append(
            f"Nota: en {unknown_owner} conexiones no se pudo ver el programa (pertenecen a otro usuario "
            f"o al sistema). {elevation_hint()}"
        )
    return "\n".join(lines)
