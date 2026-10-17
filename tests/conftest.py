from __future__ import annotations

import pytest

from dui.agent import ToolContext
from dui.compat import SystemInfo
from dui.config import Settings
from dui.security import Scope


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


@pytest.fixture
def context(settings) -> ToolContext:
    system = SystemInfo(os="linux", os_version="6.0", python="3.12", user="test", admin=False)
    return ToolContext(settings=settings, scope=Scope(resolver=lambda host: ["93.184.216.34"]), system=system)


@pytest.fixture(autouse=True)
def _ignore_real_env_file(monkeypatch):
    """Las pruebas no deben depender del .env del desarrollador (ni usar su API key)."""
    monkeypatch.setattr("dui.config.load_dotenv", lambda *args, **kwargs: False)
