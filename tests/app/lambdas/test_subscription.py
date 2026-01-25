import json
import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import JwtDTO
from app.errors.web_errors import ErrorCodes
from app.lambdas import subscription


class TestUpgradeSubscription(unittest.TestCase):
    def test_upgrade_subscription(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
        }

        mock_service = MagicMock()
        mock_service.upgrade_subscription.return_value = "new-jwt"

        payload = JwtDTO(id="u1", email="e@example.com", name="Name", iat=1, exp=2, subscription="std").model_dump()

        with patch.object(subscription, "subscription_service", mock_service), \
             patch("app.utils.auth_decorator.jwt.decode", return_value=payload):
            response = subscription.upgrade_subscription(event, None)

        self.assertEqual(200, response["statusCode"])
        body = json.loads(response["body"])
        self.assertEqual("new-jwt", body["jwt"])


if __name__ == "__main__":
    unittest.main()
