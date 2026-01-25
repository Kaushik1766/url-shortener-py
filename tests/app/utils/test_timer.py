import contextlib
import io
import unittest

from app.utils.timer import log_performance


class TestLogPerformance(unittest.TestCase):
    def test_log_performance(self):
        def succeed(x: int) -> int:
            return x * 2

        def fail() -> None:
            raise ValueError("boom")

        cases = [
            {"name": "returns result", "func": succeed, "args": (3,), "kwargs": {}, "raises": None, "expected": 6},
            {"name": "propagates error", "func": fail, "args": (), "kwargs": {}, "raises": ValueError, "expected": None},
        ]

        for case in cases:
            wrapped = log_performance(case["func"])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                if case["raises"]:
                    with self.subTest(case["name"]), self.assertRaises(case["raises"]):
                        wrapped(*case["args"], **case["kwargs"])
                else:
                    with self.subTest(case["name"]):
                        self.assertEqual(case["expected"], wrapped(*case["args"], **case["kwargs"]))
            output = buf.getvalue()
            self.assertIn("took", output)
            self.assertIn(case["func"].__name__, output)


if __name__ == "__main__":
    unittest.main()
