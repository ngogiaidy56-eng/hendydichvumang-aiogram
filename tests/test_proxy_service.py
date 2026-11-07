from __future__ import annotations

import unittest
from dataclasses import replace

from aiohttp import web
from aiohttp.test_utils import unused_port

from config import Settings
from services.proxy_service import ProxyService, ProxyServiceError


class ProxyServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.received: dict[str, object] = {}

        async def credit(request: web.Request) -> web.Response:
            self.received["credit_user_id"] = request.query.get("telegram_user_id")
            self.received["auth"] = request.headers.get("Authorization")
            return web.json_response({"credit": 42})

        async def route(request: web.Request) -> web.Response:
            self.received["route_payload"] = await request.json()
            return web.json_response({"accepted": True})

        async def status(request: web.Request) -> web.Response:
            return web.Response(text="upstream diagnostic with potential secret")

        async def too_large(request: web.Request) -> web.Response:
            return web.Response(text="x" * (ProxyService.MAX_RESPONSE_BYTES + 1))

        async def unavailable(request: web.Request) -> web.Response:
            return web.Response(status=503, text="private upstream stack trace")

        app = web.Application()
        app.router.add_get("/credit", credit)
        app.router.add_post("/route", route)
        app.router.add_get("/status", status)
        app.router.add_get("/large", too_large)
        app.router.add_get("/unavailable", unavailable)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.port = unused_port()
        site = web.TCPSite(self.runner, "127.0.0.1", self.port)
        await site.start()

        self.settings = Settings(
            bot_token="test-token",
            admin_ids=frozenset({123}),
            mini_app_url="",
            database_path="database.json",
            proxy_api_url=f"http://127.0.0.1:{self.port}",
            proxy_api_token="test-api-token",
            proxy_auth_scheme="Bearer",
            proxy_status_path="/status",
            proxy_credit_path="/credit",
            proxy_route_path="/route",
            proxy_timeout_seconds=3,
            host="127.0.0.1",
            port=10000,
            log_level="INFO",
        )
        self.service = ProxyService(self.settings)

    async def asyncTearDown(self) -> None:
        await self.service.close()
        await self.runner.cleanup()

    async def test_credit_is_scoped_to_telegram_user(self) -> None:
        response = await self.service.get_credit(778899)
        self.assertEqual(response, {"credit": 42})
        self.assertEqual(self.received["credit_user_id"], "778899")
        self.assertEqual(self.received["auth"], "Bearer test-api-token")

    async def test_route_payload_contains_telegram_identity(self) -> None:
        response = await self.service.set_route(778899, "sample_user", "connect")
        self.assertEqual(response, {"accepted": True})
        self.assertEqual(
            self.received["route_payload"],
            {"telegram_user_id": 778899, "username": "sample_user", "action": "connect"},
        )

    async def test_rejects_absolute_and_traversal_api_paths(self) -> None:
        for path in ("https://attacker.example/steal", "//attacker.example", "/a/../secret", "/status?x=y"):
            with self.subTest(path=path), self.assertRaises(ProxyServiceError):
                self.service._build_url(path)

    async def test_non_json_body_is_not_echoed_to_telegram(self) -> None:
        response = await self.service.get_status()
        self.assertEqual(response["message"], "API đã phản hồi dữ liệu không phải JSON; nội dung đã được ẩn.")
        self.assertNotIn("potential secret", str(response))

    async def test_oversized_response_is_rejected(self) -> None:
        service = ProxyService(replace(self.settings, proxy_status_path="/large"))
        try:
            with self.assertRaises(ProxyServiceError) as captured:
                await service.get_status()
            self.assertIn("64 KB", str(captured.exception))
        finally:
            await service.close()

    async def test_upstream_error_body_is_not_exposed(self) -> None:
        service = ProxyService(replace(self.settings, proxy_status_path="/unavailable"))
        try:
            with self.assertRaises(ProxyServiceError) as captured:
                await service.get_status()
            self.assertNotIn("private upstream", str(captured.exception))
            self.assertIn("503", str(captured.exception))
        finally:
            await service.close()


if __name__ == "__main__":
    unittest.main()
