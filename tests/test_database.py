from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from database import JsonDatabase


class JsonDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_upsert_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "database.json"
            database = JsonDatabase(path)
            await database.initialize()
            user = SimpleNamespace(
                id=987654321,
                username="test_user",
                first_name="Test",
                last_name=None,
                language_code="vi",
            )
            await database.upsert_user(user)
            await database.add_event(user.id, "unit_test")
            stored = await database.get_user(user.id)
            stats = await database.get_stats()
            self.assertEqual(stored["telegram_id"], user.id)
            self.assertEqual(stored["username"], "test_user")
            self.assertEqual(stats, {"users": 1, "events_kept": 1})

    async def test_data_survives_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "database.json"
            first = JsonDatabase(path)
            await first.initialize()
            user = SimpleNamespace(id=12345, username=None, first_name="A", last_name=None, language_code="en")
            await first.upsert_user(user)
            second = JsonDatabase(path)
            await second.initialize()
            self.assertIsNotNone(await second.get_user(12345))

    async def test_list_users_and_recent_events_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = JsonDatabase(Path(directory) / "database.json")
            await database.initialize()
            for user_id in range(1, 5):
                await database.upsert_user(SimpleNamespace(
                    id=user_id, username=f"user{user_id}", first_name="User", last_name=None, language_code="vi"
                ))
                await database.add_event(user_id, "view")
            self.assertEqual(len(await database.list_users(limit=2)), 2)
            self.assertEqual(len(await database.get_recent_events(limit=3)), 3)

    async def test_non_json_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = JsonDatabase(Path(directory) / "database.json")
            await database.initialize()
            with self.assertRaises(TypeError):
                await database.add_event(123, "bad", {"not_json": object()})

    async def test_invalid_existing_root_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "database.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            database = JsonDatabase(path)
            with self.assertRaises(RuntimeError):
                await database.initialize()
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), ["not", "an", "object"])


if __name__ == "__main__":
    unittest.main()
