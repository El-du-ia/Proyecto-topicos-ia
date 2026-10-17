from pathlib import Path

from dui.config import DEFAULT_MODEL, Settings


def test_defaults():
    s = Settings.from_env({})
    assert s.model == DEFAULT_MODEL
    assert s.scope == [] and s.api_base is None and s.max_turns == 20
    assert s.reports_path == s.data_dir / "reports"


def test_reads_dui_variables():
    s = Settings.from_env(
        {
            "DUI_MODEL": '"ollama_chat/llama3.1"',
            "DUI_API_BASE": "http://localhost:11434",
            "DUI_TEMPERATURE": "0.2",
            "DUI_MAX_TURNS": "5",
            "DUI_SCOPE": "192.168.1.0/24, example.com;10.0.0.1",
            "DUI_DATA_DIR": "/tmp/dui",
            "DUI_REPORTS_DIR": "/tmp/reportes",
        }
    )
    assert s.model == "ollama_chat/llama3.1"
    assert s.api_base == "http://localhost:11434"
    assert s.temperature == 0.2 and s.max_turns == 5
    assert s.scope == ["192.168.1.0/24", "example.com", "10.0.0.1"]
    assert s.data_dir == Path("/tmp/dui") and s.reports_path == Path("/tmp/reportes")


def test_v1_cai_model_variable_still_works():
    assert Settings.from_env({"CAI_MODEL": "gemini/gemini-2.5-pro"}).model == "gemini/gemini-2.5-pro"
    env = {"CAI_MODEL": "gemini/x", "DUI_MODEL": "openai/y"}
    assert Settings.from_env(env).model == "openai/y"
