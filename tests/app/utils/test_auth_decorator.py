import unittest
from unittest.mock import patch

from app.dtos.auth import JwtDTO
from app.errors.web_errors import ErrorCodes, WebException
from app.utils.auth_decorator import requires_auth


class TestRequiresAuth(unittest.TestCase):
    def test_requires_auth(self):
        def handler(event, ctx=None, user: JwtDTO | None = None):
            return {"user": user}

        valid_payload = {
            "id": "user-1",
            "email": "foo@example.com",
            "name": "Foo",
            "iat": 1,
            "exp": 2,
            "subscription": "std",
        }

        cases = [
            {
                "name": "no headers",
                "event": {"headers": None},
                "auth_header": None,
                "decode_side_effect": None,
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "missing authorization",
                "event": {"headers": {}},
                "auth_header": None,
                "decode_side_effect": None,
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "invalid token",
                "event": {"headers": {"Authorization": "Bearer bad"}},
                "auth_header": "Bearer bad",
                "decode_side_effect": Exception("bad token"),
                "expect_exception": WebException,
                "error_code": ErrorCodes.UNAUTHORIZED,
            },
            {
                "name": "valid token",
                "event": {"headers": {"Authorization": "Bearer good"}},
                "auth_header": "Bearer good",
                "decode_side_effect": None,
                "decode_return": valid_payload,
                "expect_exception": None,
                "error_code": None,
            },
        ]

        for case in cases:
            wrapped = requires_auth(handler)
            decode_return = case.get("decode_return")
            side_effect = case.get("decode_side_effect")
            with patch("app.utils.auth_decorator.jwt.decode", return_value=decode_return, side_effect=side_effect):
                if case["expect_exception"]:
                    with self.subTest(case["name"]):
                        with self.assertRaises(WebException) as ctx:
                            wrapped(case["event"], None)
                        self.assertEqual(case["error_code"], ctx.exception.error_code)
                else:
                    with self.subTest(case["name"]):
                        result = wrapped(case["event"], None)
                        self.assertIsInstance(result["user"], JwtDTO)
                        self.assertEqual(valid_payload["id"], result["user"].id)


if __name__ == "__main__":
    unittest.main()
