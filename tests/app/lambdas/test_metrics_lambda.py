import json
import unittest
from unittest.mock import MagicMock, patch

from app.lambdas import metrics as metrics_lambda
from app.models.metrics import DailyAccessMetrics


class TestMetricsLambda(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.patcher = patch.object(metrics_lambda, "metrics_service", self.mock_service)
        self.patcher.start()
        self.jwt_payload = {
            "id": "user-1",
            "email": "u@example.com",
            "name": "User",
            "iat": 1,
            "exp": 2,
            "subscription": "std",
        }

    def tearDown(self):
        self.patcher.stop()

    def test_process_metrics(self):
        cases = [
            {
                "name": "success with failures",
                "process_return": ["a", "b"],
                "side_effect": None,
                "expect_result": {"batchItemFailures": [{"itemIdentifier": "a"}, {"itemIdentifier": "b"}]},
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_service.process_event.return_value = case["process_return"]
                self.mock_service.process_event.side_effect = case["side_effect"]
                
                result = metrics_lambda.process_metrics({"Records": []}, None)
                
                self.assertEqual(case["expect_result"], result)
                self.mock_service.process_event.assert_called()

    def test_get_url_metrics(self):
        metric = DailyAccessMetrics(
            ShortURL="abc",
            Day="2023-01-01",
            TotalHits=1,
            ByCountry={"IN": 1},
            ByDeviceType={"desktop": 1},
            ByReferrer={"ref": 1},
        )
        
        cases = [
            {
                "name": "success with metrics",
                "event": {
                    "headers": {"Authorization": "Bearer good"},
                    "pathParameters": {"short_url": "abc"},
                    "queryStringParameters": {"startDate": "2023-01-01", "endDate": "2023-01-02"},
                },
                "metrics": [metric],
                "expect_status": 200,
                "expect_short_url": "abc",
            },
            {
                "name": "missing path parameters",
                "event": {"headers": {"Authorization": "Bearer good"}, "pathParameters": None},
                "metrics": [],
                "expect_status": 404,
                "expect_error_code": metrics_lambda.ErrorCodes.SHORTURL_NOT_FOUND,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_service.get_metrics_by_url.return_value = case["metrics"]
                
                with patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                    resp = metrics_lambda.get_url_metrics(case["event"], None)
                
                self.assertEqual(case["expect_status"], resp["statusCode"])
                body = json.loads(resp["body"])
                
                if "expect_short_url" in case:
                    self.assertEqual(case["expect_short_url"], body[0]["short_url"])
                if "expect_error_code" in case:
                    self.assertEqual(case["expect_error_code"], body["code"])

