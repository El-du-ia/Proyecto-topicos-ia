"""Prueba el cliente LiteLLM real usando sus respuestas simuladas (sin red ni API key)."""

import functools

import litellm
import pytest

from dui.agent import LiteLLMClient
from dui.errors import LLMError


def with_mock(monkeypatch, **mock):
    original = litellm.completion
    monkeypatch.setattr(litellm, "completion", functools.partial(original, **mock))


def test_text_response(monkeypatch):
    with_mock(monkeypatch, mock_response="Hola desde el modelo")
    response = LiteLLMClient("gemini/gemini-2.5-flash").complete([{"role": "user", "content": "hola"}], [])
    assert response.content == "Hola desde el modelo"
    assert response.tool_calls == []
    assert response.to_message() == {"role": "assistant", "content": "Hola desde el modelo"}


def test_tool_call_response(monkeypatch):
    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "dns_lookup", "arguments": '{"domain": "example.com"}'},
        }
    ]
    with_mock(monkeypatch, mock_response="", mock_tool_calls=tool_calls)
    response = LiteLLMClient("openai/gpt-4o-mini").complete([{"role": "user", "content": "x"}], [])
    assert [(c.name, c.arguments) for c in response.tool_calls] == [
        ("dns_lookup", '{"domain": "example.com"}')
    ]
    assert response.to_message()["tool_calls"][0]["function"]["name"] == "dns_lookup"


def test_provider_errors_become_friendly_llm_errors(monkeypatch):
    def fail(**kwargs):
        raise litellm.AuthenticationError("invalid key", llm_provider="gemini", model=kwargs["model"])

    monkeypatch.setattr(litellm, "completion", fail)
    with pytest.raises(LLMError, match="API key de 'gemini'"):
        LiteLLMClient("gemini/gemini-2.5-flash").complete([{"role": "user", "content": "x"}], [])


def test_missing_api_key_hint_even_if_reported_as_connection_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(LLMError, match="Revisa la API key") as info:
        LiteLLMClient("gemini/gemini-2.5-flash").complete([{"role": "user", "content": "x"}], [])
    assert "ollama serve" not in str(info.value)
