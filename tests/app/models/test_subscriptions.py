import unittest

from app.models.subscriptions import Subscription


class TestSubscription(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_from_number(self):
        cases = [
            {"name": "standard from 1", "number": 1, "expect": Subscription.STANDARD, "raises": None},
            {"name": "premium from 2", "number": 2, "expect": Subscription.PREMIUM, "raises": None},
            {"name": "invalid number", "number": 3, "expect": None, "raises": ValueError},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(case["raises"]):
                        Subscription.from_number(case["number"])
                else:
                    result = Subscription.from_number(case["number"])
                    self.assertIs(case["expect"], result)


if __name__ == "__main__":
    unittest.main()
