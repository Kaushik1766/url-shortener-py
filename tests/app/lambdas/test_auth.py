import json
import unittest
from unittest.mock import MagicMock, patch

from app.errors.web_errors import ErrorCodes
from app.lambdas import auth


class TestLoginHandler(unittest.TestCase):
    def test_login_handler(self):
        event_ok = {"body": json.dumps({"email": "foo@example.com", "password": "secret"})}
        event_bad = {"body": json.dumps({"email": "not-an-email", "password": "short"})}

        mock_service = MagicMock()
        mock_service.login.return_value = "jwt-token"

        with patch.object(auth, "auth_service", mock_service):
            cases = [
                {"name": "success", "event": event_ok, "expect_status": 200, "expect_code": None},
                {"name": "validation", "event": event_bad, "expect_status": 422, "expect_code": ErrorCodes.VALIDATION_ERROR},
            ]

            for case in cases:
                with self.subTest(case["name"]):
                    response = auth.login_handler(case["event"], None)
                    self.assertEqual(case["expect_status"], response["statusCode"])
                    body = json.loads(response["body"])
                    if case["expect_code"]:
                        self.assertEqual(case["expect_code"], body["code"])
                    else:
                        self.assertEqual("jwt-token", body["jwt"])


class TestSignupHandler(unittest.TestCase):
    def test_signup_handler(self):
        event_ok = {"body": json.dumps({"email": "bar@example.com", "password": "secret", "name": "Bar"})}
        event_bad = {"body": json.dumps({"email": "bar@example.com", "password": "x", "name": "B"})}

        mock_service = MagicMock()

        with patch.object(auth, "auth_service", mock_service):
            cases = [
                {"name": "success", "event": event_ok, "expect_status": 201, "expect_code": None},
                {"name": "validation", "event": event_bad, "expect_status": 422, "expect_code": ErrorCodes.VALIDATION_ERROR},
            ]

            for case in cases:
                with self.subTest(case["name"]):
                    response = auth.signup_handler(case["event"], None)
                    self.assertEqual(case["expect_status"], response["statusCode"])
                    body = json.loads(response["body"])
                    if case["expect_code"]:
                        self.assertEqual(case["expect_code"], body["code"])
                    else:
                        self.assertEqual("signup complete, proceed to login", body["message"])


if __name__ == "__main__":
    unittest.main()
