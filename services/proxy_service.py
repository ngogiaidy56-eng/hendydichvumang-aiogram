"""Safe HTTP adapter for installation-specific HomeProxy Hub APIs.

The actual API contract must come from the operator's HomeProxy Hub documentation.
This adapter deliberately does not invent routes, payload formats, or auth schemes.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlparse

import aiohttp

from config import Settings


class ProxyServiceError(RuntimeError):
    """Safe-to-display error raised by the HomeProxy adapter."""


class ProxyService:
    MAX_RESPONSE_BYTES = 64 * 1024

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session: aiohttp.ClientSession | None = None

    @property
    def is_configured(self) -> bool:
        return self.settings.proxy_api_configured

    @property
    def route_is_configured(self) -> bool:
        return self.is_configured and bool(self.settings.proxy_route_path)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.settings.proxy_timeout_seconds)
            connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    def _build_url(self, path: str) -> str:
        if not self.is_configured:
            raise ProxyServiceError(
                "HomeProxy Hub chưa được cấu hình. Hãy khai báo HOME_PROXY_HUB_API_URL và HOME_PROXY_HUB_API_TOKEN."
            )
        if not path:
            raise ProxyServiceError("Thiếu đường dẫn API. Hãy cấu hình biến HOME_PROXY_*_PATH theo tài liệu nhà cung cấp.")
        parsed = urlparse(path)
        segments = parsed.path.split("/")
        if (
            parsed.scheme
            or parsed.netloc
            or not path.startswith("/")
            or path.startswith("//")
            or parsed.query
            or parsed.fragment
            or ".." in segments
            or "\\" in path
        ):
            raise ProxyServiceError("API path không hợp lệ; chỉ chấp nhận đường dẫn tương đối an toàn bắt đầu bằng '/'.")
        return f"{self.settings.proxy_api_url}{path}"

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        url = self._build_url(path)
        headers = {"Accept": "application/json"}
        scheme = self.settings.proxy_auth_scheme
        token = self.settings.proxy_api_token
        headers["Authorization"] = f"{scheme} {token}" if scheme else token
        session = await self._get_session()
        try:
            async with session.request(
                method,
                url,
                json=payload,
                params=params,
                headers=headers,
                allow_redirects=False,
            ) as response:
                if 300 <= response.status < 400:
                    raise ProxyServiceError("HomeProxy Hub trả về redirect; hãy kiểm tra URL API cấu hình.")
                if response.status >= 400:
                    raise ProxyServiceError(f"HomeProxy Hub trả về HTTP {response.status}.")
                raw = await response.content.read(self.MAX_RESPONSE_BYTES + 1)
                if len(raw) > self.MAX_RESPONSE_BYTES:
                    raise ProxyServiceError("Phản hồi HomeProxy Hub vượt quá giới hạn 64 KB.")
                if not raw.strip():
                    return {"ok": True, "status": response.status}
                try:
                    return json.loads(raw.decode(response.charset or "utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return {
                        "ok": True,
                        "status": response.status,
                        "message": "API đã phản hồi dữ liệu không phải JSON; nội dung đã được ẩn.",
                    }
        except ProxyServiceError:
            raise
        except asyncio.TimeoutError as exc:
            raise ProxyServiceError("Kết nối HomeProxy Hub quá thời gian chờ.") from exc
        except aiohttp.ClientError as exc:
            raise ProxyServiceError("Không thể kết nối HomeProxy Hub. Hãy kiểm tra URL, mạng và TLS.") from exc

    async def get_status(self) -> Any:
        return await self._request("GET", self.settings.proxy_status_path)

    async def get_credit(self, telegram_id: int) -> Any:
        user_id = int(telegram_id)
        if user_id <= 0:
            raise ValueError("Telegram user ID không hợp lệ.")
        return await self._request(
            "GET",
            self.settings.proxy_credit_path,
            params={"telegram_user_id": str(user_id)},
        )

    async def set_route(self, telegram_id: int, username: str | None, action: str) -> Any:
        user_id = int(telegram_id)
        if user_id <= 0:
            raise ValueError("Telegram user ID không hợp lệ.")
        if action not in {"connect", "disconnect"}:
            raise ValueError("Unsupported proxy action")
        payload = {"telegram_user_id": user_id, "username": username, "action": action}
        return await self._request("POST", self.settings.proxy_route_path, payload)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
