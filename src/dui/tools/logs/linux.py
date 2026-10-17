"""
Registros de Linux: journalctl (systemd) y, si no existe, los archivos clásicos
de /var/log (auth.log, secure, syslog, messages).

Permisos: para ver los registros de todo el sistema, el usuario debe ser root o
pertenecer a los grupos 'adm' o 'systemd-journal'.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ...compat import elevation_hint, find_binary
from .common import LogAccessError, LogEvent, LogResult, run

PRIORITIES = {
    "0": "crítico",
    "1": "crítico",
    "2": "crítico",
    "3": "error",
    "4": "advertencia",
    "5": "información",
    "6": "información",
    "7": "información",
}

PERMISSION_HINT = "not seeing messages from other users"

Parser = Callable[[LogEvent], LogEvent | None]


# ---------------------------------------------------------------- intérpretes


def _with(event: LogEvent, message: str, **fields: str) -> LogEvent:
    event.message = message
    event.fields = {k: v for k, v in fields.items() if v}
    return event


_SSH_FAILED = re.compile(
    r"Failed (?P<method>password|publickey|keyboard-interactive/pam|none) for (?:invalid user )?"
    r"(?P<user>\S+) from (?P<origin>\S+)"
)
_PAM_FAILURE = re.compile(
    r"pam_unix\((?P<service>[\w-]+):auth\): authentication failure;.*?(?:rhost=(?P<origin>\S*))?"
    r"(?:\s+user=(?P<user>\S+))?\s*$"
)
_SUDO_WRONG = re.compile(r"^\s*(?P<user>\S+) : (?:\d+ )?incorrect password attempts?")
_SU_FAILED = re.compile(r"FAILED SU \(to (?P<target>\S+)\) (?P<user>\S+)")


def parse_failed_login(event: LogEvent) -> LogEvent | None:
    text = event.message
    if m := _SSH_FAILED.search(text):
        invalid = "invalid user" in text
        reason = (
            "el usuario no existe"
            if invalid
            else (
                "contraseña incorrecta"
                if m["method"] == "password"
                else f"autenticación rechazada ({m['method']})"
            )
        )
        return _with(
            event,
            f"Inicio de sesión SSH fallido de {m['user']}",
            user=m["user"],
            origin=m["origin"],
            logon_type="SSH (remoto)",
            reason=reason,
        )
    if (m := _SUDO_WRONG.search(text)) and event.source == "sudo":
        return _with(
            event,
            f"Contraseña de sudo incorrecta ({m['user']})",
            user=m["user"],
            origin="local",
            logon_type="sudo",
            reason="contraseña incorrecta",
        )
    if m := _SU_FAILED.search(text):
        return _with(
            event,
            f"'su' fallido de {m['user']} hacia {m['target']}",
            user=m["user"],
            origin="local",
            logon_type="su",
            reason="contraseña incorrecta",
        )
    # sshd ya registra 'Failed password': se ignora su línea PAM para no contar dos veces.
    if (m := _PAM_FAILURE.search(text)) and m["service"] != "sshd":
        return _with(
            event,
            f"Autenticación fallida en {m['service']}",
            user=m["user"] or "",
            origin=m["origin"] or "local",
            logon_type=m["service"],
            reason="contraseña incorrecta",
        )
    return None


_ACCOUNT_PATTERNS = [
    (re.compile(r"new user: name=(?P<user>[^,\s]+)"), "Cuenta de usuario creada"),
    (re.compile(r"new group: name=(?P<group>[^,\s]+)"), "Grupo creado"),
    (re.compile(r"delete user '(?P<user>[^']+)'"), "Cuenta eliminada"),
    (re.compile(r"removed group '(?P<group>[^']+)'"), "Grupo eliminado"),
    (
        re.compile(r"add '(?P<user>[^']+)' to (?:shadow )?group '(?P<group>[^']+)'"),
        "Miembro agregado a un grupo",
    ),
    (
        re.compile(r"user (?P<user>\S+) added by (?P<by>\S+) to group (?P<group>\S+)"),
        "Miembro agregado a un grupo",
    ),
    (re.compile(r"password changed for (?P<user>\S+)"), "Contraseña cambiada"),
    (re.compile(r"lock user '(?P<user>[^']+)' password"), "Cuenta bloqueada"),
]


def parse_account_change(event: LogEvent) -> LogEvent | None:
    for pattern, label in _ACCOUNT_PATTERNS:
        if m := pattern.search(event.message):
            return _with(event, label, **{k: v for k, v in m.groupdict().items() if v})
    return None


_SERVICE_FAILURE = re.compile(
    r"Failed to start (?P<unit>.+?)\.?$"
    r"|(?P<unit2>\S+): (?:Failed with result|Main process exited, code=(?:killed|dumped))"
)


def parse_service_failure(event: LogEvent) -> LogEvent | None:
    if m := _SERVICE_FAILURE.search(event.message):
        unit = (m["unit"] or m["unit2"] or "").strip()
        return _with(event, f"Falla del servicio {unit}", service=unit)
    return None


def parse_antivirus(event: LogEvent) -> LogEvent | None:
    if m := re.search(r"(?P<path>\S+): (?P<threat>\S+) FOUND", event.message):
        return _with(event, "ClamAV detectó malware", threat=m["threat"], path=m["path"])
    return None


def keep(event: LogEvent) -> LogEvent:
    return event


# ------------------------------------------------------------------- fuentes


@dataclass(frozen=True)
class Spec:
    journal_args: list[str]
    parser: Parser
    files: tuple[str, ...]


SPECS: dict[str, Spec] = {
    # SYSLOG_FACILITY 4 = auth, 10 = authpriv
    "logins_fallidos": Spec(
        ["SYSLOG_FACILITY=4", "SYSLOG_FACILITY=10"],
        parse_failed_login,
        ("/var/log/auth.log", "/var/log/secure"),
    ),
    "cuentas": Spec(
        ["SYSLOG_FACILITY=4", "SYSLOG_FACILITY=10"],
        parse_account_change,
        ("/var/log/auth.log", "/var/log/secure"),
    ),
    "errores": Spec(["-p", "3"], keep, ()),
    "servicios": Spec(["_PID=1"], parse_service_failure, ("/var/log/syslog", "/var/log/messages")),
    "antivirus": Spec(
        ["-u", "clamav-daemon", "-u", "clamonacc"], parse_antivirus, ("/var/log/clamav/clamav.log",)
    ),
}


def _journal_event(entry: dict) -> LogEvent:
    message = entry.get("MESSAGE", "")
    if isinstance(message, list):  # journalctl entrega bytes como lista de enteros
        message = bytes(message).decode("utf-8", errors="replace")
    micros = int(entry.get("__REALTIME_TIMESTAMP", "0") or 0)
    return LogEvent(
        time=datetime.fromtimestamp(micros / 1_000_000).isoformat(timespec="seconds") if micros else "",
        source=entry.get("SYSLOG_IDENTIFIER") or entry.get("_COMM") or entry.get("_SYSTEMD_UNIT", ""),
        level=PRIORITIES.get(str(entry.get("PRIORITY", "6")), "información"),
        message=str(message),
    )


def read_journal(spec: Spec, hours: int, max_events: int) -> LogResult:
    # Se piden más líneas de las necesarias porque luego se filtran por contenido.
    fetch = max_events if spec.parser is keep else min(max_events * 20, 20_000)
    code, out, err = run(
        [
            "journalctl",
            "--no-pager",
            "-o",
            "json",
            "--since",
            f"-{hours}h",
            "-n",
            str(fetch),
            *spec.journal_args,
        ]
    )
    if code != 0 and not out:
        raise LogAccessError(f"journalctl falló: {err.strip()[:200]}")
    events: list[LogEvent] = []
    for line in out.splitlines():
        try:
            parsed = spec.parser(_journal_event(json.loads(line)))
        except (ValueError, TypeError):
            continue
        if parsed is not None:
            events.append(parsed)
    notes = []
    if PERMISSION_HINT in err:
        notes.append(
            "Solo se ven los registros de tu usuario. Para ver los del sistema, agrégate al grupo "
            f"'adm' o 'systemd-journal' (sudo usermod -aG adm $USER) o {elevation_hint()}"
        )
    events = events[-max_events:]
    return LogResult(events, "journalctl", notes, truncated=len(events) >= max_events)


# --------------------------------------------------------- archivos clásicos

_SYSLOG_LINE = re.compile(
    r"^(?P<time>\d{4}-\d\d-\d\dT[\d:.]+(?:[+-]\d\d:?\d\d|Z)?|[A-Z][a-z]{2} [ \d]\d \d\d:\d\d:\d\d) "
    r"(?P<host>\S+) (?P<source>[^\s:\[]+)(?:\[\d+\])?: (?P<message>.*)$"
)


def _syslog_time(raw: str, now: datetime) -> datetime | None:
    try:
        if raw[0].isdigit():
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
        parsed = datetime.strptime(f"{now.year} {raw}", "%Y %b %d %H:%M:%S")
        # El formato clásico no trae año: si queda en el futuro, era del año anterior.
        return parsed.replace(year=now.year - 1) if parsed > now + timedelta(days=1) else parsed
    except ValueError:
        return None


def tail_lines(path: Path, count: int, block: int = 65536) -> list[str]:
    """Últimas `count` líneas sin leer el archivo entero (los logs pueden pesar GB)."""
    with path.open("rb") as fh:
        fh.seek(0, os.SEEK_END)
        position = fh.tell()
        data = b""
        while position > 0 and data.count(b"\n") <= count:
            step = min(block, position)
            position -= step
            fh.seek(position)
            data = fh.read(step) + data
    return data.decode("utf-8", errors="replace").splitlines()[-count:]


def read_files(spec: Spec, hours: int, max_events: int, now: datetime | None = None) -> LogResult:
    now = now or datetime.now()
    since = now - timedelta(hours=hours)
    path = next((Path(p) for p in spec.files if Path(p).is_file()), None)
    if path is None:
        raise LogAccessError("No se encontró journalctl ni archivos de registro conocidos en /var/log.")
    try:
        lines = tail_lines(path, 50_000)
    except PermissionError as exc:
        raise LogAccessError(f"Sin permiso para leer {path}. {elevation_hint()}") from exc
    events = []
    for line in lines:
        m = _SYSLOG_LINE.match(line)
        if not m:
            continue
        moment = _syslog_time(m["time"], now)
        if moment is None or moment < since:
            continue
        event = LogEvent(
            time=moment.isoformat(timespec="seconds"),
            source=m["source"],
            level="información",
            message=m["message"],
        )
        if (parsed := spec.parser(event)) is not None:
            events.append(parsed)
    events = events[-max_events:]
    return LogResult(events, str(path), truncated=len(events) >= max_events)


def read(category: str, hours: int, max_events: int) -> LogResult:
    spec = SPECS[category]
    if find_binary("journalctl"):
        result = read_journal(spec, hours, max_events)
        if result.events or not spec.files:
            return result
        # Algunas distribuciones siguen escribiendo auth.log aparte: se revisa también.
        try:
            from_files = read_files(spec, hours, max_events)
        except LogAccessError:
            return result
        from_files.notes = result.notes + from_files.notes
        return from_files if from_files.events else result
    if not spec.files:
        raise LogAccessError("Esta categoría necesita journalctl (systemd), que no está disponible.")
    return read_files(spec, hours, max_events)
