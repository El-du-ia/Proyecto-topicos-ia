"""
Alcance permitido: qué objetivos se pueden analizar de forma activa.

Las herramientas activas (escaneo de puertos, descubrimiento de hosts) solo
aceptan objetivos dentro del alcance. Si no se configura nada, solo se permiten
redes privadas y locales (192.168.x.x, 10.x.x.x, 127.0.0.1, ...), que es lo que
un usuario normalmente puede analizar con permiso: su propia red.

Para analizar algo público hay que agregarlo de forma explícita (DUI_SCOPE en
.env o el comando /scope add), lo que deja constancia de que se tiene permiso.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from collections.abc import Callable, Iterable

from ..errors import ToolError

IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network

# Letras, números, puntos, guiones, dos puntos (IPv6), barra (CIDR) y guion bajo.
_TARGET_RE = re.compile(r"^[A-Za-z0-9._:/\-]+$")
HOSTNAME_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$")

DEFAULT_NETWORKS: tuple[IPNetwork, ...] = tuple(
    ipaddress.ip_network(n)
    for n in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)


class ScopeError(ToolError):
    """El objetivo está fuera del alcance permitido o tiene un formato inválido."""


def _resolve(host: str) -> list[str]:
    infos = socket.getaddrinfo(host, None)
    return sorted({info[4][0] for info in infos})


def validate_target_syntax(target: str) -> str:
    """Rechaza objetivos que podrían interpretarse como opciones de un comando (p. ej. '-iL')."""
    target = target.strip()
    if not target:
        raise ScopeError("No se indicó ningún objetivo.")
    if target.startswith("-") or not _TARGET_RE.match(target):
        raise ScopeError(
            f"'{target}' no es un objetivo válido. Usa una IP (192.168.1.10), "
            "una red en formato CIDR (192.168.1.0/24) o un nombre de dominio."
        )
    return target


class Scope:
    def __init__(
        self,
        entries: Iterable[str] = (),
        resolver: Callable[[str], list[str]] = _resolve,
    ) -> None:
        self.networks: list[IPNetwork] = []
        self.domains: list[str] = []
        self._resolver = resolver
        for entry in entries:
            self.add(entry)

    @property
    def is_custom(self) -> bool:
        return bool(self.networks or self.domains)

    def add(self, entry: str) -> None:
        # "*.example.com" equivale a "example.com" (los subdominios siempre se incluyen).
        entry = validate_target_syntax(entry.strip().removeprefix("*.")).lower().rstrip(".")
        try:
            self.networks.append(ipaddress.ip_network(entry, strict=False))
            return
        except ValueError:
            pass
        domain = entry
        if not HOSTNAME_RE.match(domain):
            raise ScopeError(f"'{entry}' no es una IP, red ni dominio válido.")
        if domain not in self.domains:
            self.domains.append(domain)

    def _allowed_networks(self) -> tuple[IPNetwork, ...]:
        return DEFAULT_NETWORKS + tuple(self.networks)

    def _network_allowed(self, net: IPNetwork) -> bool:
        return any(
            net.version == allowed.version and net.subnet_of(allowed)  # type: ignore[arg-type]
            for allowed in self._allowed_networks()
        )

    def _domain_allowed(self, host: str) -> bool:
        return any(host == d or host.endswith("." + d) for d in self.domains)

    def check(self, target: str) -> tuple[bool, str]:
        """Devuelve (permitido, explicación)."""
        try:
            target = validate_target_syntax(target).lower().rstrip(".")
        except ScopeError as exc:
            return False, str(exc)

        try:
            net = ipaddress.ip_network(target, strict=False)
        except ValueError:
            net = None

        if net is not None:
            if self._network_allowed(net):
                return True, f"{target} está dentro del alcance permitido."
            return False, self._outside_message(target)

        if not HOSTNAME_RE.match(target):
            return False, f"'{target}' no es una IP, red ni dominio válido."
        if self._domain_allowed(target):
            return True, f"{target} está dentro de los dominios permitidos."
        try:
            addresses = self._resolver(target)
        except OSError:
            return False, f"No se pudo resolver '{target}', así que no se puede verificar el alcance."
        if addresses and all(self._network_allowed(ipaddress.ip_network(a)) for a in addresses):
            return True, f"{target} resuelve a direcciones dentro del alcance ({', '.join(addresses)})."
        return False, self._outside_message(target)

    def ensure_allowed(self, target: str) -> str:
        allowed, message = self.check(target)
        if not allowed:
            raise ScopeError(message)
        return target.strip()

    @staticmethod
    def _outside_message(target: str) -> str:
        return (
            f"'{target}' está FUERA del alcance permitido. Por defecto solo se pueden analizar "
            "redes privadas o locales. Si tienes autorización para analizar este objetivo, "
            f"agrégalo con '/scope add {target}' o en DUI_SCOPE dentro del archivo .env."
        )

    def describe(self) -> str:
        base = "redes privadas y locales"
        extra = [str(n) for n in self.networks] + self.domains
        return f"{base} + {', '.join(extra)}" if extra else base
