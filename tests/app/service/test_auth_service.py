import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import LoginRequestDTO, SignupRequestDTO
from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.service.auth_service import AuthService


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.service = AuthService(self.mock_user_repo)
        self.test_user = User(
            ID="1",
            Email="foo@example.com",
            PasswordHash="hashed",
            Username="Foo",
            Subscription=Subscription.STANDARD
        )

    def tearDown(self):
        pass

    def test_login(self):
        self.mock_user_repo.get_user_by_email.return_value = self.test_user
        login_req = LoginRequestDTO(email="foo@example.com", password="passw")

        cases = [
            {
                "name": "invalid password",
                "checkpw_return": False,
                "expect_raise": True,
                "expect_error_code": ErrorCodes.INVALID_CREDENTIALS,
            },
            {
                "name": "valid password",
                "checkpw_return": True,
                "expect_raise": False,
                "expect_token": "jwt-token",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                with patch("app.service.auth_service.checkpw", return_value=case["checkpw_return"]), \
                     patch("app.service.auth_service.jwt.encode", return_value="jwt-token"):
                    if case["expect_raise"]:
                        with self.assertRaises(WebException) as ctx:
                            self.service.login(login_req)
                        self.assertEqual(case["expect_error_code"], ctx.exception.error_code)
                    else:
                        token = self.service.login(login_req)
                        self.assertEqual(case["expect_token"], token)

    def test_signup(self):
        cases = [
            {
                "name": "successful signup",
                "signup_req": SignupRequestDTO(email="bar@example.com", password="secret", name="Bar"),
                "hashpw_return": b"hashed",
                "gensalt_return": b"salt",
                "expect_email": "bar@example.com",
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                with patch("app.service.auth_service.bcrypt.hashpw", return_value=case["hashpw_return"]), \
                     patch("app.service.auth_service.bcrypt.gensalt", return_value=case["gensalt_return"]):
                    self.service.signup(case["signup_req"])
                
                self.mock_user_repo.add_user.assert_called()
                args, kwargs = self.mock_user_repo.add_user.call_args
                added_user: User = kwargs["user"]
                self.assertEqual(case["expect_email"], added_user.email)
                self.assertTrue(added_user.password)


if __name__ == "__main__":
    unittest.main()
