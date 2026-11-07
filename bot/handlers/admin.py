"""Admin-only system controls and read-only operational views."""
from __future__ import annotations

import json
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import admin_keyboard
from config import Settings
from database import JsonDatabase
from services.proxy_service import ProxyService, ProxyServiceError
from services.sanitize import redact_sensitive

router = Router(name="admin")


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


def _require_admin(message: Message, settings: Settings) -> bool:
    return bool(message.from_user and _is_admin(message.from_user.id, settings))


def _render_users(users: list[dict]) -> str:
    if not users:
        return "Chưa có người dùng được ghi nhận."
    lines = ["<b>Người dùng gần đây</b>"]
    for user in users:
        username = f"@{escape(user['username'])}" if user.get("username") else "không username"
        lines.append(f"• <code>{user.get('telegram_id')}</code> — {username} — {escape(str(user.get('first_name') or ''))}")
    return "\n".join(lines)


@router.message(Command("admin"))
async def admin_panel(message: Message, database: JsonDatabase, settings: Settings, proxy_service: ProxyService) -> None:
    if not _require_admin(message, settings):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị.")
        return
    await database.upsert_user(message.from_user)
    await database.add_event(message.from_user.id, "admin_panel")
    stats = await database.get_stats()
    api_state = "Đã khai báo URL + token" if proxy_service.is_configured else "Chưa cấu hình"
    await message.answer(
        "<b>Hendy Admin</b>\n"
        f"Người dùng đã ghi nhận: <b>{stats['users']}</b>\n"
        f"Sự kiện lưu gần đây: <b>{stats['events_kept']}</b>\n"
        f"HomeProxy API: <b>{api_state}</b>",
        reply_markup=admin_keyboard(),
    )


@router.message(Command("photoid"))
async def photo_id_command(message: Message, settings: Settings) -> None:
    """Return a photo file_id so an admin can set BOT_HOME_PHOTO on Render."""
    if not _require_admin(message, settings):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị.")
        return
    replied = message.reply_to_message
    if not replied or not replied.photo:
        await message.answer("Hãy trả lời (Reply) vào một ảnh đã gửi cho bot bằng lệnh /photoid.")
        return
    file_id = replied.photo[-1].file_id
    await message.answer(
        "Đặt giá trị này trong Render Environment:\n"
        f"<code>BOT_HOME_PHOTO={escape(file_id)}</code>"
    )


@router.message(Command("users"))
async def users_command(message: Message, database: JsonDatabase, settings: Settings) -> None:
    if not _require_admin(message, settings):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị.")
        return
    users = await database.list_users(limit=20)
    await message.answer(_render_users(users))


@router.message(Command("user"))
async def user_command(message: Message, command: CommandObject, database: JsonDatabase, settings: Settings) -> None:
    if not _require_admin(message, settings):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị.")
        return
    raw_id = (command.args or "").strip()
    if not raw_id.isdigit() or int(raw_id) <= 0:
        await message.answer("Cách dùng: <code>/user TELEGRAM_ID</code>")
        return
    user = await database.get_user(int(raw_id))
    if not user:
        await message.answer("Không tìm thấy người dùng trong database.json.")
        return
    safe_username = f"@{escape(user['username'])}" if user.get("username") else "Chưa đặt"
    await message.answer(
        "<b>Hồ sơ người dùng</b>\n"
        f"ID: <code>{user['telegram_id']}</code>\n"
        f"Username: {safe_username}\n"
        f"Tên: {escape(str(user.get('first_name') or ''))}\n"
        f"Đăng ký: {escape(str(user.get('first_seen_at') or ''))}\n"
        f"Hoạt động cuối: {escape(str(user.get('last_seen_at') or ''))}"
    )


@router.message(Command("events"))
async def events_command(message: Message, database: JsonDatabase, settings: Settings) -> None:
    if not _require_admin(message, settings):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị.")
        return
    events = await database.get_recent_events(limit=15)
    if not events:
        await message.answer("Chưa có hoạt động nào được ghi nhận.")
        return
    lines = ["<b>Hoạt động gần đây</b>"]
    for event in events:
        lines.append(
            f"• <code>{event.get('telegram_id')}</code> — "
            f"{escape(str(event.get('event_type', 'unknown')))} — "
            f"{escape(str(event.get('created_at', '')))}"
        )
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(
    callback: CallbackQuery,
    database: JsonDatabase,
    settings: Settings,
    proxy_service: ProxyService,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Không có quyền quản trị.", show_alert=True)
        return
    await callback.answer()

    action = (callback.data or "").split(":", maxsplit=1)[-1]
    if action == "stats":
        stats = await database.get_stats()
        text = (
            "<b>Thống kê hệ thống</b>\n"
            f"Người dùng: <b>{stats['users']}</b>\n"
            f"Sự kiện đang lưu: <b>{stats['events_kept']}</b>"
        )
    elif action == "users":
        text = _render_users(await database.list_users(limit=15))
    elif action == "events":
        events = await database.get_recent_events(limit=15)
        text = "<b>Hoạt động gần đây</b>\n" + "\n".join(
            f"• <code>{item.get('telegram_id')}</code> — "
            f"{escape(str(item.get('event_type', 'unknown')))}"
            for item in events
        ) if events else "Chưa có hoạt động nào."
    elif action == "proxy_status":
        try:
            result = await proxy_service.get_status()
            text = "<b>HomeProxy Hub</b>\n<pre>" + escape(
                json.dumps(redact_sensitive(result), ensure_ascii=False, indent=2, default=str)[:2500]
            ) + "</pre>"
        except ProxyServiceError as exc:
            text = f"<b>HomeProxy Hub:</b> {escape(str(exc))}"
    else:
        text = "Lệnh quản trị không được hỗ trợ."

    if isinstance(callback.message, Message):
        await callback.message.answer(text)
