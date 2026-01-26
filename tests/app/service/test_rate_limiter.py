import datetime
import unittest
from unittest.mock import MagicMock, patch

import hashids

from app.constants import HASHID_SALT, PRO_RATE_LIMIT, STD_RATE_LIMIT
from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.service.rate_limiter import RateLimitingService


class TestRateLimitingService(unittest.TestCase):
    def setUp(self):
        self.mock_redis = MagicMock()
        self.service = RateLimitingService(self.mock_redis)
        self.encoder = hashids.Hashids(salt=HASHID_SALT, min_length=7)
        self.std_short = self.encoder.encode(int(f"{Subscription.STANDARD.to_number()}123"))
        self.pro_short = self.encoder.encode(int(f"{Subscription.PREMIUM.to_number()}123"))
        self.fixed_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)

    def tearDown(self):
        pass

    def test_check_access(self):
        cases = [
            {
                "name": "invalid hash",
                "short": "bad123",
                "prep_counts": {},
                "raises": WebException,
                "error_code": ErrorCodes.SHORTURL_NOT_FOUND,
            },
            {
                "name": "std within limit",
                "short": self.std_short,
                "prep_counts": {},
                "raises": None,
                "expect_allowed": True,
            },
            {
                "name": "std over limit",
                "short": self.std_short,
                "prep_counts": lambda key: {key: STD_RATE_LIMIT + 1},
                "raises": None,
                "expect_allowed": False,
            },
            {
                "name": "pro within limit",
                "short": self.pro_short,
                "prep_counts": lambda key: {key: PRO_RATE_LIMIT - 1},
                "raises": None,
                "expect_allowed": True,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                with patch("app.service.rate_limiter.datetime") as mock_dt:
                    mock_dt.datetime.now.return_value = self.fixed_time
                    mock_dt.datetime.strftime = datetime.datetime.strftime
                    mock_dt.timezone = datetime.timezone
                    mock_dt.timedelta = datetime.timedelta
                    
                    window_start = int(self.fixed_time.timestamp()) - (int(self.fixed_time.timestamp()) % 60)
                    key = f"rl:{case['short']}:{window_start}"
                    
                    if callable(case["prep_counts"]):
                        counts = case["prep_counts"](key)
                    else:
                        counts = case["prep_counts"]
                    
                    self.mock_redis.incr.return_value = counts.get(key, 1)
                    
                    if case["raises"]:
                        with self.assertRaises(WebException) as ctx:
                            self.service.check_access(case["short"])
                        self.assertEqual(case["error_code"], ctx.exception.error_code)
                    else:
                        allowed = self.service.check_access(case["short"])
                        self.assertEqual(case["expect_allowed"], allowed)

    def test_rate_limit(self):
        event = {"pathParameters": {"short_url": "stdabc"}}

        def dummy(*args, **kwargs):
            return {"ok": True}

        cases = [
            {
                "name": "missing path",
                "event": {"pathParameters": None},
                "check_return": True,
                "raises": WebException,
                "error_code": ErrorCodes.SHORTURL_NOT_FOUND,
            },
            {
                "name": "missing short url",
                "event": {"pathParameters": {}},
                "check_return": True,
                "raises": WebException,
                "error_code": ErrorCodes.SHORTURL_NOT_FOUND,
            },
            {
                "name": "blocked",
                "event": event,
                "check_return": False,
                "raises": WebException,
                "error_code": ErrorCodes.TOO_MANY_REQUESTS,
            },
            {
                "name": "allowed",
                "event": event,
                "check_return": True,
                "raises": None,
                "expect_result": {"ok": True},
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.service.check_access = MagicMock(return_value=case["check_return"])
                wrapped = self.service.rate_limit(dummy)
                
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        wrapped(case["event"], None)
                    self.assertEqual(case["error_code"], ctx.exception.error_code)
                else:
                    result = wrapped(case["event"], None)
                    self.assertEqual(case["expect_result"], result)


if __name__ == "__main__":
    unittest.main()
