"""Application settings loaded from environment variables and optional .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _parse_admin_ids(raw: str) -> frozenset[int]:
    values: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        value = part.strip()
        if not value:
            continue
        try:
            user_id = int(value)
        except ValueError as exc:
            raise ConfigurationError("ADMIN_IDS chỉ nhận Telegram user ID dạng số, phân tách bằng dấu phẩy.") from exc
        if user_id <= 0:
            raise ConfigurationError("ADMIN_IDS phải chứa ID số nguyên dương.")
        values.add(user_id)
    return frozenset(values)


def _validate_base_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    if not value:
        return ""
    parsed = urlparse(value)
    is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme not in ({"https", "http"} if is_local else {"https"}) or not parsed.netloc:
        raise ConfigurationError("HOME_PROXY_HUB_API_URL phải là URL HTTPS hợp lệ (HTTP chỉ được phép cho localhost).")
    if parsed.username or parsed.password:
        raise ConfigurationError("Không đặt thông tin đăng nhập trong URL API; hãy dùng HOME_PROXY_HUB_API_TOKEN.")
    if parsed.query or parsed.fragment:
        raise ConfigurationError("HOME_PROXY_HUB_API_URL không được chứa query hoặc fragment.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    mini_app_url: str
    database_path: str
    proxy_api_url: str
    proxy_api_token: str
    proxy_auth_scheme: str
    proxy_status_path: str
    proxy_credit_path: str
    proxy_route_path: str
    proxy_timeout_seconds: float
    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise ConfigurationError("Thiếu BOT_TOKEN. Hãy khai báo BOT_TOKEN trong Environment Variables.")

        mini_app_url = os.getenv("MINI_APP_URL", "").strip()
        if mini_app_url:
            parsed = urlparse(mini_app_url)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                raise ConfigurationError("MINI_APP_URL phải là URL HTTPS công khai của Telegram Mini App.")

        try:
            timeout = float(os.getenv("HOME_PROXY_TIMEOUT_SECONDS", "15"))
            port = int(os.getenv("PORT", "10000"))
        except ValueError as exc:
            raise ConfigurationError("HOME_PROXY_TIMEOUT_SECONDS và PORT phải là số hợp lệ.") from exc
        if timeout <= 0 or timeout > 120:
            raise ConfigurationError("HOME_PROXY_TIMEOUT_SECONDS phải nằm trong khoảng lớn hơn 0 và không quá 120.")
        if not 1 <= port <= 65535:
            raise ConfigurationError("PORT phải nằm trong khoảng 1–65535.")

        auth_scheme = os.getenv("HOME_PROXY_AUTH_SCHEME", "Bearer").strip()
        if any(ch.isspace() for ch in auth_scheme):
            raise ConfigurationError("HOME_PROXY_AUTH_SCHEME không được chứa khoảng trắng.")

        return cls(
            bot_token=token,
            admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
            mini_app_url=mini_app_url,
            database_path=os.getenv("DATABASE_PATH", "database.json").strip() or "database.json",
            proxy_api_url=_validate_base_url(os.getenv("HOME_PROXY_HUB_API_URL", "")),
            proxy_api_token=os.getenv("HOME_PROXY_HUB_API_TOKEN", "").strip(),
            proxy_auth_scheme=auth_scheme,
            proxy_status_path=os.getenv("HOME_PROXY_STATUS_PATH", "").strip(),
            proxy_credit_path=os.getenv("HOME_PROXY_CREDIT_PATH", "").strip(),
            proxy_route_path=os.getenv("HOME_PROXY_ROUTE_PATH", "").strip(),
            proxy_timeout_seconds=timeout,
            host=os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0",
            port=port,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper().strip(),
        )

    @property
    def proxy_api_configured(self) -> bool:
        return bool(self.proxy_api_url and self.proxy_api_token)
