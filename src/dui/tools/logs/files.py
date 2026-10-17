"""
Análisis de un archivo de log concreto (de una aplicación, servidor web, etc.).

Se lee solo el final del archivo y se rechazan archivos que suelen contener
secretos: su contenido se enviaría al modelo de IA.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from ...errors import ToolError
from .linux import tail_lines

PATTERNS: dict[str, tuple[str, list[str]]] = {
    "errores": (
        "Errores y fallos",
        [
            r"\berror\b",
            r"\bfail(?:ed|ure)?\b",
            r"\bcrash(?:ed)?\b",
            r"\bexception\b",
            r"\bcritical\b",
            r"\bfatal\b",
        ],
    ),
    "autenticacion": (
        "Autenticación",
        [
            r"failed password",
            r"authentication failure",
            r"invalid user",
            r"login failed",
            r"access denied",
            r"unauthorized",
            r"\b401\b",
            r"\b403\b",
        ],
    ),
    "sospechoso": (
        "Actividad sospechosa",
        [
            r"brute.?force",
            r"\.\./",
            r"union\s+select",
            r"<script",
            r"/etc/passwd",
            r"cmd\.exe",
            r"powershell\s+-enc",
            r"\bmalware\b",
            r"\bintrusion\b",
        ],
    ),
}

# Archivos que suelen guardar contraseñas o claves: no se analizan.
_SECRET_NAMES = re.compile(
    r"(^\.env|id_rsa|id_ecdsa|id_ed25519|\.pem$|\.key$|\.p12$|\.pfx$|^shadow$|^gshadow$|credentials|"
    r"^sam$|^security$|^system$|\.kdbx$|secrets?\.)",
    re.IGNORECASE,
)
_SECRET_DIRS = {".ssh", ".gnupg", ".aws", ".azure", ".kube"}
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def check_path(raw: str) -> Path:
    path = Path(raw.strip().strip('"').strip("'")).expanduser()
    if _SECRET_NAMES.search(path.name) or _SECRET_DIRS.intersection(p.lower() for p in path.parts):
        raise ToolError(
            f"Por seguridad no se analizan archivos que suelen contener contraseñas o claves ({path.name})."
        )
    if not path.exists():
        raise ToolError(f"No existe el archivo: {path}")
    if not path.is_file():
        raise ToolError(f"No es un archivo: {path}")
    return path


def analyze_file(raw_path: str, focus: str, max_lines: int) -> str:
    path = check_path(raw_path)
    max_lines = max(10, min(max_lines, 20_000))
    try:
        lines = tail_lines(path, max_lines)
    except PermissionError as exc:
        raise ToolError(
            f"Sin permiso para leer {path}. Puede requerir privilegios de administrador."
        ) from exc
    except OSError as exc:
        raise ToolError(f"No se pudo leer {path}: {exc}") from exc

    groups = PATTERNS if focus == "todo" else {focus: PATTERNS[focus]}
    compiled = {key: [re.compile(p, re.IGNORECASE) for p in pats] for key, (_, pats) in groups.items()}
    findings: dict[str, list[tuple[int, str]]] = {key: [] for key in groups}
    first_line = 1 + max(0, _count_lines(path) - len(lines)) if len(lines) >= max_lines else 1
    for offset, line in enumerate(lines):
        for key, regexes in compiled.items():
            if any(r.search(line) for r in regexes):
                findings[key].append((first_line + offset, line.strip()))

    out = [f"Análisis de {path.name} · últimas {len(lines)} líneas · ruta: {path}"]
    total = sum(len(v) for v in findings.values())
    if not total:
        out.append("No se encontraron eventos de interés con los patrones buscados.")
        return "\n".join(out)
    for key, hits in findings.items():
        if not hits:
            continue
        label = groups[key][0]
        out.append(f"\n{label}: {len(hits)} líneas")
        ips = Counter(ip for _, text in hits for ip in _IP.findall(text))
        if ips:
            out.append("  IPs más frecuentes: " + ", ".join(f"{ip} ({n})" for ip, n in ips.most_common(5)))
        for number, text in hits[-8:]:
            out.append(f"  línea {number}: {text[:200]}")
    return "\n".join(out)


def _count_lines(path: Path) -> int:
    with path.open("rb") as fh:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(1 << 20), b""))
