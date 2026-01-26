import json
import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.errors.web_errors import ErrorCodes, WebException, exception_boundary


class TestExceptionBoundary(unittest.TestCase):
    def test_exception_boundary(self):
        validation_error = ValidationError.from_exception_data(
            "ValidationError",
            [{"type": "int_parsing", "loc": ("value",), "msg": "Input should be a valid integer", "input": "bad"}]
        )
        
        cases = [
            {
                "name": "success passthrough",
                "mock_config": {"return_value": {"status": "ok"}},
                "expect_status": None,
                "expect_code": None
            },
            {
                "name": "web exception",
                "mock_config": {"side_effect": WebException(status_code=400, message="bad", error_code=ErrorCodes.UNEXPECTED_ERROR)},
                "expect_status": 400,
                "expect_code": ErrorCodes.UNEXPECTED_ERROR
            },
            {
                "name": "validation error",
                "mock_config": {"side_effect": validation_error},
                "expect_status": 422,
                "expect_code": ErrorCodes.VALIDATION_ERROR
            },
            {
                "name": "generic error",
                "mock_config": {"side_effect": RuntimeError("boom")},
                "expect_status": 500,
                "expect_code": ErrorCodes.INTERNAL_SERVER_ERROR
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                mock_func = Mock(**case["mock_config"])
                wrapped = exception_boundary(mock_func)
                
                if case["expect_status"] is None:
                        self.assertEqual({"status": "ok"}, wrapped({}))
                else:
                    response = wrapped({})
                    self.assertEqual(case["expect_status"], response["statusCode"])
                    body = json.loads(response["body"])
                    self.assertEqual(case["expect_code"], body["code"])
