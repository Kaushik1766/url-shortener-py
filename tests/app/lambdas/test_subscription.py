import json
import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.lambdas import subscription


class TestSubscriptionLambda(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.patcher = patch.object(subscription, "subscription_service", self.mock_service)
        self.patcher.start()
        self.jwt_payload = JwtDTO(id="u1", email="e@example.com", name="Name", iat=1, exp=2, subscription="std").model_dump()

    def tearDown(self):
        self.patcher.stop()

    def test_upgrade_subscription(self):
        cases = [
            {
                "name": "successful upgrade",
                "event": {"headers": {"Authorization": "Bearer token"}},
                "service_return": "new-jwt",
                "expect_status": 200,
                "expect_jwt": "new-jwt",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.mock_service.upgrade_subscription.return_value = case["service_return"]
                
                with patch("app.utils.auth_decorator.jwt.decode", return_value=self.jwt_payload):
                    response = subscription.upgrade_subscription(case["event"], None)
                
                self.assertEqual(case["expect_status"], response["statusCode"])
                body = json.loads(response["body"])
                self.assertEqual(case["expect_jwt"], body["jwt"])


if __name__ == "__main__":
    unittest.main()
