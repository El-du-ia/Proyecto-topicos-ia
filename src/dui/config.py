"""
Configuración de dui-IA.

Se lee de variables de entorno y de un archivo .env en el directorio actual.
Cualquier modelo soportado por LiteLLM sirve (en la nube o local), por ejemplo:

    DUI_MODEL=gemini/gemini-2.5-flash          (requiere GEMINI_API_KEY)
    DUI_MODEL=openai/gpt-4o-mini               (requiere OPENAI_API_KEY)
    DUI_MODEL=anthropic/claude-sonnet-5-5      (requiere ANTHROPIC_API_KEY)
    DUI_MODEL=ollama_chat/llama3.1             (local, DUI_API_BASE=http://localhost:11434)
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from platformdirs import user_data_dir

APP_NAME = "dui-IA"
DEFAULT_MODEL = "gemini/gemini-2.5-flash"


def _first(env: Mapping[str, str], *names: str) -> str | None:
    """Primer valor no vacío entre varias variables (permite nombres heredados de v1)."""
    for name in names:
        value = env.get(name, "").strip().strip('"').strip("'")
        if value:
            return value
    return None


def _split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]


@dataclass
class Settings:
    model: str = DEFAULT_MODEL
    api_base: str | None = None
    temperature: float | None = None
    max_turns: int = 20
    # Máximo de mensajes anteriores que se envían al modelo (las sesiones largas se recortan).
    max_history: int = 60
    # Objetivos que se pueden analizar de forma activa. Vacío = solo redes privadas.
    scope: list[str] = field(default_factory=list)
    data_dir: Path = field(default_factory=lambda: Path(user_data_dir(APP_NAME, appauthor=False)))
    reports_dir: Path | None = None

    @property
    def reports_path(self) -> Path:
        return self.reports_dir or self.data_dir / "reports"

    @property
    def db_path(self) -> Path:
        """Base de datos con sesiones, mensajes y auditoría."""
        return self.data_dir / "dui.db"

    @property
    def exports_path(self) -> Path:
        return self.data_dir / "exports"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, load_env_file: bool = True) -> Settings:
        if env is None:
            if load_env_file:
                load_dotenv(find_dotenv(usecwd=True), override=False)
            env = os.environ

        settings = cls()
        settings.model = _first(env, "DUI_MODEL", "CAI_MODEL") or DEFAULT_MODEL
        settings.api_base = _first(env, "DUI_API_BASE")
        if temperature := _first(env, "DUI_TEMPERATURE"):
            settings.temperature = float(temperature)
        if max_turns := _first(env, "DUI_MAX_TURNS"):
            settings.max_turns = int(max_turns)
        if max_history := _first(env, "DUI_MAX_HISTORY"):
            settings.max_history = int(max_history)
        settings.scope = _split_list(_first(env, "DUI_SCOPE"))
        if data_dir := _first(env, "DUI_DATA_DIR"):
            settings.data_dir = Path(data_dir).expanduser()
        if reports_dir := _first(env, "DUI_REPORTS_DIR"):
            settings.reports_dir = Path(reports_dir).expanduser()
        return settings
