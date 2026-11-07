from __future__ import annotations

import unittest

from services.sanitize import redact_sensitive


class RedactionTests(unittest.TestCase):
    def test_redacts_nested_credentials(self) -> None:
        value = {
            "credit": 12,
            "access_token": "abc",
            "profile": {"api-key": "def", "username": "user"},
            "items": [{"password_hash": "ghi"}],
        }
        result = redact_sensitive(value)
        self.assertEqual(result["credit"], 12)
        self.assertEqual(result["access_token"], "[đã ẩn]")
        self.assertEqual(result["profile"]["api-key"], "[đã ẩn]")
        self.assertEqual(result["profile"]["username"], "user")
        self.assertEqual(result["items"][0]["password_hash"], "[đã ẩn]")


if __name__ == "__main__":
    unittest.main()
