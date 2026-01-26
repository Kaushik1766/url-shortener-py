import unittest

import hashids

from app.constants import HASHID_SALT
from app.models.subscriptions import Subscription
from app.repository.short_url_repo import ShortURLRepository
from app.service.url_service import ShortURLService


class _FakeRepo(ShortURLRepository):
    def __init__(self, counter_start: int = 0):
        self.counter_start = counter_start
        self.added = []
        self.url_lookup = {}
        self.urls_by_user = {}

    def get_counter(self):
        self.counter_start += 1
        return self.counter_start

    def add_url(self, short_url):
        self.added.append(short_url)

    def get_url(self, shortened_url: str) -> str:
        return self.url_lookup.get(shortened_url)

    def get_urls_by_user_id(self, user_id: str) -> list[str]:
        return self.urls_by_user.get(user_id, [])


class _FakeRedis:
    def __init__(self):
        self.store = {}
        self.set_calls = []

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value
        self.set_calls.append({"key": key, "value": value, "ex": ex})


class TestShortURLServiceCreateShortUrl(unittest.TestCase):
    def test_create_short_url(self):
        encoder = hashids.Hashids(salt=HASHID_SALT, min_length=7)
        cases = [
            {"name": "standard encoding", "subscription": Subscription.STANDARD},
            {"name": "premium encoding", "subscription": Subscription.PREMIUM},
        ]
        for case in cases:
            repo = _FakeRepo(counter_start=10)
            service = ShortURLService(repo, _FakeRedis())
            with self.subTest(case["name"]):
                short_url = service.create_short_url("https://example.com", "user-id", case["subscription"])
                decoded = encoder.decode(short_url)
                self.assertEqual(1, len(decoded))
                decoded_str = str(decoded[0])
                prefix = str(case["subscription"].to_number())
                self.assertTrue(decoded_str.startswith(prefix))
                self.assertEqual(str(repo.counter_start), decoded_str[len(prefix):])
                self.assertEqual(1, len(repo.added))
                saved = repo.added[0]
                self.assertEqual(short_url, saved.short_url)
                self.assertEqual("user-id", saved.owner_id)


class TestShortURLServiceGetOriginalUrl(unittest.TestCase):
    def test_get_original_url(self):
        repo = _FakeRepo()
        redis_client = _FakeRedis()
        repo.url_lookup["stdabc"] = "cached.com"
        service = ShortURLService(repo, redis_client)

        cases = [
            {"name": "cache hit", "cache_value": "hit.com", "db_value": "db.com"},
            {"name": "cache miss", "cache_value": None, "db_value": "db.com"},
        ]

        for case in cases:
            redis_client.store = {"shorturl:stdabc": case["cache_value"]} if case["cache_value"] else {}
            repo.url_lookup["stdabc"] = case["db_value"]
            with self.subTest(case["name"]):
                result = service.get_original_url("stdabc")
                expected = case["cache_value"] or case["db_value"]
                self.assertEqual(str(expected), result)
                if case["cache_value"] is None:
                    self.assertEqual(1, len(redis_client.set_calls))
                    self.assertEqual("shorturl:stdabc", redis_client.set_calls[-1]["key"])


class TestShortURLServiceGetUrlsByUser(unittest.TestCase):
    def test_get_urls_by_user(self):
        repo = _FakeRepo()
        repo.urls_by_user["u1"] = ["a", "b"]
        service = ShortURLService(repo, _FakeRedis())

        self.assertEqual(["a", "b"], service.get_urls_by_user("u1"))


if __name__ == "__main__":
    unittest.main()
