"""Utilities for identifying provider rate limits without exposing provider details."""

import math
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Literal


def _exception_chain(error: Exception) -> Iterator[BaseException]:
    seen = set()
    current: Any = error
    while isinstance(current, BaseException) and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _duration_seconds(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
        return math.ceil(value)
    if not isinstance(value, str):
        return None

    value = value.strip()
    try:
        seconds = float(value)
        if math.isfinite(seconds) and seconds >= 0:
            return math.ceil(seconds)
    except ValueError:
        pass

    parts = re.fullmatch(
        r"(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m)?"
        r"(?:(\d+(?:\.\d+)?)s)?",
        value,
        re.IGNORECASE,
    )
    if parts and any(part is not None for part in parts.groups()):
        hours, minutes, remainder = (
            float(part or 0) for part in parts.groups()
        )
        seconds = hours * 3600 + minutes * 60 + remainder
        if math.isfinite(seconds):
            return math.ceil(seconds)
    return None


def _retry_after_header(value: Any) -> int | None:
    seconds = _duration_seconds(value)
    if seconds is not None:
        return seconds
    if not isinstance(value, str):
        return None
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0, math.ceil((retry_at - datetime.now(timezone.utc)).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return None


def _retry_from_message(message: str) -> int | None:
    prefix = r"(?:retry[- ]after|retry\s+in|try\s+again\s+in)\s+"
    compound = re.search(
        prefix + r"((?:\d+(?:\.\d+)?[hms])+)",
        message,
        re.IGNORECASE,
    )
    if compound:
        return _duration_seconds(compound.group(1))

    match = re.search(
        prefix + r"(\d+(?:\.\d+)?)\s*"
        r"(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b",
        message,
        re.IGNORECASE,
    )
    if not match:
        return None
    amount = float(match.group(1))
    if not math.isfinite(amount):
        return None
    unit = match.group(2).lower()
    multiplier = 3600 if unit.startswith(("h",)) else (
        60 if unit.startswith("m") else 1
    )
    return math.ceil(amount * multiplier)


def rate_limit_payload(
    error: Exception,
    service: Literal["llm", "stt"],
) -> dict[str, str | int | None] | None:
    """Return a safe API payload only when the exception represents HTTP 429."""
    chain = list(_exception_chain(error))
    is_rate_limited = any(
        getattr(item, "status_code", None) == 429
        or getattr(getattr(item, "response", None), "status_code", None) == 429
        or type(item).__name__ in {"RateLimitError", "RateLimitExceeded"}
        for item in chain
    )
    if not is_rate_limited:
        return None

    retry_after = None
    reset_values = []
    message_values = []
    for item in chain:
        response = getattr(item, "response", None)
        headers = getattr(response, "headers", None)
        if headers is not None:
            if retry_after is None:
                retry_after = _retry_after_header(headers.get("retry-after"))
            for header in (
                "x-ratelimit-reset-requests",
                "x-ratelimit-reset-tokens",
            ):
                reset = _duration_seconds(headers.get(header))
                if reset is not None:
                    reset_values.append(reset)

        body = getattr(item, "body", None)
        if isinstance(body, dict):
            metadata = [body]
            for nested_key in ("error", "metadata"):
                nested = body.get(nested_key)
                if isinstance(nested, dict):
                    metadata.append(nested)
            for details in metadata:
                for key in ("retry_after_seconds", "retry_after", "retryAfter"):
                    if retry_after is None:
                        retry_after = _retry_after_header(details.get(key))
                    if retry_after is not None:
                        break
                if retry_after is not None:
                    break

        message = str(getattr(item, "message", ""))
        if message:
            message_values.append(message)

    if retry_after is None and reset_values:
        retry_after = max(reset_values)
    if retry_after is None:
        for message in message_values:
            retry_after = _retry_from_message(message)
            if retry_after is not None:
                break

    service_message = (
        "The AI response limit has been reached."
        if service == "llm"
        else "The voice transcription limit has been reached."
    )
    return {
        "code": "RATE_LIMIT_EXCEEDED",
        "service": service,
        "message": service_message,
        "retry_after_seconds": retry_after,
    }
