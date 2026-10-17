"""Herramientas de ciberseguridad multiplataforma."""

from ..agent.tools import Tool
from .logs import analyze_log_file, analyze_logs
from .recon import dns_lookup, reverse_dns, whois_lookup
from .reports import generate_report
from .system import local_connections, network_interfaces


def default_tools() -> list[Tool]:
    return [
        dns_lookup,
        reverse_dns,
        whois_lookup,
        network_interfaces,
        local_connections,
        analyze_logs,
        analyze_log_file,
        generate_report,
    ]


__all__ = [
    "analyze_log_file",
    "analyze_logs",
    "default_tools",
    "dns_lookup",
    "generate_report",
    "local_connections",
    "network_interfaces",
    "reverse_dns",
    "whois_lookup",
]
