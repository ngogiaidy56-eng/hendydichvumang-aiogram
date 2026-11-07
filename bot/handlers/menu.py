"""Main customer menu callbacks."""
from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from bot.keyboards.inline import main_menu_keyboard, proxy_keyboard
from config import Settings
from database import JsonDatabase

router = Router(name="main-menu")

PENDING_MODULES = {
    "upcoming": (
        "👑 <b>DỊCH VỤ SẮP TRIỂN KHAI</b>\n\n"
        "Các dịch vụ mới đang được chuẩn bị. Bot sẽ mở chức năng khi quản trị viên hoàn tất tích hợp."
    ),
    "tools": (
        "👑 <b>KHO CÔNG CỤ TOOLS ĐỘC QUYỀN</b>\n\n"
        "Kho công cụ đang chờ danh mục sản phẩm và API cấp quyền. Hiện chưa có giao dịch nào được thực hiện."
    ),
    "deposit": (
        "💳 <b>NẠP TIỀN</b>\n\n"
        "Chức năng nạp tiền chưa được kết nối cổng thanh toán. Vui lòng chưa chuyển tiền vào bất kỳ tài khoản nào "
        "cho đến khi thông tin thanh toán chính thức được hiển thị trong bot."
    ),
    "codes": (
        "🎁 <b>CODE MÀN - CODE TELE</b>\n\n"
        "Danh mục code đang chờ cấu hình sản phẩm và nhà cung cấp."
    ),
    "vip": (
        "👑 <b>TRUNG TÂM VIP</b>\n\n"
        "Thông tin cấp VIP, quyền lợi và nâng cấp sẽ hiển thị khi module VIP được tích hợp."
    ),
    "giftcode": (
        "🎟️ <b>NHẬP GIFTCODE</b>\n\n"
        "Hệ thống xác thực giftcode chưa được kết nối. Chưa nhập hoặc gửi mã tại đây để tránh nhầm lẫn."
    ),
}


@router.callback_query(F.data.startswith("menu:"))
async def main_menu_callback(
    callback: CallbackQuery,
    database: JsonDatabase,
    settings: Settings,
) -> None:
    action = (callback.data or "").split(":", maxsplit=1)[-1]
    await callback.answer()
    await database.upsert_user(callback.from_user)
    await database.add_event(callback.from_user.id, f"menu_{action}")

    if action == "home":
        if isinstance(callback.message, Message):
            await callback.message.answer(
                "<b>Hendy Dịch Vụ Mạng</b>\nChọn dịch vụ bạn muốn sử dụng:",
                reply_markup=main_menu_keyboard(settings),
            )
        return

    if action == "proxy":
        if isinstance(callback.message, Message):
            await callback.message.answer(
                "<b>📲 OTP & PROXY</b>\nChọn thao tác quản lý proxy:",
                reply_markup=proxy_keyboard(settings.mini_app_url),
            )
        return

    if action == "customer":
        profile = await database.get_user(callback.from_user.id)
        if profile:
            username = f"@{escape(profile['username'])}" if profile.get("username") else "Chưa đặt"
            text = (
                "<b>💠 TRUNG TÂM KHÁCH HÀNG</b>\n"
                f"Telegram ID: <code>{profile['telegram_id']}</code>\n"
                f"Username: {username}\n"
                f"Tên: {escape(str(profile.get('first_name') or ''))}\n"
                f"Hoạt động gần nhất: {escape(str(profile.get('last_seen_at') or ''))}"
            )
        else:
            text = "Chưa có hồ sơ. Hãy gửi /start để khởi tạo tài khoản."
        keyboard = None
        if settings.mini_app_url:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="📱 Mở trung tâm khách hàng",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]])
        else:
            text += "\n\nTrung tâm Mini App chưa được cấu hình (MINI_APP_URL)."
        if isinstance(callback.message, Message):
            await callback.message.answer(text, reply_markup=keyboard)
        return

    if action == "minigame":
        text = (
            "🚀 <b>MINIGAME LIVE</b>\n\n"
            "Chưa cấu hình BOT_MINIGAME_URL. Quản trị viên cần thêm URL HTTPS của dịch vụ trước khi mở module."
        )
    elif action == "group":
        text = (
            "🗣️ <b>NHÓM CHAT</b>\n\nChưa cấu hình BOT_GROUP_CHAT_URL. "
            "Quản trị viên cần thêm liên kết nhóm HTTPS."
        )
    elif action == "support":
        text = (
            "🧑🏻‍💻 <b>LIÊN HỆ CSKH</b>\n\nChưa cấu hình BOT_SUPPORT_URL. "
            "Quản trị viên cần thêm liên kết hỗ trợ HTTPS."
        )
    else:
        text = PENDING_MODULES.get(action, "Chức năng này chưa được hỗ trợ.")

    if isinstance(callback.message, Message):
        await callback.message.answer(text)
