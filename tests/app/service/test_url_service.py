import unittest
from unittest.mock import MagicMock

import hashids

from app.constants import HASHID_SALT
from app.models.subscriptions import Subscription
from app.service.url_service import ShortURLService


class TestShortURLService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.mock_redis = MagicMock()
        self.service = ShortURLService(self.mock_repo, self.mock_redis)
        self.encoder = hashids.Hashids(salt=HASHID_SALT, min_length=7)

    def tearDown(self):
        pass

    def test_create_short_url(self):
        cases = [
            {
                "name": "standard encoding",
                "subscription": Subscription.STANDARD,
                "counter_start": 10,
                "expect_prefix": str(Subscription.STANDARD.to_number()),
            },
            {
                "name": "premium encoding",
                "subscription": Subscription.PREMIUM,
                "counter_start": 10,
                "expect_prefix": str(Subscription.PREMIUM.to_number()),
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_repo.get_counter.return_value = case["counter_start"] + 1
                self.mock_repo.added = []
                
                short_url = self.service.create_short_url("https://example.com", "user-id", case["subscription"])
                
                decoded = self.encoder.decode(short_url)
                self.assertEqual(1, len(decoded))
                decoded_str = str(decoded[0])
                self.assertTrue(decoded_str.startswith(case["expect_prefix"]))
                self.mock_repo.add_url.assert_called()

    def test_get_original_url(self):
        cases = [
            {
                "name": "cache hit",
                "short_url": "stdabc",
                "cache_value": "hit.com",
                "db_value": "db.com",
                "expect_result": "hit.com",
                "expect_db_called": False,
            },
            {
                "name": "cache miss",
                "short_url": "stdabc",
                "cache_value": None,
                "db_value": "db.com",
                "expect_result": "db.com",
                "expect_db_called": True,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_redis.get.return_value = case["cache_value"]
                self.mock_repo.get_url.return_value = case["db_value"]
                self.mock_redis.set.reset_mock()
                
                result = self.service.get_original_url(case["short_url"])
                
                self.assertEqual(case["expect_result"], result)
                if not case["expect_db_called"]:
                    self.mock_repo.get_url.assert_not_called()
                else:
                    self.mock_repo.get_url.assert_called_once()
                    self.mock_redis.set.assert_called()

    def test_get_urls_by_user(self):
        cases = [
            {
                "name": "returns user urls",
                "user_id": "u1",
                "repo_return": ["a", "b"],
                "expect": ["a", "b"],
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_repo.get_urls_by_user_id.return_value = case["repo_return"]
                
                result = self.service.get_urls_by_user(case["user_id"])
                
                self.assertEqual(case["expect"], result)


if __name__ == "__main__":
    unittest.main()
