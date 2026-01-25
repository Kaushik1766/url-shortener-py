import json
import os
import unittest
from unittest.mock import patch

from app.models.metrics import DeviceType
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
        ]

        for case in cases:
            sqs = _FakeSQS(side_effect=case["side_effect"])
            service = MetricsService(sqs)
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


if __name__ == "__main__":
    unittest.main()
