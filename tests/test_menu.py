from __future__ import annotations

import unittest

from bot.keyboards.inline import main_menu_keyboard
from config import Settings


class MainMenuTests(unittest.TestCase):
    def make_settings(self, **overrides) -> Settings:
        values = dict(
            bot_token="123:test",
            admin_ids=frozenset(),
            mini_app_url="",
            database_path="database.json",
            proxy_api_url="",
            proxy_api_token="",
            proxy_auth_scheme="Bearer",
            proxy_status_path="",
            proxy_credit_path="",
            proxy_route_path="",
            proxy_timeout_seconds=15.0,
            host="0.0.0.0",
            port=10000,
            log_level="INFO",
        )
        values.update(overrides)
        return Settings(**values)

    def test_menu_contains_all_eleven_buttons_in_requested_order(self) -> None:
        keyboard = main_menu_keyboard(self.make_settings())
        labels = [button.text for row in keyboard.inline_keyboard for button in row]
        self.assertEqual(labels, [
            "🚀 MINIGAME LIVE",
            "📲 OTP & PROXY",
            "💠 TRUNG TÂM KHÁCH HÀNG",
            "👑 DỊCH VỤ SẮP TRIỂN KHAI",
            "👑 KHO CÔNG CỤ TOOLS ĐỘC QUYỀN",
            "💳 NẠP TIỀN",
            "🗣️ NHÓM CHAT",
            "🧑🏻‍💻 LIÊN HỆ CSKH",
            "🎁 CODE MÀN - CODE TELE",
            "👑 TRUNG TÂM VIP",
            "🎟️ NHẬP GIFTCODE",
        ])

    def test_optional_links_become_url_buttons(self) -> None:
        settings = self.make_settings(
            bot_minigame_url="https://example.com/game",
            bot_group_chat_url="https://t.me/example_group",
            bot_support_url="https://t.me/example_support",
        )
        keyboard = main_menu_keyboard(settings)
        buttons = [button for row in keyboard.inline_keyboard for button in row]
        by_label = {button.text: button for button in buttons}
        self.assertEqual(by_label["🚀 MINIGAME LIVE"].url, "https://example.com/game")
        self.assertEqual(by_label["🗣️ NHÓM CHAT"].url, "https://t.me/example_group")
        self.assertEqual(by_label["🧑🏻‍💻 LIÊN HỆ CSKH"].url, "https://t.me/example_support")

    def test_proxy_button_routes_to_proxy_menu(self) -> None:
        keyboard = main_menu_keyboard(self.make_settings())
        buttons = [button for row in keyboard.inline_keyboard for button in row]
        proxy = next(button for button in buttons if button.text == "📲 OTP & PROXY")
        self.assertEqual(proxy.callback_data, "menu:proxy")


if __name__ == "__main__":
    unittest.main()
