import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.models.subscriptions import Subscription
from app.service.subscription_service import SubscriptionService


class TestSubscriptionService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.service = SubscriptionService(self.mock_user_repo)

    def tearDown(self):
        pass

    def test_upgrade_subscription(self):
        cases = [
            {
                "name": "upgrades from standard to premium",
                "jwt_input": JwtDTO(id="u1", email="u@example.com", name="User", iat=1, exp=2, subscription=Subscription.STANDARD),
                "encode_return": "token",
                "expect_token": "token",
                "expect_subscription": Subscription.PREMIUM,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                with patch("app.service.subscription_service.jwt.encode", return_value=case["encode_return"]) as mock_encode:
                    token = self.service.upgrade_subscription(case["jwt_input"])

                self.mock_user_repo.set_user_subscription.assert_called_with(user_id="u1", subscription=Subscription.PREMIUM)
                self.assertEqual(case["expect_token"], token)
                args, kwargs = mock_encode.call_args
                payload = args[0]
                self.assertEqual(case["expect_subscription"], payload["subscription"])


if __name__ == "__main__":
    unittest.main()
