# AURA FastAPI backend

## Configuration

The agent loads `GROQ_API_KEY` from the project-root `.env` file. Copy
`backend\.env.example` to the project root as `.env` and set the key locally.
Do not put API keys in frontend environment variables. By default, CORS allows
the Vite development origins `http://localhost:5173` and
`http://127.0.0.1:5173`. Override them with a comma-separated
`AURA_CORS_ORIGINS` environment variable when needed.

## Start on Windows

From the project root:

```powershell
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

For microphone input, install the additional voice requirements with
`python -m pip install -r backend\requirements-voice.txt`. On Windows, PyAudio
may need Microsoft C++ Build Tools to compile if a compatible wheel is not
available. Text chat and the health endpoint do not require that microphone
dependency.

The API is available at `http://127.0.0.1:8000`; interactive documentation is
at `http://127.0.0.1:8000/docs`.

## Routes

- `GET /api/health` reports backend availability.
- `POST /api/chat` processes a message using its conversation's LangGraph thread.
- `GET /api/conversations/{conversation_id}` retrieves that agent thread's messages.
- `POST /api/voice/start`, `POST /api/voice/stop`, and `GET /api/voice/status` manage
  one microphone session at a time.
- `POST /api/voice/stop-speaking` reports when the active audio player cannot
  interrupt playback.

Voice listening depends on a working microphone and the optional voice
dependencies. The API reports voice startup errors instead of pretending that
the microphone is listening. A lost status heartbeat also stops the listener
after ten seconds; the frontend sends a best-effort stop request during page
exit or refresh.

Groq rate limits return a structured `RATE_LIMIT_EXCEEDED` error for chat
requests. Voice status includes the same rate-limit information for Whisper
transcription or LLM failures, including a retry duration only when the
provider supplies reliable timing metadata.
