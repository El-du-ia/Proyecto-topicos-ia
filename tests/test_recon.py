"""Pruebas de las herramientas de reconocimiento, sin acceso real a la red."""

import socket

import httpx
import pytest

from dui.agent import ToolError
from dui.tools import recon
from dui.tools.recon import dns_lookup, normalize_domain, reverse_dns, whois_lookup

RDAP_DOMAIN = {
    "ldhName": "EXAMPLE.COM",
    "status": ["active"],
    "events": [
        {"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2027-08-13T04:00:00Z"},
    ],
    "entities": [
        {
            "roles": ["registrar"],
            "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "IANA"]]],
        }
    ],
    "nameservers": [{"ldhName": "A.IANA-SERVERS.NET"}],
    "secureDNS": {"delegationSigned": True},
}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM", "example.com"),
        ("https://example.com/path?q=1", "example.com"),
        ("example.com.", "example.com"),
        ("example.com:8080", "example.com"),
        ("münchen.de", "xn--mnchen-3ya.de"),
    ],
)
def test_normalize_domain(raw, expected):
    assert normalize_domain(raw) == expected


@pytest.mark.parametrize("raw", ["localhost", "-bad.com", "a b.com", ""])
def test_normalize_domain_rejects_invalid(raw):
    with pytest.raises(ToolError):
        normalize_domain(raw)


def test_whois_formats_rdap(monkeypatch):
    monkeypatch.setattr(recon, "_rdap", lambda kind, value: RDAP_DOMAIN)
    out = whois_lookup.invoke({"target": "example.com"})
    assert "Registrador: IANA" in out
    assert "Creado: 1995-08-14" in out and "Expira: 2027-08-13" in out
    assert "a.iana-servers.net" in out and "DNSSEC: activado" in out


def test_whois_falls_back_to_port_43(monkeypatch):
    def not_found(kind, value):
        request = httpx.Request("GET", "https://rdap.org")
        raise httpx.HTTPStatusError("404", request=request, response=httpx.Response(404, request=request))

    monkeypatch.setattr(recon, "_rdap", not_found)
    monkeypatch.setattr(recon, "_whois43", lambda q: "Domain Name: ejemplo.mx\nRegistrar: X")
    out = whois_lookup.invoke({"target": "ejemplo.mx"})
    assert "WHOIS clásico" in out and "Registrar: X" in out


def test_whois_reports_total_failure(monkeypatch):
    def offline(kind, value):
        raise httpx.ConnectError("sin red")

    def no_socket(q):
        raise OSError("sin red")

    monkeypatch.setattr(recon, "_rdap", offline)
    monkeypatch.setattr(recon, "_whois43", no_socket)
    with pytest.raises(ToolError, match="WHOIS clásico falló"):
        whois_lookup.invoke({"target": "example.com"})


def test_whois_detects_ip(monkeypatch):
    seen = {}

    def fake(kind, value):
        seen["kind"] = kind
        return {"startAddress": "8.8.8.0", "endAddress": "8.8.8.255", "name": "GOGL", "events": []}

    monkeypatch.setattr(recon, "_rdap", fake)
    assert "GOGL" in whois_lookup.invoke({"target": "8.8.8.8"})
    assert seen["kind"] == "ip"


def test_reverse_dns(monkeypatch):
    monkeypatch.setattr(socket, "gethostbyaddr", lambda ip: ("dns.google", [], [ip]))
    assert "dns.google" in reverse_dns.invoke({"ip_address": "8.8.8.8"})

    def missing(ip):
        raise socket.herror()

    monkeypatch.setattr(socket, "gethostbyaddr", missing)
    assert "No hay registro" in reverse_dns.invoke({"ip_address": "10.0.0.1"})
    with pytest.raises(ToolError):
        reverse_dns.invoke({"ip_address": "999.1.1.1"})


def test_dns_lookup_sorts_mx_by_preference(monkeypatch):
    import dns.resolver

    class MX:
        def __init__(self, pref, host):
            self.preference, self.host = pref, host

        def to_text(self):
            return f"{self.preference} {self.host}"

    class Answer(list):
        rrset = type("R", (), {"ttl": 300})()

    monkeypatch.setattr(dns.resolver, "resolve", lambda *a, **k: Answer([MX(20, "b."), MX(5, "a.")]))
    out = dns_lookup.invoke({"domain": "gmail.com", "record_type": "MX"})
    assert out.splitlines()[1:] == ["  - 5 a.", "  - 20 b."]
    assert "TTL 300" in out


def test_dns_lookup_falls_back_to_system_resolver(monkeypatch):
    import dns.resolver

    def broken(*a, **k):
        raise dns.resolver.NoNameservers()

    monkeypatch.setattr(dns.resolver, "resolve", broken)
    monkeypatch.setattr(recon, "_system_resolve", lambda d, t: ["93.184.216.34"])
    assert "93.184.216.34" in dns_lookup.invoke({"domain": "example.com"})
    with pytest.raises(ToolError):
        dns_lookup.invoke({"domain": "example.com", "record_type": "MX"})
