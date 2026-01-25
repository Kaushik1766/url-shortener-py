import unittest
from unittest.mock import MagicMock, patch

from app.dtos.auth import LoginRequestDTO, SignupRequestDTO
from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.service.auth_service import AuthService


class TestAuthServiceLogin(unittest.TestCase):
    def test_login(self):
        user_repo = MagicMock()
        user_repo.get_user_by_email.return_value = User(ID="1", Email="foo@example.com", PasswordHash="hashed", Username="Foo", Subscription=Subscription.STANDARD)
        service = AuthService(user_repo)
        login_req = LoginRequestDTO(email="foo@example.com", password="passw")

        cases = [
            {"name": "invalid password", "checkpw": False, "expect_raise": True},
            {"name": "valid password", "checkpw": True, "expect_raise": False},
        ]

        for case in cases:
            with patch("app.service.auth_service.checkpw", return_value=case["checkpw"]), \
                 patch("app.service.auth_service.jwt.encode", return_value="jwt-token"):
                if case["expect_raise"]:
                    with self.subTest(case["name"]), self.assertRaises(WebException) as ctx:
                        service.login(login_req)
                    self.assertEqual(ErrorCodes.INVALID_CREDENTIALS, ctx.exception.error_code)
                else:
                    with self.subTest(case["name"]):
                        token = service.login(login_req)
                        self.assertEqual("jwt-token", token)


class TestAuthServiceSignup(unittest.TestCase):
    def test_signup(self):
        user_repo = MagicMock()
        service = AuthService(user_repo)
        signup_req = SignupRequestDTO(email="bar@example.com", password="secret", name="Bar")

        with patch("app.service.auth_service.bcrypt.hashpw", return_value=b"hashed"), \
             patch("app.service.auth_service.bcrypt.gensalt", return_value=b"salt"):
            service.signup(signup_req)

        user_repo.add_user.assert_called_once()
        args, kwargs = user_repo.add_user.call_args
        added_user: User = kwargs["user"]
        self.assertEqual("bar@example.com", added_user.email)
        self.assertTrue(added_user.password)


if __name__ == "__main__":
    unittest.main()
