from app.service.auth_service import AuthService
import json
import unittest
from unittest.mock import MagicMock, patch

from app.errors.web_errors import ErrorCodes
from app.lambdas import auth


class TestLoginHandler(unittest.TestCase):
    def setUp(self):
        self.mock_auth_service = MagicMock(spec=AuthService)
        self.patcher = patch.object(auth, "auth_service", self.mock_auth_service)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_login_handler(self):
        valid_details = {"body": json.dumps({"email": "kaushik@a.com", "password": "secret"})}
        invalid_details = {"body": json.dumps({"email": "invalid email", "password": "short"})}

        self.mock_auth_service.login.return_value = "jwt-token"

        cases = [
            {"name": "success", "event": valid_details, "expect_status": 200, "expect_code": None},
            {"name": "validation", "event": invalid_details, "expect_status": 422, "expect_code": ErrorCodes.VALIDATION_ERROR},
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

    def test_signup_handler(self):
        valid_details = {"body": json.dumps({"email": "bar@example.com", "password": "secret", "name": "Bar"})}
        invalid_details = {"body": json.dumps({"email": "bar@example.com", "password": "x", "name": "B"})}

        cases = [
            {"name": "success", "event": valid_details, "expect_status": 201, "expect_code": None},
            {"name": "validation", "event": invalid_details, "expect_status": 422, "expect_code": ErrorCodes.VALIDATION_ERROR},
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

