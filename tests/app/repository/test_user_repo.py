import unittest
from unittest.mock import MagicMock

from app.errors.web_errors import ErrorCodes, WebException
from app.models.subscriptions import Subscription
from app.models.user import User
from app.repository.user_repo import UserRepository


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.mock_table = MagicMock()
        self.mock_client = MagicMock()
        self.mock_dynamo = MagicMock()
        self.mock_dynamo.Table.return_value = self.mock_table
        self.mock_dynamo.meta.client = self.mock_client
        self.repo = UserRepository(self.mock_dynamo)
        self.user_item = {"ID": "1", "Email": "foo@example.com", "PasswordHash": "p", "Username": "Foo", "Subscription": "std"}

    def tearDown(self):
        pass

    def test_get_user_by_id(self):
        items = {("USER#1", "PROFILE"): self.user_item}
        self.mock_table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}

        cases = [
            {"name": "found", "user_id": "1", "raises": None, "expect_email": "foo@example.com"},
            {"name": "missing", "user_id": "2", "raises": WebException, "error_code": ErrorCodes.USER_NOT_FOUND},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        self.repo.get_user_by_id(case["user_id"])
                    self.assertEqual(case["error_code"], ctx.exception.error_code)
                else:
                    user = self.repo.get_user_by_id(case["user_id"])
                    self.assertIsInstance(user, User)
                    self.assertEqual(case["expect_email"], user.email)

    def test_get_user_by_email(self):
        items = {
            ("LOOKUP", "EMAIL#foo@example.com"): {"ID": "1"},
            ("USER#1", "PROFILE"): self.user_item,
        }
        self.mock_table.get_item.side_effect = lambda Key: {"Item": items.get((Key["PK"], Key["SK"]))}

        cases = [
            {"name": "found", "email": "foo@example.com", "raises": None, "expect_id": "1"},
            {"name": "missing", "email": "bar@example.com", "raises": WebException, "error_code": ErrorCodes.USER_NOT_FOUND},
        ]

        for case in cases:
            with self.subTest(case["name"]):
                if case["raises"]:
                    with self.assertRaises(WebException) as ctx:
                        self.repo.get_user_by_email(case["email"])
                    self.assertEqual(case["error_code"], ctx.exception.error_code)
                else:
                    user = self.repo.get_user_by_email(case["email"])
                    self.assertEqual(case["expect_id"], user.id)

    def test_add_user(self):
        cases = [
            {
                "name": "adds user with transaction",
                "user": User(ID="2", Email="bar@example.com", PasswordHash="hash", Username="Bar"),
                "expect_items_count": 2,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.repo.add_user(case["user"])
                self.mock_client.transact_write_items.assert_called()
                call_kwargs = self.mock_client.transact_write_items.call_args.kwargs
                self.assertEqual(case["expect_items_count"], len(call_kwargs["TransactItems"]))

    def test_set_user_subscription(self):
        cases = [
            {
                "name": "updates subscription",
                "user_id": "abc",
                "subscription": Subscription.PREMIUM,
                "expect_subscription": Subscription.PREMIUM.value,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                self.repo.set_user_subscription(user_id=case["user_id"], subscription=case["subscription"])
                self.mock_table.update_item.assert_called()
                kwargs = self.mock_table.update_item.call_args.kwargs
                self.assertEqual(case["expect_subscription"], kwargs["ExpressionAttributeValues"][":subscription"])


if __name__ == "__main__":
    unittest.main()
