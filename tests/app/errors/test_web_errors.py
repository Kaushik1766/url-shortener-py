import json
import unittest

from pydantic import BaseModel, ValidationError

from app.errors.web_errors import ErrorCodes, WebException, exception_boundary


class TestExceptionBoundary(unittest.TestCase):
    def test_exception_boundary(self):
        class SampleModel(BaseModel):
            value: int

        def ok(event=None, ctx=None):
            return {"status": "ok"}

        def raises_web(event=None, ctx=None):
            raise WebException(status_code=400, message="bad", error_code=ErrorCodes.UNEXPECTED_ERROR)

        def raises_validation(event=None, ctx=None):
            SampleModel(value="bad")

        def raises_generic(event=None, ctx=None):
            raise RuntimeError("boom")

        cases = [
            {"name": "success passthrough", "func": ok, "expect_status": None, "expect_code": None},
            {"name": "web exception", "func": raises_web, "expect_status": 400, "expect_code": ErrorCodes.UNEXPECTED_ERROR},
            {"name": "validation error", "func": raises_validation, "expect_status": 422, "expect_code": ErrorCodes.VALIDATION_ERROR},
            {"name": "generic error", "func": raises_generic, "expect_status": 500, "expect_code": ErrorCodes.INTERNAL_SERVER_ERROR},
        ]

        for case in cases:
            wrapped = exception_boundary(case["func"])
            if case["expect_status"] is None:
                with self.subTest(case["name"]):
                    self.assertEqual({"status": "ok"}, wrapped({}))
            else:
                with self.subTest(case["name"]):
                    response = wrapped({})
                    self.assertEqual(case["expect_status"], response["statusCode"])
                    body = json.loads(response["body"])
                    self.assertEqual(case["expect_code"], body["code"])


if __name__ == "__main__":
    unittest.main()
