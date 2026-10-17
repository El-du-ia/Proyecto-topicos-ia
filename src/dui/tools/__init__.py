"""Herramientas de ciberseguridad multiplataforma."""

from ..agent.tools import Tool
from .recon import dns_lookup, reverse_dns, whois_lookup
from .reports import generate_report


def default_tools() -> list[Tool]:
    return [dns_lookup, reverse_dns, whois_lookup, generate_report]


__all__ = ["default_tools", "dns_lookup", "generate_report", "reverse_dns", "whois_lookup"]
