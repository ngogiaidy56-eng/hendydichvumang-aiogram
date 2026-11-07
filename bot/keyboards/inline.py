"""Inline keyboards for proxy controls, Mini App entry and admin tools."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


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
    rows.append([InlineKeyboardButton(text="ℹ️ Trợ giúp", callback_data="app:help")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Thống kê hệ thống", callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Người dùng gần đây", callback_data="admin:users")],
        [InlineKeyboardButton(text="🧾 Hoạt động gần đây", callback_data="admin:events")],
        [InlineKeyboardButton(text="🌐 Kiểm tra HomeProxy", callback_data="admin:proxy_status")],
    ])
