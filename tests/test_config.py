from __future__ import annotations

import unittest

from config import ConfigurationError, _parse_admin_ids, _validate_base_url


class ConfigValidationTests(unittest.TestCase):
    def test_parse_admin_ids(self) -> None:
        self.assertEqual(_parse_admin_ids("12, 34;56"), frozenset({12, 34, 56}))

    def test_reject_non_numeric_admin_id(self) -> None:
        with self.assertRaises(ConfigurationError):
            _parse_admin_ids("12,root")

    def test_reject_external_http_api_url(self) -> None:
        with self.assertRaises(ConfigurationError):
            _validate_base_url("http://proxy.example.com")

    def test_allow_local_http_api_url(self) -> None:
        self.assertEqual(_validate_base_url("http://localhost:8080/"), "http://localhost:8080")

    def test_reject_credentials_in_api_url(self) -> None:
        with self.assertRaises(ConfigurationError):
            _validate_base_url("https://user:pass@proxy.example.com")


if __name__ == "__main__":
    unittest.main()
