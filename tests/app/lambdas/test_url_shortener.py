import json
import os
import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.errors.web_errors import ErrorCodes
from app.lambdas import url_shortener


class TestUrlShortenerLambda(unittest.TestCase):
    def setUp(self):
        self.mock_url_service = MagicMock()
        self.mock_sqs = MagicMock()
        self.url_patcher = patch.object(url_shortener, "url_service", self.mock_url_service)
        self.url_patcher.start()
        self.jwt_payload = JwtDTO(id="u1", email="e@example.com", name="Name", iat=1, exp=2, subscription="std").model_dump()

    def tearDown(self):
        self.url_patcher.stop()

    def test_create_shorturl_handler(self):
        cases = [
            {
                "name": "successful creation",
                "event": {
                    "headers": {"Authorization": "Bearer token"},
                    "body": json.dumps({"url": "example.com"}),
                },
                "service_return": "stdabc",
                "expect_status": 201,
                "expect_short_url": "stdabc",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_url_service.create_short_url.return_value = case["service_return"]
                
                with patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                    response = url_shortener.create_shorturl_handler(case["event"], None)
                
                self.assertEqual(case["expect_status"], response["statusCode"])
                body = json.loads(response["body"])
                self.assertEqual(case["expect_short_url"], body["shortUrl"])

    def test_get_url_handler(self):
        cases = [
            {
                "name": "allowed no scheme",
                "short_url": "stdcode",
                "original": "example.com",
                "check_return": True,
                "expect_status": 302,
                "expect_location": "https://example.com",
            },
            {
                "name": "blocked by rate limit",
                "short_url": "stdcode",
                "original": "http://withscheme",
                "check_return": False,
                "expect_status": 429,
                "expect_error_code": ErrorCodes.TOO_MANY_REQUESTS,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                event = {
                    "pathParameters": {"short_url": case["short_url"]},
                    "headers": {},
                    "requestContext": {"identity": {"sourceIp": "1.1.1.1"}},
                }
                
                url_shortener.rate_limiter.check_access = MagicMock(return_value=case["check_return"])
                url_shortener.metrics_service.sqs_client = self.mock_sqs
                self.mock_url_service.get_original_url.return_value = case["original"]
                
                with patch.dict(os.environ, {"QUEUE_URL": "queue"}):
                    response = url_shortener.get_url_handler(event, None)
                
                self.assertEqual(case["expect_status"], response["statusCode"])
                if "expect_location" in case:
                    self.assertEqual(case["expect_location"], response["headers"]["Location"])
                if "expect_error_code" in case:
                    body = json.loads(response["body"])
                    self.assertEqual(case["expect_error_code"], body["code"])

    def test_get_user_short_urls(self):
        cases = [
            {
                "name": "returns user urls",
                "event": {"headers": {"Authorization": "Bearer token"}},
                "service_return": ["a", "b"],
                "expect_status": 200,
                "expect_urls": ["a", "b"],
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_url_service.get_urls_by_user.return_value = case["service_return"]
                
                with patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                    response = url_shortener.get_user_short_urls(case["event"], None)
                
                self.assertEqual(case["expect_status"], response["statusCode"])
                body = json.loads(response["body"])
                self.assertEqual(case["expect_urls"], body)


if __name__ == "__main__":
    unittest.main()
