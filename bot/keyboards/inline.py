"""Inline keyboards for the main menu, proxy controls and admin tools."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import Settings


def main_menu_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    """Build the 11 requested customer buttons in the order supplied."""
    minigame_button = (
        InlineKeyboardButton(text="🚀 MINIGAME LIVE", url=settings.bot_minigame_url)
        if settings.bot_minigame_url
        else InlineKeyboardButton(text="🚀 MINIGAME LIVE", callback_data="menu:minigame")
    )
    customer_button = (
        InlineKeyboardButton(text="💠 TRUNG TÂM KHÁCH HÀNG", web_app=WebAppInfo(url=settings.mini_app_url))
        if settings.mini_app_url
        else InlineKeyboardButton(text="💠 TRUNG TÂM KHÁCH HÀNG", callback_data="menu:customer")
    )
    group_button = (
        InlineKeyboardButton(text="🗣️ NHÓM CHAT", url=settings.bot_group_chat_url)
        if settings.bot_group_chat_url
        else InlineKeyboardButton(text="🗣️ NHÓM CHAT", callback_data="menu:group")
    )
    support_button = (
        InlineKeyboardButton(text="🧑🏻‍💻 LIÊN HỆ CSKH", url=settings.bot_support_url)
        if settings.bot_support_url
        else InlineKeyboardButton(text="🧑🏻‍💻 LIÊN HỆ CSKH", callback_data="menu:support")
    )

    rows = [
        [minigame_button, InlineKeyboardButton(text="📲 OTP & PROXY", callback_data="menu:proxy")],
        [customer_button],
        [
            InlineKeyboardButton(text="👑 DỊCH VỤ SẮP TRIỂN KHAI", callback_data="menu:upcoming"),
            InlineKeyboardButton(text="👑 KHO CÔNG CỤ TOOLS ĐỘC QUYỀN", callback_data="menu:tools"),
        ],
        [InlineKeyboardButton(text="💳 NẠP TIỀN", callback_data="menu:deposit")],
        [group_button, support_button],
        [
            InlineKeyboardButton(text="🎁 CODE MÀN - CODE TELE", callback_data="menu:codes"),
            InlineKeyboardButton(text="👑 TRUNG TÂM VIP", callback_data="menu:vip"),
        ],
        [InlineKeyboardButton(text="🎟️ NHẬP GIFTCODE", callback_data="menu:giftcode")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def proxy_keyboard(mini_app_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔍 Kiểm tra trạng thái", callback_data="proxy:status")],
        [InlineKeyboardButton(text="💳 Credit của tôi", callback_data="proxy:credit")],
        [
            InlineKeyboardButton(text="🔌 Kết nối", callback_data="proxy:connect"),
            InlineKeyboardButton(text="⏏️ Ngắt kết nối", callback_data="proxy:disconnect"),
        ],
    ]
    if mini_app_url:
        rows.append([InlineKeyboardButton(text="📱 Mở Mini App", web_app=WebAppInfo(url=mini_app_url))])
    rows.append([InlineKeyboardButton(text="↩️ Menu chính", callback_data="menu:home")])
    rows.append([InlineKeyboardButton(text="ℹ️ Trợ giúp", callback_data="app:help")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Thống kê hệ thống", callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Người dùng gần đây", callback_data="admin:users")],
        [InlineKeyboardButton(text="🧾 Hoạt động gần đây", callback_data="admin:events")],
        [InlineKeyboardButton(text="🌐 Kiểm tra HomeProxy", callback_data="admin:proxy_status")],
    ])
