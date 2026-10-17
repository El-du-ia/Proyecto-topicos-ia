"""Análisis de registros: cada backend se prueba con salidas simuladas (corre en cualquier SO)."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from dui.agent import ToolError
from dui.tools import logs as logs_tool
from dui.tools.logs import analyze_log_file, analyze_logs, common, linux, macos, windows
from dui.tools.logs.common import LogAccessError, LogEvent, LogResult, decode, summarize

# ------------------------------------------------------------------- Windows

EVENT_4625 = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System>
<Provider Name='Microsoft-Windows-Security-Auditing'/><EventID>4625</EventID><Level>0</Level>
<TimeCreated SystemTime='2026-10-16T12:38:58.5103885Z'/></System><EventData>
<Data Name='TargetUserName'>admin</Data><Data Name='TargetDomainName'>PC</Data>
<Data Name='Status'>0xc000006d</Data><Data Name='SubStatus'>0xC000006A</Data>
<Data Name='LogonType'>10</Data><Data Name='WorkstationName'>ATACANTE</Data>
<Data Name='IpAddress'>203.0.113.9</Data></EventData>
<RenderingInfo Culture='es-ES'><Message>Error de inicio de sesión de una cuenta.

Sujeto: ...</Message></RenderingInfo></Event>"""

EVENT_7045 = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System>
<Provider Name='Service Control Manager'/><EventID Qualifiers='16384'>7045</EventID><Level>4</Level>
<TimeCreated SystemTime='2026-10-15T08:00:00.0000000Z'/></System><EventData>
<Data Name='ServiceName'>Updater</Data><Data Name='ImagePath'>C:\\Users\\x\\AppData\\Temp\\u.exe</Data>
<Data Name='AccountName'>LocalSystem</Data></EventData></Event>"""

EVENT_DEFENDER = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'><System>
<Provider Name='Microsoft-Windows-Windows Defender'/><EventID>1116</EventID><Level>3</Level>
<TimeCreated SystemTime='2026-10-15T09:00:00Z'/></System><EventData>
<Data Name='Threat Name'>Trojan:Win32/Test</Data><Data Name='Severity Name'>Grave</Data>
<Data Name='Path'>file:_C:\\x.exe</Data><Data Name='Action Name'>Cuarentena</Data></EventData></Event>"""


def test_windows_parses_failed_logon_with_meaningful_fields():
    (event,) = windows.parse_events(EVENT_4625)
    assert event.event_id == "4625" and event.source == "Microsoft-Windows-Security-Auditing"
    assert event.fields == {
        "user": "PC\\admin",
        "origin": "203.0.113.9",
        "logon_type": "escritorio remoto (RDP)",
        "reason": "contraseña incorrecta",
    }
    assert event.message == "Inicio de sesión fallido de PC\\admin"
    assert event.time.startswith("2026-10-16")


def test_windows_parses_service_and_defender_events():
    service, defender = windows.parse_events(EVENT_7045 + "\n" + EVENT_DEFENDER)
    assert service.message == "Servicio instalado: Updater" and service.fields["path"].endswith("u.exe")
    assert defender.fields["threat"] == "Trojan:Win32/Test" and defender.level == "advertencia"


def test_windows_local_time_handles_7_decimals():
    assert windows.local_time("2026-10-16T12:38:58.5103885Z")[:4] == "2026"
    assert windows.local_time("basura") == "basura"


def test_windows_read_builds_query_and_reports_permissions(monkeypatch):
    calls = []

    def fake_run(command, timeout=60):
        calls.append(command)
        return 0, EVENT_4625, ""

    monkeypatch.setattr(windows, "run", fake_run)
    result = windows.read("logins_fallidos", 24, 50)
    assert len(result.events) == 1 and result.origin == "Visor de eventos: Security"
    command = calls[0]
    assert command[:3] == ["wevtutil", "qe", "Security"]
    assert "EventID=4625" in command[3] and "timediff(@SystemTime) <= 86400000" in command[3]
    assert "/c:50" in command and "/f:RenderedXml" in command

    monkeypatch.setattr(windows, "run", lambda c, timeout=60: (5, "", "Acceso denegado."))
    with pytest.raises(LogAccessError, match="Administrador"):
        windows.read("logins_fallidos", 24, 50)
    monkeypatch.setattr(windows, "run", lambda c, timeout=60: (15007, "", ""))
    with pytest.raises(LogAccessError, match="no existe"):
        windows.read("antivirus", 24, 50)


# --------------------------------------------------------------------- Linux


@pytest.mark.parametrize(
    ("source", "message", "expected"),
    [
        (
            "sshd",
            "Failed password for invalid user oracle from 198.51.100.7 port 4022 ssh2",
            {"user": "oracle", "origin": "198.51.100.7", "reason": "el usuario no existe"},
        ),
        (
            "sshd",
            "Failed password for root from 198.51.100.7 port 4022 ssh2",
            {"user": "root", "origin": "198.51.100.7", "reason": "contraseña incorrecta"},
        ),
        ("sudo", "  ana : 3 incorrect password attempts ; TTY=pts/0", {"user": "ana", "logon_type": "sudo"}),
        ("su", "FAILED SU (to root) ana on pts/1", {"user": "ana", "logon_type": "su"}),
        (
            "login",
            "pam_unix(login:auth): authentication failure; logname= uid=0 euid=0 tty=tty1 ruser= rhost=  user=bob",
            {"user": "bob", "logon_type": "login"},
        ),
    ],
)
def test_linux_failed_login_patterns(source, message, expected):
    event = linux.parse_failed_login(LogEvent("2026-10-16T10:00:00", source, "información", message))
    assert event is not None
    for key, value in expected.items():
        assert event.fields[key] == value


def test_linux_ignores_duplicate_sshd_pam_lines_and_noise():
    pam_sshd = "pam_unix(sshd:auth): authentication failure; logname= uid=0 rhost=198.51.100.7 user=root"
    assert linux.parse_failed_login(LogEvent("", "sshd", "", pam_sshd)) is None
    assert linux.parse_failed_login(LogEvent("", "sshd", "", "Accepted password for ana")) is None


def test_linux_account_and_service_patterns():
    created = linux.parse_account_change(LogEvent("", "useradd", "", "new user: name=backdoor, UID=1001"))
    added = linux.parse_account_change(LogEvent("", "usermod", "", "add 'backdoor' to group 'sudo'"))
    failed = linux.parse_service_failure(LogEvent("", "systemd", "", "nginx.service: Failed with result 'exit-code'."))
    assert created.fields == {"user": "backdoor"} and created.message == "Cuenta de usuario creada"
    assert added.fields == {"user": "backdoor", "group": "sudo"}
    assert failed.fields == {"service": "nginx.service"}


def _journal_line(message, ident="sshd", priority=6, ts=1_792_000_000_000_000):
    return json.dumps(
        {"MESSAGE": message, "SYSLOG_IDENTIFIER": ident, "PRIORITY": str(priority), "__REALTIME_TIMESTAMP": str(ts)}
    )


def test_linux_journal_read_filters_and_reports_permission_hint(monkeypatch):
    out = "\n".join(
        [
            _journal_line("Failed password for root from 198.51.100.7 port 1 ssh2"),
            _journal_line("Accepted publickey for ana"),
            _journal_line(list(b"Failed password for bob from 10.0.0.2 port 2 ssh2")),  # bytes en JSON
            "no es json",
        ]
    )
    calls = []

    def fake_run(command, timeout=60):
        calls.append(command)
        return 0, out, "Hint: You are currently not seeing messages from other users and the system."

    monkeypatch.setattr(linux, "run", fake_run)
    result = linux.read_journal(linux.SPECS["logins_fallidos"], 24, 100)
    assert [e.fields["user"] for e in result.events] == ["root", "bob"]
    assert "grupo" in result.notes[0]
    assert "SYSLOG_FACILITY=4" in calls[0] and "--since" in calls[0] and "-24h" in calls[0]


def test_linux_auth_log_file_with_time_filter_and_year_rollover(