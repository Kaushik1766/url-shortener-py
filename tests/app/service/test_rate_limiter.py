import datetime
import unittest
from unittest.mock import MagicMock, patch

from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.service.rate_limiter import RateLimitingService
from app.constants import HASHID_SALT, STD_RATE_LIMIT, PRO_RATE_LIMIT
import hashids


class _FakeRedis:
    def __init__(self):
        self.counts = {}
        self.expire_calls = []

    def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key, ttl):
        self.expire_calls.append((key, ttl))


class TestRateLimitingServiceCheckAccess(unittest.TestCase):
    def test_check_access(self):
        redis_client = _FakeRedis()
        service = RateLimitingService(redis_client)
        encoder = hashids.Hashids(salt=HASHID_SALT, min_length=7)
        valid_code = encoder.encode(123)
        std_short = f"{Subscription.STANDARD.value}{valid_code}"
        pro_short = f"{Subscription.PREMIUM.value}{valid_code}"
        fixed_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)

        cases = [
            {"name": "invalid prefix", "short": "bad123", "prep": lambda key: None, "raises": WebException, "allowed": None},
            {"name": "invalid hash", "short": f"{Subscription.STANDARD.value}invalid", "prep": lambda key: None, "raises": WebException, "allowed": None},
            {"name": "std within limit", "short": std_short, "prep": lambda key: None, "raises": None, "allowed": True},
            {"name": "std over limit", "short": std_short, "prep": lambda key: redis_client.counts.__setitem__(key, STD_RATE_LIMIT), "raises": None, "allowed": False},
            {"name": "pro within limit", "short": pro_short, "prep": lambda key: redis_client.counts.__setitem__(key, PRO_RATE_LIMIT - 1), "raises": None, "allowed": True},
        ]

        for case in cases:
            with patch("app.service.rate_limiter.datetime") as mock_dt:
                mock_dt.datetime.now.return_value = fixed_time
                mock_dt.datetime.strftime = datetime.datetime.strftime
                mock_dt.timezone = datetime.timezone
                mock_dt.timedelta = datetime.timedelta
                window_start = int(fixed_time.timestamp()) - (int(fixed_time.timestamp()) % 60)
                key = f"rl:{case['short']}:{window_start}"
                case["prep"](key)

                with self.subTest(case["name"]):
                    if case["raises"]:
                        with self.assertRaises(WebException) as ctx:
                            service.check_access(case["short"])
                        self.assertEqual(ErrorCodes.SHORTURL_NOT_FOUND, ctx.exception.error_code)
                    else:
                        allowed = service.check_access(case["short"])
                        self.assertEqual(case["allowed"], allowed)


class TestRateLimitingServiceRateLimit(unittest.TestCase):
    def test_rate_limit(self):
        redis_client = _FakeRedis()
        service = RateLimitingService(redis_client)
        event = {"pathParameters": {"short_url": "stdabc"}}

        def dummy(*args, **kwargs):
            return {"ok": True}

        cases = [
            {"name": "missing short url", "event": {"pathParameters": {}}, "check": True, "raises": WebException, "status": ErrorCodes.SHORTURL_NOT_FOUND},
            {"name": "blocked", "event": event, "check": False, "raises": WebException, "status": ErrorCodes.TOO_MANY_REQUESTS},
            {"name": "allowed", "event": event, "check": True, "raises": None, "status": None},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                service.check_access = MagicMock(return_value=case["check"])
                wrapped = service.rate_limit(dummy)
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        wrapped(case["event"], None)
                    self.assertEqual(case["status"], ctx.exception.error_code)
                else:
                    self.assertEqual({"ok": True}, wrapped(case["event"], None))


if __name__ == "__main__":
    unittest.main()
