import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.models.subscriptions import Subscription
from app.service.subscription_service import SubscriptionService


class TestSubscriptionServiceUpgrade(unittest.TestCase):
    def test_upgrade_subscription(self):
        user_repo = MagicMock()
        service = SubscriptionService(user_repo)
        jwt_input = JwtDTO(id="u1", email="u@example.com", name="User", iat=1, exp=2, subscription=Subscription.STANDARD)

        with patch("app.service.subscription_service.jwt.encode", return_value="token") as mock_encode:
            token = service.upgrade_subscription(jwt_input)

        user_repo.set_user_subscription.assert_called_once_with(user_id="u1", subscription=Subscription.PREMIUM)
        self.assertEqual("token", token)
        args, kwargs = mock_encode.call_args
        payload = args[0]
        self.assertEqual(Subscription.PREMIUM, payload["subscription"])


if __name__ == "__main__":
    unittest.main()
