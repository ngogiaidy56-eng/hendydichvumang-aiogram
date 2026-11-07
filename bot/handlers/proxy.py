"""User-facing commands and callbacks for proxy operations."""
from __future__ import annotations

import json
import logging
from html import escape
from pathlib import Path
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards.inline import main_menu_keyboard, proxy_keyboard
from config import Settings
from database import JsonDatabase
from services.proxy_service import ProxyService, ProxyServiceError
from services.sanitize import redact_sensitive

router = Router(name="proxy")

HELP_TEXT = (
    "<b>Hendy Dịch Vụ Mạng — Trợ giúp</b>\n\n"
    "/start — Mở menu chính\n"
    "/proxy — Mở bảng điều khiển proxy\n"
    "/status — Kiểm tra trạng thái HomeProxy Hub\n"
    "/credit — Xem credit gắn với Telegram ID\n"
    "/me — Xem thông tin tài khoản Telegram\n"
    "/id — Hiển thị Telegram ID của bạn\n"
    "/help — Hiển thị hướng dẫn này\n\n"
    "Các thao tác kết nối chỉ hoạt động khi quản trị viên cấu hình API HomeProxy Hub chính xác."
)

HOME_CAPTION = (
    "<b>HENDY BOT — HENDY CYBERTECH</b>\n"
    "Công nghệ kết nối — Giá trị thật!\n\n"
    "Chọn một dịch vụ bên dưới để bắt đầu."
)


def _format_result(value: Any) -> str:
    try:
        rendered = json.dumps(redact_sensitive(value), ensure_ascii=False, indent=2, default=str)
    except (TypeError, ValueError):
        rendered = str(value)
    return f"<pre>{escape(rendered[:2500])}</pre>"


def _resolve_home_photo(photo_setting: str) -> str | FSInputFile:
    """Accept Telegram file_id, HTTPS URL, or an existing local file path."""
    value = photo_setting.strip()
    local_path = Path(value).expanduser()
    if local_path.is_file():
        return FSInputFile(local_path)
    return value


async def _track(database: JsonDatabase, user: Any, action: str) -> None:
    await database.upsert_user(user)
    await database.add_event(user.id, action)


@router.message(CommandStart())
async def start_handler(message: Message, database: JsonDatabase, settings: Settings) -> None:
    if message.from_user:
        await _track(database, message.from_user, "start")
    keyboard = main_menu_keyboard(settings)

    if settings.bot_home_photo:
        try:
            await message.answer_photo(
                photo=_resolve_home_photo(settings.bot_home_photo),
                caption=HOME_CAPTION,
                reply_markup=keyboard,
            )
            return
        except (TelegramAPIError, OSError, ValueError) as exc:
            logging.warning("BOT_HOME_PHOTO could not be sent (%s); falling back to text menu.", type(exc).__name__)

    await message.answer(HOME_CAPTION, reply_markup=keyboard)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=None)


@router.callback_query(F.data == "app:help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(HELP_TEXT)


@router.message(Command("id"))
async def id_handler(message: Message) -> None:
    if message.from_user:
        await message.answer(f"Telegram ID của bạn: <code>{message.from_user.id}</code>")


@router.message(Command("me"))
async def me_handler(message: Message, database: JsonDatabase) -> None:
    if not message.from_user:
        return
    await _track(database, message.from_user, "profile_view")
    profile = await database.get_user(message.from_user.id)
    if not profile:
        await message.answer("Chưa tìm thấy hồ sơ. Hãy gửi /start trước.")
        return
    username = f"@{escape(profile['username'])}" if profile.get("username") else "Chưa đặt"
    await message.answer(
        "<b>Thông tin tài khoản</b>\n"
        f"ID: <code>{profile['telegram_id']}</code>\n"
        f"Tên: {escape(str(profile.get('first_name') or ''))}\n"
        f"Username: {username}\n"
        f"Ngôn ngữ: {escape(str(profile.get('language_code') or 'không rõ'))}"
    )


@router.message(Command("proxy"))
async def proxy_handler(message: Message, database: JsonDatabase, settings: Settings) -> None:
    if message.from_user:
        await _track(database, message.from_user, "proxy_menu")
    await message.answer(
        "<b>Điều khiển OTP & Proxy</b>\nChọn một thao tác:",
        reply_markup=proxy_keyboard(settings.mini_app_url),
    )


@router.message(Command("status"))
async def status_handler(message: Message, database: JsonDatabase, proxy_service: ProxyService) -> None:
    if message.from_user:
        await _track(database, message.from_user, "proxy_status")
    try:
        result = await proxy_service.get_status()
        text = "<b>Trạng thái HomeProxy Hub</b>\n" + _format_result(result)
    except ProxyServiceError as exc:
        text = f"<b>Chưa lấy được trạng thái:</b> {escape(str(exc))}"
    await message.answer(text)


@router.message(Command("credit"))
async def credit_handler(message: Message, database: JsonDatabase, proxy_service: ProxyService) -> None:
    if not message.from_user:
        return
    await _track(database, message.from_user, "proxy_credit")
    try:
        result = await proxy_service.get_credit(message.from_user.id)
        text = "<b>Thông tin Credit</b>\n" + _format_result(result)
    except ProxyServiceError as exc:
        text = f"<b>Chưa lấy được Credit:</b> {escape(str(exc))}"
    await message.answer(text)


@router.callback_query(F.data == "proxy:status")
async def proxy_status_callback(callback: CallbackQuery, database: JsonDatabase, proxy_service: ProxyService) -> None:
    await callback.answer()
    await _track(database, callback.from_user, "proxy_status_button")
    try:
        result = await proxy_service.get_status()
        text = "<b>Trạng thái HomeProxy Hub</b>\n" + _format_result(result)
    except ProxyServiceError as exc:
        text = f"<b>Chưa lấy được trạng thái:</b> {escape(str(exc))}"
    if isinstance(callback.message, Message):
        await callback.message.answer(text)


@router.callback_query(F.data == "proxy:credit")
async def proxy_credit_callback(callback: CallbackQuery, database: JsonDatabase, proxy_service: ProxyService) -> None:
    await callback.answer()
    await _track(database, callback.from_user, "proxy_credit_button")
    try:
        result = await proxy_service.get_credit(callback.from_user.id)
        text = "<b>Thông tin Credit</b>\n" + _format_result(result)
    except ProxyServiceError as exc:
        text = f"<b>Chưa lấy được Credit:</b> {escape(str(exc))}"
    if isinstance(callback.message, Message):
        await callback.message.answer(text)


async def _route_callback(
    callback: CallbackQuery,
    database: JsonDatabase,
    proxy_service: ProxyService,
    action: str,
) -> None:
    await callback.answer("Đang gửi yêu cầu…")
    await _track(database, callback.from_user, f"proxy_{action}")
    try:
        result = await proxy_service.set_route(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            action=action,
        )
        verb = "kết nối" if action == "connect" else "ngắt kết nối"
        text = f"<b>Yêu cầu {verb} đã được gửi.</b>\n" + _format_result(result)
    except ProxyServiceError as exc:
        text = f"<b>Không thực hiện được:</b> {escape(str(exc))}"
    if isinstance(callback.message, Message):
        await callback.message.answer(text)


@router.callback_query(F.data == "proxy:connect")
async def proxy_connect_callback(callback: CallbackQuery, database: JsonDatabase, proxy_service: ProxyService) -> None:
    await _route_callback(callback, database, proxy_service, "connect")


@router.callback_query(F.data == "proxy:disconnect")
async def proxy_disconnect_callback(callback: CallbackQuery, database: JsonDatabase, proxy_service: ProxyService) -> None:
    await _route_callback(callback, database, proxy_service, "disconnect")
