"""Hendy Dịch Vụ Mạng — one asyncio loop for aiogram polling and HTTP health."""
from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram.types import BotCommand

from bot.loader import create_bot_dispatcher
from config import ConfigurationError, Settings
from database import JsonDatabase
from services.proxy_service import ProxyService

SERVICE_NAME = "hendydichvumang-aiogram"


async def health_handler(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": SERVICE_NAME})


async def ready_handler(request: web.Request) -> web.Response:
    if not request.app.get("ready", False):
        return web.json_response({"status": "not_ready", "service": SERVICE_NAME}, status=503)
    return web.json_response({"status": "ready", "service": SERVICE_NAME})


async def start_health_server(settings: Settings) -> web.AppRunner:
    app = web.Application(client_max_size=16 * 1024)
    app["ready"] = False
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ready", ready_handler)
    runner = web.AppRunner(app, access_log=logging.getLogger("aiohttp.access"))
    await runner.setup()
    site = web.TCPSite(runner, host=settings.host, port=settings.port)
    await site.start()
    app["ready"] = True
    logging.info("Health server listening on %s:%s", settings.host, settings.port)
    return runner


async def _set_commands(bot) -> None:
    commands = [
        BotCommand(command="start", description="Bắt đầu sử dụng bot"),
        BotCommand(command="help", description="Xem hướng dẫn sử dụng"),
        BotCommand(command="proxy", description="Mở bảng điều khiển proxy"),
        BotCommand(command="status", description="Kiểm tra trạng thái proxy"),
        BotCommand(command="credit", description="Kiểm tra credit của bạn"),
        BotCommand(command="me", description="Xem thông tin tài khoản"),
        BotCommand(command="id", description="Hiển thị Telegram ID"),
        BotCommand(command="admin", description="Bảng quản trị (admin)"),
        BotCommand(command="photoid", description="Lấy file_id ảnh trang chủ (admin)"),
        BotCommand(command="users", description="Danh sách người dùng (admin)"),
        BotCommand(command="user", description="Tra cứu Telegram ID (admin)"),
        BotCommand(command="events", description="Lịch sử hoạt động (admin)"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    try:
        settings = Settings.from_env()
    except ConfigurationError:
        logging.basicConfig(level=logging.ERROR)
        logging.exception("Cấu hình không hợp lệ")
        raise

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not settings.admin_ids:
        logging.warning("ADMIN_IDS đang trống: không có tài khoản nào được phép dùng /admin.")
    if not settings.proxy_api_configured:
        logging.warning("HomeProxy Hub chưa cấu hình; các lệnh API sẽ báo chưa sẵn sàng.")

    database = JsonDatabase(settings.database_path)
    await database.initialize()
    proxy_service = ProxyService(settings)
    bot, dispatcher = create_bot_dispatcher(settings)
    dispatcher["database"] = database
    dispatcher["settings"] = settings
    dispatcher["proxy_service"] = proxy_service

    runner: web.AppRunner | None = None
    try:
        me = await bot.get_me()  # Validate BOT_TOKEN before marking service ready.
        await _set_commands(bot)
        runner = await start_health_server(settings)
        logging.info("Telegram bot @%s started with long polling", me.username or "unknown")
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
            close_bot_session=False,
            handle_signals=True,
        )
    finally:
        if runner is not None:
            await runner.cleanup()
        await proxy_service.close()
        await bot.session.close()
        logging.info("Application shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
