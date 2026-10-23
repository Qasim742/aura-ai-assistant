import sys
import threading
from types import ModuleType, SimpleNamespace

from fastapi.testclient import TestClient
from groq import RateLimitError
from httpx import Request, Response

from backend import main
from backend.rate_limits import rate_limit_payload


class ProviderError(Exception):
    def __init__(self, status_code, headers=None, message="provider error"):
        super().__init__(message)
        self.status_code = status_code
        self.response = SimpleNamespace(
            status_code=status_code,
            headers=headers or {},
        )
        self.message = message


def test_rate_limit_uses_retry_after_header():
    error = ProviderError(429, {"retry-after": "75"})

    assert rate_limit_payload(error, "llm") == {
        "code": "RATE_LIMIT_EXCEEDED",
        "service": "llm",
        "message": "The AI response limit has been reached.",
        "retry_after_seconds": 75,
    }


def test_installed_groq_rate_limit_error_is_recognized():
    response = Response(
        429,
        headers={"retry-after": "12"},
        request=Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )
    error = RateLimitError(
        "Rate limit exceeded",
        response=response,
        body={"error": {"message": "provider response"}},
    )

    assert rate_limit_payload(error, "llm")["retry_after_seconds"] == 12


def test_rate_limit_uses_groq_reset_header_and_unknown_is_none():
    error = ProviderError(429, {"x-ratelimit-reset-requests": "1m2.2s"})
    unknown = ProviderError(429)

    assert rate_limit_payload(error, "stt")["retry_after_seconds"] == 63
    assert rate_limit_payload(unknown, "stt")["retry_after_seconds"] is None


def test_unrelated_http_errors_are_not_rate_limits():
    error = ProviderError(401, message="retry after 20 seconds")

    assert rate_limit_payload(error, "llm") is None


def test_rate_limit_retry_duration_can_be_extracted_from_exception_message():
    error = ProviderError(429, message="Please try again in 2 minutes.")
    compound = ProviderError(429, message="Retry after 1m2.5s.")

    assert rate_limit_payload(error, "stt")["retry_after_seconds"] == 120
    assert rate_limit_payload(compound, "stt")["retry_after_seconds"] == 63


def test_chat_endpoint_returns_safe_structured_rate_limit(monkeypatch):
    def rate_limited_message(*args, **kwargs):
        raise ProviderError(
            429,
            {"retry-after": "30"},
            "provider detail that must not be exposed",
        )

    monkeypatch.setattr(main, "_process_agent_message", rate_limited_message)
    response = TestClient(main.app).post(
        "/api/chat",
        json={
            "conversation_id": "test-chat",
            "conversation_type": "text",
            "message": "Hello",
        },
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": {
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "service": "llm",
                "message": "The AI response limit has been reached.",
                "retry_after_seconds": 30,
            }
        }
    }


def test_voice_session_exposes_stt_rate_limit_in_status(monkeypatch):
    fake_agent = ModuleType("agent.agent")

    def rate_limited_transcription(*args, **kwargs):
        raise ProviderError(429, {"retry-after": "45"})

    fake_agent.listen = rate_limited_transcription
    fake_agent.process_message = lambda *args, **kwargs: ""
    fake_agent.speak = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "agent.agent", fake_agent)

    manager = main.VoiceSessionManager()
    manager._conversation_id = "voice-session"
    manager._run("voice-session", threading.Event())
    status = manager.snapshot("voice-session")

    assert status.rate_limit is not None
    assert status.rate_limit.service == "stt"
    assert status.rate_limit.retry_after_seconds == 45
