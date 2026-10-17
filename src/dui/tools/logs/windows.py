"""
Registros de Windows (Visor de eventos) mediante wevtutil, que viene con Windows.

Permisos: el registro "Security" (inicios de sesión, cuentas) requiere ejecutar
como Administrador; "System" y el de Windows Defender se leen sin privilegios.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

from ...compat import elevation_hint
from .common import LogAccessError, LogEvent, LogResult, run

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
ACCESS_DENIED = 5
CHANNEL_NOT_FOUND = 15007

LEVELS = {"1": "crítico", "2": "error", "3": "advertencia", "4": "información", "0": "información"}

LOGON_TYPES = {
    "2": "local (teclado)",
    "3": "red (carpetas compartidas)",
    "4": "tarea programada",
    "5": "servicio",
    "7": "desbloqueo de pantalla",
    "8": "red (texto claro)",
    "9": "credenciales nuevas",
    "10": "escritorio remoto (RDP)",
    "11": "credenciales en caché",
}

FAILURE_REASONS = {
    "0xc000006a": "contraseña incorrecta",
    "0xc0000064": "el usuario no existe",
    "0xc0000234": "cuenta bloqueada",
    "0xc0000072": "cuenta deshabilitada",
    "0xc000006f": "fuera del horario permitido",
    "0xc0000070": "equipo no autorizado",
    "0xc0000071": "contraseña vencida",
    "0xc0000193": "cuenta vencida",
    "0xc0000133": "reloj desincronizado",
    "0xc000015b": "tipo de inicio de sesión no permitido",
    "0xc0000224": "debe cambiar la contraseña",
}

ACCOUNT_EVENTS = {
    "4720": "Cuenta de usuario creada",
    "4722": "Cuenta habilitada",
    "4723": "Intento de cambio de contraseña",
    "4724": "Contraseña restablecida",
    "4725": "Cuenta deshabilitada",
    "4726": "Cuenta eliminada",
    "4728": "Miembro agregado a un grupo global",
    "4732": "Miembro agregado a un grupo local",
    "4756": "Miembro agregado a un grupo universal",
    "4738": "Cuenta modificada",
}

DEFENDER_EVENTS = {
    "1006": "Se detectó malware",
    "1007": "Se tomó una acción contra malware",
    "1008": "Falló la acción contra malware",
    "1015": "Se detectó comportamiento sospechoso",
    "1116": "Se detectó malware o software no deseado",
    "1117": "Se tomó una acción para proteger el equipo",
    "1118": "Falló la acción de corrección",
    "1119": "Error crítico en la acción de corrección",
    "5001": "Protección en tiempo real DESACTIVADA",
    "5010": "Análisis de spyware desactivado",
    "5012": "Análisis de virus desactivado",
}


@dataclass(frozen=True)
class Query:
    log: str
    condition: str  # filtro XPath dentro de System[...]
    label: str


def _ids(*ids: str) -> str:
    return "(" + " or ".join(f"EventID={i}" for i in ids) + ")"


QUERIES: dict[str, Query] = {
    "logins_fallidos": Query("Security", _ids("4625", "4740"), "Visor de eventos: Security"),
    "cuentas": Query("Security", _ids(*ACCOUNT_EVENTS), "Visor de eventos: Security"),
    "errores": Query("System", "(Level=1 or Level=2)", "Visor de eventos: System"),
    "servicios": Query("System", _ids("7045", "7034", "7031"), "Visor de eventos: System"),
    "antivirus": Query(
        "Microsoft-Windows-Windows Defender/Operational",
        _ids(*DEFENDER_EVENTS),
        "Visor de eventos: Windows Defender",
    ),
}


def local_time(system_time: str) -> str:
    """'2026-10-16T12:38:58.5103885Z' (UTC, 7 decimales) → hora local ISO sin decimales."""
    value = re.sub(r"\.(\d{6})\d*", r".\1", system_time.strip()).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value).astimezone().isoformat(timespec="seconds")
    except ValueError:
        return system_time


def parse_events(xml_text: str) -> list[LogEvent]:
    xml_text = xml_text.strip()
    if not xml_text:
        return []
    root = ET.fromstring(f"<Events>{xml_text}</Events>")
    events = []
    for node in root.findall("e:Event", NS):
        system = node.find("e:System", NS)
        if system is None:
            continue
        provider = system.find("e:Provider", NS)
        created = system.find("e:TimeCreated", NS)
        data = {
            d.get("Name", ""): (d.text or "").strip()
            for d in node.findall("e:EventData/e:Data", NS)
            if d.get("Name")
        }
        message = node.findtext("e:RenderingInfo/e:Message", default="", namespaces=NS) or ""
        event = LogEvent(
            time=local_time(created.get("SystemTime", "")) if created is not None else "",
            source=provider.get("Name", "") if provider is not None else "",
            level=LEVELS.get(system.findtext("e:Level", default="", namespaces=NS), "información"),
            message=message.strip().splitlines()[0] if message.strip() else "",
            event_id=system.findtext("e:EventID", default="", namespaces=NS),
        )
        _enrich(event, data)
        events.append(event)
    return events


def _enrich(event: LogEvent, data: dict[str, str]) -> None:
    """Extrae los campos importantes de cada tipo de evento y redacta un mensaje claro."""
    eid = event.event_id

    def user(name_key: str = "TargetUserName", domain_key: str = "TargetDomainName") -> str:
        name, domain = data.get(name_key, ""), data.get(domain_key, "")
        return f"{domain}\\{name}" if domain and domain != "-" and name else name

    if eid == "4625":
        origin = data.get("IpAddress", "")
        if origin in ("", "-"):
            origin = data.get("WorkstationName", "") or "local"
        status = (data.get("SubStatus") or "").lower()
        if status in ("", "0x0"):
            status = (data.get("Status") or "").lower()
        event.fields = {
            "user": user(),
            "origin": origin,
            "logon_type": LOGON_TYPES.get(data.get("LogonType", ""), data.get("LogonType", "")),
            "reason": FAILURE_REASONS.get(status, status),
        }
        event.message = f"Inicio de sesión fallido de {event.fields['user'] or '?'}"
    elif eid == "4740":
        event.fields = {
            "user": user(),
            "origin": data.get("TargetDomainName", ""),
            "reason": "cuenta bloqueada",
        }
        event.message = f"Cuenta bloqueada por demasiados intentos: {data.get('TargetUserName', '?')}"
    elif eid in ACCOUNT_EVENTS:
        event.fields = {"by": user("SubjectUserName", "SubjectDomainName")}
        if eid in ("4728", "4732", "4756"):
            event.fields["group"] = data.get("TargetUserName", "")
            event.fields["member"] = data.get("MemberName", "") or data.get("MemberSid", "")
        else:
            event.fields["user"] = user()
        event.message = ACCOUNT_EVENTS[eid]
    elif eid == "7045":
        event.fields = {
            "service": data.get("ServiceName", ""),
            "path": data.get("ImagePath", ""),
            "account": data.get("AccountName", ""),
        }
        event.message = f"Servicio instalado: {data.get('ServiceName', '?')}"
    elif eid in DEFENDER_EVENTS:
        event.fields = {
            "threat": data.get("Threat Name", ""),
            "severity": data.get("Severity Name", ""),
            "path": data.get("Path", ""),
            "action": data.get("Action Name", ""),
        }
        event.message = DEFENDER_EVENTS[eid]


def read(category: str, hours: int, max_events: int) -> LogResult:
    query = QUERIES[category]
    xpath = f"*[System[{query.condition} and TimeCreated[timediff(@SystemTime) <= {hours * 3_600_000}]]]"
    code, out, err = run(
        ["wevtutil", "qe", query.log, f"/q:{xpath}", f"/c:{max_events}", "/rd:true", "/f:RenderedXml"]
    )
    if code == ACCESS_DENIED:
        raise LogAccessError(
            f"Leer el registro '{query.log}' requiere privilegios de Administrador. {elevation_hint()}"
        )
    if code == CHANNEL_NOT_FOUND:
        raise LogAccessError(f"El registro '{query.log}' no existe en este equipo.")
    if code != 0:
        raise LogAccessError(f"wevtutil falló (código {code}): {err.strip()[:200]}")
    try:
        events = parse_events(out)
    except ET.ParseError as exc:
        raise LogAccessError(f"No se pudo interpretar la salida de wevtutil: {exc}") from exc
    return LogResult(events, query.label, truncated=len(events) >= max_events)
