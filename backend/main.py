"""FastAPI application for the AURA assistant."""
import traceback
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

if __package__:
    from .config import APP_NAME, CORS_ORIGINS
    from .rate_limits import rate_limit_payload
else:
    from config import APP_NAME, CORS_ORIGINS
    from rate_limits import rate_limit_payload


logger = logging.getLogger(__name__)
app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=128)
    conversation_type: Literal["text", "voice"]
    message: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


class ConversationMessage(BaseModel):
    sender: Literal["user", "aura"]
    text: str


class ConversationHistory(BaseModel):
    conversation_id: str
    messages: list[ConversationMessage]


class VoiceStartRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=128)
    conversation_type: Literal["voice"]


class VoiceStopRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=128)


class RateLimitNotification(BaseModel):
    code: Literal["RATE_LIMIT_EXCEEDED"]
    service: Literal["llm", "stt"]
    message: str
    retry_after_seconds: int | None = None


class VoiceStatus(BaseModel):
    conversation_id: str | None
    state: Literal["Idle", "Listening", "Thinking", "Speaking", "Error"]
    active: bool
    messages: list[dict[str, str]]
    error: str | None = None
    rate_limit: RateLimitNotification | None = None


def thread_id_for_conversation(conversation_id: str) -> str:
    """Map a browser conversation ID to a stable, isolated LangGraph thread."""
    return f"aura-{conversation_id}"


def _process_agent_message(message: str, conversation_id: str) -> str:
    from agent.agent import process_message

    return process_message(
        message,
        thread_id=thread_id_for_conversation(conversation_id),
        speak_response=False,
    )


def _get_agent_history(conversation_id: str) -> list[dict[str, str]]:
    from agent.agent import get_conversation_history

    return get_conversation_history(thread_id_for_conversation(conversation_id))


def _agent_unavailable(error: Exception) -> HTTPException:
    rate_limit = rate_limit_payload(error, "llm")
    if rate_limit:
        logger.warning(
            "AURA LLM request was rate limited (%s, status=%s)",
            type(error).__name__,
            getattr(error, "status_code", None),
        )
        return HTTPException(
            status_code=429,
            detail={"error": rate_limit},
        )
    traceback.print_exc()
    logger.warning("AURA agent request failed (%s)", type(error).__name__)
    if isinstance(error, (ImportError, ValueError)):
        return HTTPException(
            status_code=503,
            detail="AURA is not ready. Check its Python dependencies and backend configuration.",
        )
    return HTTPException(
        status_code=502,
        detail="AURA could not process the request. Please try again.",
    )


class VoiceSessionManager:
    """Own one microphone/agent/TTS worker for this local API process."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._conversation_id: str | None = None
        self._state: Literal["Idle", "Listening", "Thinking", "Speaking", "Error"] = "Idle"
        self._active = False
        self._error: str | None = None
        self._rate_limit: RateLimitNotification | None = None
        self._messages: list[dict[str, str]] = []
        self._stop_event: threading.Event | None = None
        self._worker: threading.Thread | None = None
        self._last_status_at = 0.0

    def snapshot(self, conversation_id: str | None = None) -> VoiceStatus:
        with self._lock:
            if conversation_id is not None and conversation_id != self._conversation_id:
                return VoiceStatus(
                    conversation_id=conversation_id,
                    state="Idle",
                    active=False,
                    messages=[],
                )
            if self._active and conversation_id == self._conversation_id:
                self._last_status_at = time.monotonic()
            return VoiceStatus(
                conversation_id=self._conversation_id,
                state=self._state,
                active=self._active,
                messages=list(self._messages),
                error=self._error,
                rate_limit=self._rate_limit,
            )

    def start(self, conversation_id: str) -> VoiceStatus:
        with self._lock:
            if self._worker and self._worker.is_alive():
                if self._conversation_id == conversation_id:
                    return self.snapshot(conversation_id)
                raise HTTPException(
                    status_code=409,
                    detail="Another voice conversation is already active.",
                )

            self._conversation_id = conversation_id
            self._state = "Idle"
            self._active = True
            self._error = None
            self._rate_limit = None
            self._messages = []
            self._last_status_at = time.monotonic()
            self._stop_event = threading.Event()
            self._worker = threading.Thread(
                target=self._run,
                args=(conversation_id, self._stop_event),
                name="aura-voice-session",
                daemon=True,
            )
            self._worker.start()
            return self.snapshot(conversation_id)

    def stop(self, conversation_id: str) -> VoiceStatus:
        with self._lock:
            if self._conversation_id is None or not self._active:
                return self.snapshot(conversation_id)
            if self._conversation_id != conversation_id:
                raise HTTPException(
                    status_code=409,
                    detail="The requested conversation does not own the active voice session.",
                )
            if self._stop_event:
                self._stop_event.set()
            return self.snapshot(conversation_id)

    def _set_state(
        self,
        state: Literal["Idle", "Listening", "Thinking", "Speaking", "Error"],
    ) -> None:
        with self._lock:
            self._state = state

    def _client_disconnected(self, stop_event: threading.Event) -> bool:
        with self._lock:
            disconnected = time.monotonic() - self._last_status_at > 10
        if disconnected:
            stop_event.set()
        return disconnected

    def _append_message(self, sender: Literal["user", "aura"], text: str) -> None:
        with self._lock:
            self._messages.append(
                {
                    "id": str(uuid4()),
                    "sender": sender,
                    "text": text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def _run(self, conversation_id: str, stop_event: threading.Event) -> None:
        service = "stt"
        try:
            from agent.agent import listen, process_message, speak

            while not stop_event.is_set():
                service = "stt"
                recognized_text = listen(
                    stop_event=stop_event,
                    on_listening=lambda: self._set_state("Listening"),
                    on_transcribing=lambda: self._set_state("Thinking"),
                    should_stop=lambda: self._client_disconnected(stop_event),
                    raise_errors=True,
                )
                if stop_event.is_set():
                    break
                if not recognized_text:
                    continue

                self._append_message("user", recognized_text)
                service = "llm"
                self._set_state("Thinking")
                answer = process_message(
                    recognized_text,
                    thread_id=thread_id_for_conversation(conversation_id),
                    speak_response=False,
                )
                if answer.strip():
                    self._append_message("aura", answer)
                    if stop_event.is_set():
                        break
                    self._set_state("Speaking")
                    service = "tts"
                    speak(answer, strict=True)
        except Exception as error:
            rate_limit = (
                rate_limit_payload(error, service)
                if service in {"stt", "llm"}
                else None
            )
            logger.warning(
                "AURA voice session failed (%s, service=%s, status=%s)",
                type(error).__name__,
                service,
                getattr(error, "status_code", None),
            )
            with self._lock:
                self._state = "Error"
                if rate_limit:
                    self._rate_limit = RateLimitNotification(**rate_limit)
                    self._error = None
                elif (
                    isinstance(error, (ImportError, ValueError))
                    or (
                        isinstance(error, AttributeError)
                        and "pyaudio" in str(error).lower()
                    )
                ):
                    self._error = (
                        "Voice is unavailable. Install the optional microphone "
                        "dependencies and check the backend configuration."
                    )
                else:
                    self._rate_limit = None
                    self._error = "The voice session encountered an error."
        finally:
            with self._lock:
                self._active = False
                if self._state != "Error":
                    self._state = "Idle"


voice_sessions = VoiceSessionManager()


@app.get("/")
def read_root() -> dict[str, str]:
    """Describe the AURA API."""
    return {"message": "AURA API", "description": "The backend API for the AURA assistant."}


@app.get("/health")
@app.get("/api/health")
def read_health() -> dict[str, str]:
    """Return a simple service health status."""
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message must not be empty.")
    try:
        response = await run_in_threadpool(
            _process_agent_message,
            request.message,
            request.conversation_id,
        )
    except Exception as error:
        raise _agent_unavailable(error) from error
    return ChatResponse(conversation_id=request.conversation_id, response=response)


@app.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationHistory,
)
async def get_conversation(conversation_id: str) -> ConversationHistory:
    if not conversation_id or len(conversation_id) > 128:
        raise HTTPException(status_code=422, detail="Invalid conversation ID.")
    try:
        messages = await run_in_threadpool(_get_agent_history, conversation_id)
    except Exception as error:
        raise _agent_unavailable(error) from error
    return ConversationHistory(conversation_id=conversation_id, messages=messages)


@app.post("/api/voice/start", response_model=VoiceStatus, status_code=202)
def start_voice(request: VoiceStartRequest) -> VoiceStatus:
    return voice_sessions.start(request.conversation_id)


@app.post("/api/voice/stop", response_model=VoiceStatus)
def stop_voice(request: VoiceStopRequest) -> VoiceStatus:
    return voice_sessions.stop(request.conversation_id)


@app.post("/api/voice/stop-speaking")
def stop_speaking(request: VoiceStopRequest) -> dict[str, str]:
    status = voice_sessions.snapshot(request.conversation_id)
    if status.state == "Speaking" and status.active:
        raise HTTPException(
            status_code=409,
            detail="Speech playback cannot be interrupted by the current audio player.",
        )
    return {"status": "idle", "message": "No interruptible speech is playing."}


@app.get("/api/voice/status", response_model=VoiceStatus)
def get_voice_status(
    conversation_id: str | None = Query(default=None, min_length=1, max_length=128),
) -> VoiceStatus:
    return voice_sessions.snapshot(conversation_id)
