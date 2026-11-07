"""Small helpers for safely presenting upstream JSON to Telegram operators/users."""
from __future__ import annotations

from typing import Any

SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "private_key",
    "refresh_key",
)


def redact_sensitive(value: Any) -> Any:
    """Return a deep, JSON-friendly copy with credential-like fields masked."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower().replace("-", "_")
            if any(part in key_text for part in SENSITIVE_KEY_PARTS):
                cleaned[str(key)] = "[đã ẩn]"
            else:
                cleaned[str(key)] = redact_sensitive(item)
        return cleaned
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item) for item in value]
    return value
