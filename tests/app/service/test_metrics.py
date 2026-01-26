import datetime
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from app.errors.web_errors import ErrorCodes, WebException
from app.models.metrics import DailyAccessMetrics, DeviceType
from app.service.metrics import MetricsService


class TestMetricsService(unittest.TestCase):
    def setUp(self):
        self.mock_sqs = MagicMock()
        self.mock_metrics_repo = MagicMock()
        self.mock_url_repo = MagicMock()
        self.service = MetricsService(self.mock_sqs, self.mock_metrics_repo, self.mock_url_repo)

    def tearDown(self):
        pass

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
            with self.subTest(case["name"]):
                self.mock_sqs.send_message.reset_mock()
                self.mock_sqs.send_message.side_effect = case["side_effect"]
                self.mock_sqs.send_message.return_value = {"MessageId": "1"}
                
                wrapped = self.service.track_metrics(case["func"])
                event = {**base_event, "headers": {**base_event["headers"], **case["headers"]}}
                
                with patch.dict(os.environ, {"QUEUE_URL": "queue"}):
                    if case["raises"]:
                        with self.assertRaises(case["raises"]):
                            wrapped(event)
                    else:
                        self.assertEqual({"ok": True}, wrapped(event))
                
                self.mock_sqs.send_message.assert_called()
                call_kwargs = self.mock_sqs.send_message.call_args.kwargs
                body = json.loads(call_kwargs["MessageBody"])
                self.assertEqual(case["expect_device"], body["device"])

    def test_process_event(self):
        timestamp = int(datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc).timestamp())
        
        cases = [
            {
                "name": "aggregates and returns failures",
                "event": {
                    "Records": [
                        {
                            "messageId": "m1",
                            "body": json.dumps({
                                "url": "abc",
                                "ip": "1.1.1.1",
                                "timestamp": timestamp,
                                "referrer": "ref1",
                                "user_agent": "ua",
                                "country": "IN",
                                "device": DeviceType.DESKTOP,
                            }),
                        },
                        {
                            "messageId": "m2",
                            "body": json.dumps({
                                "url": "abc",
                                "ip": "2.2.2.2",
                                "timestamp": timestamp,
                                "referrer": "ref1",
                                "user_agent": "ua",
                                "country": "IN",
                                "device": DeviceType.MOBILE,
                            }),
                        },
                        {
                            "messageId": "m3",
                            "body": json.dumps({
                                "url": "abc",
                                "ip": "3.3.3.3",
                                "timestamp": timestamp,
                                "referrer": "ref3",
                                "user_agent": "ua",
                                "country": "US",
                                "device": DeviceType.MOBILE,
                            }),
                        },
                    ]
                },
                "save_return": [],
                "expect_result": [],
                "expect_total_hits": 3,
                "expect_countries": {"IN": 2, "US": 1},
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_metrics_repo.save_metrics.return_value = case["save_return"]
                
                result = self.service.process_event(case["event"])
                
                self.assertEqual(case["expect_result"], result)
                self.mock_metrics_repo.save_metrics.assert_called_once()
                metrics = self.mock_metrics_repo.save_metrics.call_args[0][0]
                self.assertEqual(1, len(metrics))
                metric = metrics[0]
                self.assertEqual("abc", metric.short_url)
                self.assertEqual("2023-01-01", metric.day)
                self.assertEqual(case["expect_total_hits"], metric.total_hits)
                self.assertEqual(case["expect_countries"], metric.by_country)

    def test_get_metrics_by_url(self):
        metric = DailyAccessMetrics(
            ShortURL="mine",
            Day="2024-01-01",
            TotalHits=1,
            ByCountry={"IN": 1},
            ByDeviceType={"desktop": 1},
            ByReferrer={"ref": 1},
        )

        cases = [
            {
                "name": "blocks unowned url",
                "url": "other",
                "user_id": "u1",
                "user_urls": ["mine"],
                "metrics": [],
                "raises": WebException,
                "expect_error_code": ErrorCodes.FORBIDDEN,
            },
            {
                "name": "returns results for owned url",
                "url": "mine",
                "user_id": "u1",
                "user_urls": ["mine"],
                "metrics": [metric],
                "raises": None,
                "expect_result": [metric],
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_url_repo.get_urls_by_user_id.return_value = case["user_urls"]
                self.mock_metrics_repo.get_url_metrics.return_value = case["metrics"]
                
                if case["raises"]:
                    with self.assertRaises(case["raises"]) as ctx:
                        self.service.get_metrics_by_url(
                            url=case["url"],
                            user_id=case["user_id"],
                            start_day="2024-01-01",
                            end_day="2024-01-02"
                        )
                    self.assertEqual(case["expect_error_code"], ctx.exception.error_code)
                else:
                    result = self.service.get_metrics_by_url(
                        url=case["url"],
                        user_id=case["user_id"],
                        start_day="2024-01-01",
                        end_day="2024-01-02"
                    )
                    self.assertEqual(case["expect_result"], result)


if __name__ == "__main__":
    unittest.main()
