import json
import unittest
from unittest import mock

from app.lambdas import metrics as metrics_lambda
from app.models.metrics import DailyAccessMetrics


class _FakeMetricsService:
    def __init__(self, process_return=None, metrics=None, raise_in_process=False):
        self.process_return = process_return or []
        self.metrics = metrics or []
        self.raise_in_process = raise_in_process
        self.process_called = False
        self.get_calls = []

    def process_event(self, event):
        self.process_called = True
        if self.raise_in_process:
            raise RuntimeError("boom")
        return self.process_return

    def get_metrics_by_url(self, url, user_id, start_day, end_day):
        self.get_calls.append((url, user_id, start_day, end_day))
        return self.metrics


class TestMetricsLambda(unittest.TestCase):
    def setUp(self):
        self.jwt_payload = {
            "id": "user-1",
            "email": "u@example.com",
            "name": "User",
            "iat": 1,
            "exp": 2,
            "subscription": "std",
        }

    def test_process_metrics_success(self):
        fake = _FakeMetricsService(process_return=["a", "b"])
        with mock.patch.object(metrics_lambda, "metrics_service", fake):
            result = metrics_lambda.process_metrics({"Records": []}, None)

        self.assertTrue(fake.process_called)
        self.assertEqual({"batchItemFailures": [{"itemIdentifier": "a"}, {"itemIdentifier": "b"}]}, result)

    def test_process_metrics_failure(self):
        fake = _FakeMetricsService(raise_in_process=True)
        with mock.patch.object(metrics_lambda, "metrics_service", fake):
            self.assertIsNone(metrics_lambda.process_metrics({"Records": []}, None))
        self.assertTrue(fake.process_called)

    def test_get_url_metrics_success(self):
        metric = DailyAccessMetrics(
            ShortURL="abc",
            Day="2023-01-01",
            TotalHits=1,
            ByCountry={"IN": 1},
            ByDeviceType={"desktop": 1},
            ByReferrer={"ref": 1},
        )
        fake = _FakeMetricsService(metrics=[metric])
        with mock.patch.object(metrics_lambda, "metrics_service", fake):
            with mock.patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                event = {
                    "headers": {"Authorization": "Bearer good"},
                    "pathParameters": {"short_url": "abc"},
                    "queryStringParameters": {"startDate": "2023-01-01", "endDate": "2023-01-02"},
                }
                resp = metrics_lambda.get_url_metrics(event, None)

        self.assertEqual(200, resp["statusCode"])
        body = json.loads(resp["body"])
        self.assertEqual("abc", body[0]["short_url"])
        self.assertEqual([("abc", "user-1", "2023-01-01", "2023-01-02")], fake.get_calls)

    def test_get_url_metrics_missing_path(self):
        fake = _FakeMetricsService(metrics=[])
        with mock.patch.object(metrics_lambda, "metrics_service", fake):
            with mock.patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                event = {"headers": {"Authorization": "Bearer good"}, "pathParameters": None}
                resp = metrics_lambda.get_url_metrics(event, None)

        self.assertEqual(404, resp["statusCode"])
        body = json.loads(resp["body"])
        self.assertEqual(metrics_lambda.ErrorCodes.SHORTURL_NOT_FOUND, body["code"])


if __name__ == "__main__":
    unittest.main()
