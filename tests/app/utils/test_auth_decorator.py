import unittest
from unittest.mock import patch

import jwt

from app.dtos.auth import JwtDTO
from app.errors.web_errors import ErrorCodes, WebException
from app.utils.auth_decorator import requires_auth


class TestAuthDecorator(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "id": "user-1",
            "email": "foo@example.com",
            "name": "Foo",
            "iat": 1,
            "exp": 2,
            "subscription": "std",
        }

    def tearDown(self):
        pass

    def test_requires_auth(self):
        def handler(event, ctx=None, user: JwtDTO | None = None):
            return {"user": user}

        cases = [
            {
                "name": "no headers",
                "event": {"headers": None},
                "decode_side_effect": None,
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "missing authorization",
                "event": {"headers": {}},
                "decode_side_effect": None,
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "invalid token",
                "event": {"headers": {"Authorization": "Bearer bad"}},
                "decode_side_effect": jwt.exceptions.InvalidTokenError("bad token"),
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "unexpected error rethrows",
                "event": {"headers": {"Authorization": "Bearer boom"}},
                "decode_side_effect": RuntimeError("boom"),
                "expect_exception": RuntimeError,
                "error_code": None,
            },
            {
                "name": "valid token",
                "event": {"headers": {"Authorization": "Bearer good"}},
                "decode_side_effect": None,
                "decode_return": self.valid_payload,
                "expect_exception": None,
                "error_code": None,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                wrapped = requires_auth(handler)
                decode_return = case.get("decode_return")
                side_effect = case.get("decode_side_effect")
                
                with patch("app.utils.auth_decorator.jwt.decode", return_value=decode_return, side_effect=side_effect):
                    if case["expect_exception"]:
                        with self.assertRaises(Exception) as ctx:
                            wrapped(case["event"], None)
                        if case["error_code"]:
                            self.assertEqual(case["error_code"], ctx.exception.error_code)
                        else:
                            self.assertIsInstance(ctx.exception, case["expect_exception"])
                    else:
                        result = wrapped(case["event"], None)
                        self.assertIsInstance(result["user"], JwtDTO)
                        self.assertEqual(self.valid_payload["id"], result["user"].id)


if __name__ == "__main__":
    unittest.main()
