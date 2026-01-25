import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.errors.web_errors import ErrorCodes
from app.lambdas import url_shortener


class _FakeSQS:
    def __init__(self):
        self.calls = []

    def send_message(self, **kwargs):
        self.calls.append(kwargs)
        return {"MessageId": "1"}


class TestCreateShorturlHandler(unittest.TestCase):
    def test_create_shorturl_handler(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({"url": "example.com"}),
        }
        payload = JwtDTO(id="u1", email="e@example.com", name="Name", iat=1, exp=2, subscription="std").model_dump()

        mock_service = MagicMock()
        mock_service.create_short_url.return_value = "stdabc"

        with patch.object(url_shortener, "url_service", mock_service), \
             patch("app.utils.auth_decorator.jwt.decode", return_value=payload):
            response = url_shortener.create_shorturl_handler(event, None)

        self.assertEqual(201, response["statusCode"])
        body = json.loads(response["body"])
        self.assertEqual("stdabc", body["shortUrl"])


class TestGetUrlHandler(unittest.TestCase):
    def test_get_url_handler(self):
        event_base = {
            "pathParameters": {"short_url": "stdcode"},
            "headers": {},
            "requestContext": {"identity": {"sourceIp": "1.1.1.1"}},
        }

        payloads = [
            {"name": "allowed no scheme", "short_url": "stdcode", "original": "example.com", "check": True, "expect_status": 302, "expect_location": "https://example.com"},
            {"name": "blocked by rate limit", "short_url": "stdcode", "original": "http://withscheme", "check": False, "expect_status": 429, "expect_location": None},
        ]

        for case in payloads:
            event = {**event_base, "pathParameters": {"short_url": case["short_url"]}}
            fake_sqs = _FakeSQS()
            with patch.dict(os.environ, {"QUEUE_URL": "queue"}):
                url_shortener.rate_limiter.check_access = MagicMock(return_value=case["check"])
                url_shortener.metrics_service.sqs_client = fake_sqs
                with patch.object(url_shortener, "url_service") as us:
                    us.get_original_url.return_value = case["original"]

                    response = url_shortener.get_url_handler(event, None)

            if case["expect_location"]:
                self.assertEqual(case["expect_status"], response["statusCode"])
                self.assertEqual(case["expect_location"], response["headers"]["Location"])
            else:
                self.assertEqual(case["expect_status"], response["statusCode"])
                body = json.loads(response["body"])
                self.assertEqual(ErrorCodes.TOO_MANY_REQUESTS, body["code"])


class TestGetUserShortUrls(unittest.TestCase):
    def test_get_user_short_urls(self):
        event = {"headers": {"Authorization": "Bearer token"}}
        payload = JwtDTO(id="u1", email="e@example.com", name="Name", iat=1, exp=2, subscription="std").model_dump()
        mock_service = MagicMock()
        mock_service.get_urls_by_user.return_value = ["a", "b"]

        with patch.object(url_shortener, "url_service", mock_service), \
             patch("app.utils.auth_decorator.jwt.decode", return_value=payload):
            response = url_shortener.get_user_short_urls(event, None)

        self.assertEqual(200, response["statusCode"])
        body = json.loads(response["body"])
        self.assertEqual(["a", "b"], body)


if __name__ == "__main__":
    unittest.main()
