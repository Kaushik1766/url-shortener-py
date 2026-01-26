import unittest

from app.models.subscriptions import Subscription


class TestSubscription(unittest.TestCase):
    def test_from_number_valid(self):
        self.assertIs(Subscription.from_number(1), Subscription.STANDARD)
        self.assertIs(Subscription.from_number(2), Subscription.PREMIUM)

    def test_from_number_invalid(self):
        with self.assertRaises(ValueError):
            Subscription.from_number(3)


if __name__ == "__main__":
    unittest.main()
