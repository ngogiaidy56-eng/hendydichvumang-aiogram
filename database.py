"""Atomic asynchronous JSON storage for one bot process / one instance."""
from __future__ import annotations

import asyncio
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JsonDatabase:
    """Small JSON store suitable for a single Render instance.

    This is intentionally not a multi-instance database. Use PostgreSQL before
    scaling horizontally or storing financial balances/transactions.
    """

    EVENT_LIMIT = 1_000
    USER_PAGE_LIMIT = 100

    def __init__(self, path: str | Path = "database.json") -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] = {"schema_version": 1, "users": {}, "events": []}
        self._initialized = False

    async def initialize(self) -> None:
        async with self._lock:
            if self._initialized:
                return
            await asyncio.to_thread(self.path.parent.mkdir, parents=True, exist_ok=True)
            if self.path.exists():
                try:
                    async with aiofiles.open(self.path, "r", encoding="utf-8") as file:
                        loaded = json.loads(await file.read())
                    if not isinstance(loaded, dict):
                        raise ValueError("database root must be an object")
                    users = loaded.get("users", {})
                    events = loaded.get("events", [])
                    if not isinstance(users, dict) or not isinstance(events, list):
                        raise ValueError("users must be an object and events must be a list")
                    safe_users = {
                        str(key): value
                        for key, value in users.items()
                        if str(key).isdigit() and isinstance(value, dict)
                    }
                    safe_events = [event for event in events if isinstance(event, dict)][-self.EVENT_LIMIT:]
                    self._data = {
                        "schema_version": 1,
                        "users": safe_users,
                        "events": safe_events,
                    }
                except (OSError, json.JSONDecodeError, ValueError) as exc:
                    raise RuntimeError(f"Không thể đọc dữ liệu JSON tại {self.path}: {exc}") from exc
            else:
                await self._write_locked()
            self._initialized = True

    async def _write_locked(self) -> None:
        temp_path = self.path.with_name(self.path.name + ".tmp")
        payload = json.dumps(self._data, ensure_ascii=False, indent=2)
        try:
            async with aiofiles.open(temp_path, "w", encoding="utf-8") as file:
                await file.write(payload)
                await file.flush()
            await asyncio.to_thread(os.replace, temp_path, self.path)
            if os.name == "posix":
                await asyncio.to_thread(os.chmod, self.path, 0o600)
        finally:
            if temp_path.exists():
                await asyncio.to_thread(temp_path.unlink, missing_ok=True)

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("JsonDatabase chưa được initialize().")

    async def upsert_user(self, telegram_user: Any) -> None:
        self._ensure_initialized()
        user_id = int(telegram_user.id)
        if user_id <= 0:
            raise ValueError("Telegram user ID phải là số nguyên dương.")
        now = utc_now()
        async with self._lock:
            current = self._data["users"].get(str(user_id), {})
            if not isinstance(current, dict):
                current = {}
            self._data["users"][str(user_id)] = {
                "telegram_id": user_id,
                "username": getattr(telegram_user, "username", None),
                "first_name": getattr(telegram_user, "first_name", None),
                "last_name": getattr(telegram_user, "last_name", None),
                "language_code": getattr(telegram_user, "language_code", None),
                "first_seen_at": current.get("first_seen_at", now),
                "last_seen_at": now,
            }
            await self._write_locked()

    async def add_event(
        self,
        telegram_id: int,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._ensure_initialized()
        user_id = int(telegram_id)
        if user_id <= 0:
            raise ValueError("Telegram user ID phải là số nguyên dương.")
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata phải là dict.")
        safe_metadata = deepcopy(metadata or {})
        json.dumps(safe_metadata, ensure_ascii=False)
        async with self._lock:
            self._data["events"].append({
                "telegram_id": user_id,
                "event_type": str(event_type)[:80],
                "metadata": safe_metadata,
                "created_at": utc_now(),
            })
            self._data["events"] = self._data["events"][-self.EVENT_LIMIT:]
            await self._write_locked()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        self._ensure_initialized()
        async with self._lock:
            value = self._data["users"].get(str(int(telegram_id)))
            return deepcopy(value) if isinstance(value, dict) else None

    async def list_users(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        self._ensure_initialized()
        safe_limit = max(1, min(int(limit), self.USER_PAGE_LIMIT))
        safe_offset = max(0, int(offset))
        async with self._lock:
            users = [deepcopy(user) for user in self._data["users"].values() if isinstance(user, dict)]
        users.sort(key=lambda item: str(item.get("last_seen_at", "")), reverse=True)
        return users[safe_offset:safe_offset + safe_limit]

    async def get_recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        self._ensure_initialized()
        safe_limit = max(1, min(int(limit), 100))
        async with self._lock:
            return deepcopy(self._data["events"][-safe_limit:][::-1])

    async def get_stats(self) -> dict[str, int]:
        self._ensure_initialized()
        async with self._lock:
            return {
                "users": len(self._data["users"]),
                "events_kept": len(self._data["events"]),
            }
