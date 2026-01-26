import datetime
import json
import os
import unittest
from unittest.mock import patch

from app.errors.web_errors import ErrorCodes, WebException
from app.models.metrics import DailyAccessMetrics, DeviceType
from app.service.metrics import MetricsService


class _FakeSQS:
    def __init__(self, side_effect=None):
        self.side_effect = side_effect
        self.calls = []

    def send_message(self, **kwargs):
        self.calls.append(kwargs)
        if self.side_effect:
            raise self.side_effect
        return {"MessageId": "1"}


class _FakeMetricsRepo:
    def __init__(self, save_return=None, metrics=None):
        self.save_calls = []
        self.save_return = save_return or []
        self.metrics = metrics or []
        self.get_calls = []

    def save_metrics(self, metrics):
        self.save_calls.append(metrics)
        return self.save_return

    def get_url_metrics(self, url: str, start_day: str, end_day: str):
        self.get_calls.append((url, start_day, end_day))
        return self.metrics


class _FakeURLRepo:
    def __init__(self, urls_by_user=None):
        self.urls_by_user = urls_by_user or {}

    def get_urls_by_user_id(self, user_id: str):
        return self.urls_by_user.get(user_id, [])


class TestMetricsServiceTrackMetrics(unittest.TestCase):
    def test_track_metrics(self):
        base_event = {
            "headers": {},
            "requestContext": {"identity": {"sourceIp": "1.1.1.1"}},
            "pathParameters": {"short_url": "abc"},
        }

        def ok(event=None):
            return {"ok": True}

        def explode(event=None):
            raise ValueError("boom")

        cases = [
            {
                "name": "desktop success",
                "headers": {},
                "side_effect": None,
                "func": ok,
                "expect_device": DeviceType.DESKTOP,
                "raises": None,
            },
            {
                "name": "mobile send failure swallowed",
                "headers": {"CloudFront-Is-Mobile-Viewer": "true"},
                "side_effect": Exception("send fail"),
                "func": ok,
                "expect_device": DeviceType.MOBILE,
                "raises": None,
            },
            {
                "name": "function raises but metrics still sent",
                "headers": {"CloudFront-Is-SmartTV-Viewer": "1"},
                "side_effect": None,
                "func": explode,
                "expect_device": DeviceType.SMART_TV,
                "raises": ValueError,
            },
            {
                "name": "tablet header",
                "headers": {"CloudFront-Is-Tablet-Viewer": "true"},
                "side_effect": None,
                "func": ok,
                "expect_device": DeviceType.TABLET,
                "raises": None,
            },
        ]

        for case in cases:
            sqs = _FakeSQS(side_effect=case["side_effect"])
            service = MetricsService(sqs, _FakeMetricsRepo(), _FakeURLRepo())
            wrapped = service.track_metrics(case["func"])
            event = {**base_event, "headers": {**base_event["headers"], **case["headers"]}}
            with patch.dict(os.environ, {"QUEUE_URL": "queue"}):
                if case["raises"]:
                    with self.subTest(case["name"]), self.assertRaises(case["raises"]):
                        wrapped(event)
                else:
                    with self.subTest(case["name"]):
                        self.assertEqual({"ok": True}, wrapped(event))
            self.assertGreaterEqual(len(sqs.calls), 1)
            body = json.loads(sqs.calls[-1]["MessageBody"])
            self.assertEqual(case["expect_device"], body["device"])


class TestMetricsServiceProcessEvent(unittest.TestCase):
    def test_process_event_aggregates_and_returns_failures(self):
        timestamp = int(datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc).timestamp())
        event = {
            "Records": [
                {
                    "messageId": "m1",
                    "body": json.dumps(
                        {
                            "url": "abc",
                            "ip": "1.1.1.1",
                            "timestamp": timestamp,
                            "referrer": "ref1",
                            "user_agent": "ua",
                            "country": "IN",
                            "device": DeviceType.DESKTOP,
                        }
                    ),
                },
                {
                    "messageId": "m2",
                    "body": json.dumps(
                        {
                            "url": "abc",
                            "ip": "2.2.2.2",
                            "timestamp": timestamp,
                            "referrer": "ref1",
                            "user_agent": "ua",
                            "country": "IN",
                            "device": DeviceType.MOBILE,
                        }
                    ),
                },
                {
                    "messageId": "m3",
                    "body": json.dumps(
                        {
                            "url": "abc",
                            "ip": "3.3.3.3",
                            "timestamp": timestamp,
                            "referrer": "ref3",
                            "user_agent": "ua",
                            "country": "US",
                            "device": DeviceType.MOBILE,
                        }
                    ),
                },
            ]
        }

        metrics_repo = _FakeMetricsRepo(save_return=[])
        service = MetricsService(None, metrics_repo, _FakeURLRepo())

        result = service.process_event(event)

        self.assertEqual([], result)
        self.assertEqual(1, len(metrics_repo.save_calls))
        self.assertEqual(1, len(metrics_repo.save_calls[0]))
        metric = metrics_repo.save_calls[0][0]
        self.assertEqual("abc", metric.short_url)
        self.assertEqual("2023-01-01", metric.day)
        self.assertEqual(3, metric.total_hits)
        self.assertEqual({"IN": 2, "US": 1}, metric.by_country)
        self.assertEqual({DeviceType.DESKTOP: 1, DeviceType.MOBILE: 2}, metric.by_device_type)
        self.assertEqual({"ref1": 2, "ref3": 1}, metric.by_referrer)
        self.assertCountEqual(["m1", "m2", "m3"], metric.message_ids)


class TestMetricsServiceGetMetricsByUrl(unittest.TestCase):
    def test_get_metrics_blocks_unowned_url(self):
        service = MetricsService(None, _FakeMetricsRepo(), _FakeURLRepo({"u1": ["mine"]}))

        with self.assertRaises(WebException) as ctx:
            service.get_metrics_by_url(url="other", user_id="u1", start_day="2024-01-01", end_day="2024-01-02")

        self.assertEqual(ErrorCodes.FORBIDDEN, ctx.exception.error_code)

    def test_get_metrics_returns_results(self):
        metric = DailyAccessMetrics(
            ShortURL="mine",
            Day="2024-01-01",
            TotalHits=1,
            ByCountry={"IN": 1},
            ByDeviceType={"desktop": 1},
            ByReferrer={"ref": 1},
        )

        metrics_repo = _FakeMetricsRepo(metrics=[metric])
        service = MetricsService(None, metrics_repo, _FakeURLRepo({"u1": ["mine"]}))

        result = service.get_metrics_by_url(url="mine", user_id="u1", start_day="2024-01-01", end_day="2024-01-02")

        self.assertEqual([metric], result)
        self.assertEqual([("mine", "2024-01-01", "2024-01-02")], metrics_repo.get_calls)


if __name__ == "__main__":
    unittest.main()
