"""
Reconocimiento pasivo: DNS, DNS inverso y WHOIS.

Todo está implementado en Python (dnspython, RDAP sobre HTTPS y WHOIS por el
puerto 43), así que funciona igual en Windows, Linux y macOS sin instalar
programas externos. Son consultas públicas: no requieren confirmación.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import Any, Literal

import httpx

from ..agent.tools import ToolError, tool
from ..security.scope import HOSTNAME_RE

RecordType = Literal["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]

RDAP_BOOTSTRAP = "https://rdap.org"
TIMEOUT = 15


def normalize_domain(domain: str) -> str:
    """Acepta 'Example.com', 'https://example.com/ruta' o dominios con acentos (IDN)."""
    value = re.sub(r"^[a-z]+://", "", domain.strip().lower()).split("/")[0].split(":")[0]
    value = value.rstrip(".")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ToolError(f"'{domain}' no es un dominio válido.") from exc
    if "." not in value or not HOSTNAME_RE.match(value):
        raise ToolError(f"'{domain}' no es un dominio válido (ejemplo: example.com).")
    return value


# --------------------------------------------------------------------------- DNS


def _system_resolve(domain: str, record_type: str) -> list[str]:
    family = socket.AF_INET6 if record_type == "AAAA" else socket.AF_INET
    infos = socket.getaddrinfo(domain, None, family)
    return sorted({info[4][0] for info in infos})


@tool(category="reconnaissance")
def dns_lookup(domain: str, record_type: RecordType = "A") -> str:
    """Consulta los registros DNS de un dominio: su IP, sus servidores de correo, registros TXT, etc.

    Args:
        domain: Dominio a consultar, por ejemplo 'example.com'.
        record_type: A (IPv4), AAAA (IPv6), MX (correo), TXT (SPF y verificaciones),
            NS (servidores DNS), CNAME (alias) o SOA (autoridad de la zona).
    """
    import dns.exception
    import dns.resolver

    name = normalize_domain(domain)
    try:
        answer = dns.resolver.resolve(name, record_type, lifetime=8)
        # MX se ordena por prioridad (menor = preferido); el resto, alfabéticamente.
        records = sorted(answer, key=lambda r: (getattr(r, "preference", 0), r.to_text()))
        values = [record.to_text() for record in records]
        ttl = answer.rrset.ttl if answer.rrset is not None else None
    except dns.resolver.NXDOMAIN:
        return f"El dominio '{name}' no existe (NXDOMAIN)."
    except dns.resolver.NoAnswer:
        return f"'{name}' existe pero no tiene registros {record_type}."
    except dns.exception.DNSException as exc:
        # Sin servidor DNS configurado o con la red filtrada: probar con el resolutor del sistema.
        if record_type not in ("A", "AAAA"):
            raise ToolError(f"No se pudo consultar el DNS: {exc}") from exc
        try:
            values, ttl = _system_resolve(name, record_type), None
        except OSError as os_exc:
            raise ToolError(f"No se pudo resolver '{name}': {os_exc}") from os_exc

    header = f"Registros {record_type} de {name}" + (f" (TTL {ttl} s)" if ttl else "") + ":"
    return "\n".join([header, *(f"  - {v}" for v in values)])


@tool(category="reconnaissance")
def reverse_dns(ip_address: str) -> str:
    """Busca el nombre asociado a una dirección IP (DNS inverso) para identificar a quién pertenece.

    Args:
        ip_address: Dirección IPv4 o IPv6, por ejemplo '8.8.8.8'.
    """
    try:
        ip = ipaddress.ip_address(ip_address.strip())
    except ValueError as exc:
        raise ToolError(f"'{ip_address}' no es una dirección IP válida.") from exc
    try:
        hostname, aliases, _ = socket.gethostbyaddr(str(ip))
    except (socket.herror, socket.gaierror):
        return f"No hay registro DNS inverso para {ip}."
    except OSError as exc:
        raise ToolError(f"No se pudo hacer la consulta inversa: {exc}") from exc
    lines = [f"DNS inverso de {ip}:", f"  - Nombre: {hostname}"]
    if aliases:
        lines.append(f"  - Alias: {', '.join(aliases)}")
    return "\n".join(lines)


# ------------------------------------------------------------------------- WHOIS


def _rdap(kind: str, value: str) -> dict[str, Any]:
    response = httpx.get(
        f"{RDAP_BOOTSTRAP}/{kind}/{value}",
        follow_redirects=True,
        timeout=TIMEOUT,
        headers={"Accept": "application/rdap+json, application/json"},
    )
    response.raise_for_status()
    return response.json()


def _whois_query(server: str, query: str) -> str:
    with socket.create_connection((server, 43), timeout=TIMEOUT) as conn:
        conn.sendall(f"{query}\r\n".encode())
        chunks = []
        while data := conn.recv(4096):
            chunks.append(data)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _whois43(query: str) -> str:
    """WHOIS clásico: IANA indica qué servidor es responsable y se le pregunta a ese."""
    iana = _whois_query("whois.iana.org", query)
    match = re.search(r"^\s*(?:refer|whois):\s*(\S+)", iana, re.MULTILINE | re.IGNORECASE)
    return _whois_query(match.group(1), query) if match else iana


def _vcard_name(entity: dict[str, Any]) -> str | None:
    vcard = entity.get("vcardArray")
    if not (isinstance(vcard, list) and len(vcard) > 1):
        return None
    for item in vcard[1]:
        if isinstance(item, list) and len(item) > 3 and item[0] == "fn" and item[3]:
            return str(item[3])
    return None


def _entities_by_role(data: dict[str, Any]) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    for entity in data.get("entities", []) or []:
        name = _vcard_name(entity) or entity.get("handle")
        for role in entity.get("roles", []) or []:
            if name:
                roles.setdefault(role, []).append(name)
    return roles


def format_rdap(data: dict[str, Any], kind: str) -> str:
    events = {e.get("eventAction"): str(e.get("eventDate", ""))[:10] for e in data.get("events", [])}
    roles = _entities_by_role(data)
    lines: list[str] = []
    if kind == "domain":
        lines.append(f"WHOIS (RDAP) de {data.get('ldhName', '').lower()}:")
        if roles.get("registrar"):
            lines.append(f"  - Registrador: {', '.join(roles['registrar'])}")
        if roles.get("registrant"):
            lines.append(f"  - Titular: {', '.join(roles['registrant'])}")
    else:
        lines.append(f"WHOIS (RDAP) de la red {data.get('startAddress')} - {data.get('endAddress')}:")
        for label, key in (("Nombre", "name"), ("Identificador", "handle"), ("País", "country")):
            if data.get(key):
                lines.append(f"  - {label}: {data[key]}")
        owners = roles.get("registrant") or roles.get("administrative") or []
        if owners:
            lines.append(f"  - Organización: {', '.join(dict.fromkeys(owners))}")
    for label, action in (
        ("Creado", "registration"),
        ("Expira", "expiration"),
        ("Última modificación", "last changed"),
    ):
        if events.get(action):
            lines.append(f"  - {label}: {events[action]}")
    nameservers = [ns.get("ldhName", "").lower() for ns in data.get("nameservers", []) or []]
    if nameservers:
        lines.append(f"  - Servidores DNS: {', '.join(n for n in nameservers if n)}")
    if data.get("status"):
        lines.append(f"  - Estado: {', '.join(data['status'])}")
    secure = data.get("secureDNS", {})
    if isinstance(secure, dict) and "delegationSigned" in secure:
        lines.append(f"  - DNSSEC: {'activado' if secure['delegationSigned'] else 'no activado'}")
    return "\n".join(lines)


@tool(category="reconnaissance")
def whois_lookup(target: str) -> str:
    """Consulta quién registró un dominio o a quién pertenece una IP (WHOIS/RDAP).

    Devuelve registrador, fechas de creación y expiración, servidores DNS y estado.
    Útil para saber si un sitio es legítimo (un dominio creado hace pocos días es sospechoso).

    Args:
        target: Dominio (por ejemplo 'example.com') o dirección IP.
    """
    try:
        value = str(ipaddress.ip_address(target.strip()))
        kind = "ip"
    except ValueError:
        value, kind = normalize_domain(target), "domain"

    try:
        return format_rdap(_rdap(kind, value), kind)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            rdap_error = f"RDAP respondió {exc.response.status_code}"
        else:
            rdap_error = "RDAP no tiene información"
    except (httpx.HTTPError, ValueError) as exc:
        rdap_error = f"RDAP no disponible ({type(exc).__name__})"

    try:
        raw = _whois43(value).strip()
    except OSError as exc:
        raise ToolError(f"{rdap_error} y WHOIS clásico falló: {exc}") from exc
    if len(raw) > 6000:
        raw = raw[:6000] + "\n[... recortado]"
    return f"{rdap_error}; resultado de WHOIS clásico (puerto 43):\n\n{raw}"
