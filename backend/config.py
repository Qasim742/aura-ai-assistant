"""Simple environment-based configuration for the AURA backend."""

import os

APP_NAME = os.getenv("AURA_APP_NAME", "AURA API")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "AURA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
